from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body, Request, Depends, HTTPException, status, UploadFile, File
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from core.orchestrator import Orchestrator
from core.database import create_db_and_tables, get_session
from core.models import (
    User, UserCreate, UserRead, Token, 
    UploadedFile, FileRead,
    Project, ProjectCreate, ProjectUpdate, ProjectRead
)
from core.auth import authenticate_user, create_access_token, get_password_hash, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from core.skill_registry import SkillRegistry
from core.agent_manager import agent_lifecycle, init_agents
from core.config_manager import ConfigManager
from sqlmodel import Session, select
import json
import logging
import uuid
import asyncio
import os
import shutil
from datetime import timedelta, datetime
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalManus-Backend")

load_dotenv()
app = FastAPI(title="LocalManus API Gateway")
orchestrator = Orchestrator()
# Initialize agents to get skill_manager
manager, planner, react_agent = init_agents()
from core.agent_manager import agent_lifecycle
skill_registry = SkillRegistry(agent_lifecycle.skill_manager)
config_manager = ConfigManager()

# File upload configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def get_user_upload_dir(user_id: int) -> Path:
    """Get or create user-specific upload directory"""
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)
    return user_dir

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/api/health")
async def health_check():
    """Health check endpoint for Docker healthcheck"""
    return {
        "status": "healthy",
        "service": "localmanus-backend",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/register", response_model=UserRead)
async def register(user: UserCreate, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.post("/api/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/upload", response_model=FileRead)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Upload a file for the current user"""
    try:
        # Get user upload directory
        user_dir = get_user_upload_dir(current_user.id)
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = user_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create database record
        db_file = UploadedFile(
            user_id=current_user.id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=file.content_type
        )
        session.add(db_file)
        session.commit()
        session.refresh(db_file)
        
        return db_file
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.get("/api/files", response_model=List[FileRead])
async def list_user_files(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List all files uploaded by the current user"""
    files = session.exec(
        select(UploadedFile).where(UploadedFile.user_id == current_user.id)
    ).all()
    return files

@app.get("/api/files/{file_id}")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Download a file by ID"""
    db_file = session.exec(
        select(UploadedFile).where(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id
        )
    ).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=db_file.file_path,
        filename=db_file.original_filename,
        media_type=db_file.mime_type
    )

@app.delete("/api/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a file by ID"""
    db_file = session.exec(
        select(UploadedFile).where(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id
        )
    ).first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete file from disk
    if os.path.exists(db_file.file_path):
        os.remove(db_file.file_path)
    
    # Delete database record
    session.delete(db_file)
    session.commit()
    
    return {"message": "File deleted successfully"}

@app.get("/")
async def root():
    return {"status": "LocalManus API is running", "version": "0.1.0"}

# Skill Management Endpoints

@app.get("/api/skills", response_model=List[Dict[str, Any]])
async def list_skills(current_user: User = Depends(get_current_user)):
    """Get all available skills with metadata"""
    try:
        skills = skill_registry.get_all_skills()
        return skills
    except Exception as e:
        logger.error(f"Error listing skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills/{skill_id}", response_model=Dict[str, Any])
async def get_skill_detail(
    skill_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific skill"""
    skill = skill_registry.get_skill_detail(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@app.put("/api/skills/{skill_id}/config")
async def update_skill_config(
    skill_id: str,
    config: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Update skill configuration"""
    success = skill_registry.save_skill_config(skill_id, config)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save configuration")
    return {"message": "Configuration updated successfully"}

@app.put("/api/skills/{skill_id}/status")
async def update_skill_status(
    skill_id: str,
    payload: Dict[str, bool] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Enable or disable a skill"""
    enabled = payload.get("enabled", True)
    success = skill_registry.update_skill_status(skill_id, enabled)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update status")
    return {"message": "Status updated successfully", "enabled": enabled}

# Settings Management Endpoints

@app.get("/api/settings", response_model=Dict[str, Any])
async def get_settings(current_user: User = Depends(get_current_user)):
    """Get system configuration settings."""
    return config_manager.get_config()

@app.put("/api/settings")
async def update_settings(
    settings: Dict[str, str] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Update and persist system configuration settings."""
    success = config_manager.update_config(settings)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to persist configuration")
    return {"message": "Configuration updated successfully"}

# Project Management Endpoints

@app.get("/api/projects", response_model=List[ProjectRead])
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all projects for the current user."""
    projects = session.exec(
        select(Project).where(Project.user_id == current_user.id)
    ).all()
    return projects

@app.post("/api/projects", response_model=ProjectRead)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new project for the current user."""
    db_project = Project(
        user_id=current_user.id,
        name=project.name,
        description=project.description,
        color=project.color or "#3b82f6",
        icon=project.icon or "Folder"
    )
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@app.get("/api/projects/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific project by ID."""
    project = session.exec(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/api/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a project."""
    project = session.exec(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    if project_update.name is not None:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.color is not None:
        project.color = project_update.color
    if project_update.icon is not None:
        project.icon = project_update.icon
    
    project.updated_at = datetime.utcnow()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a project."""
    project = session.exec(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    session.delete(project)
    session.commit()
    return {"message": "Project deleted successfully"}

@app.get("/api/chat")
async def chat_sse(
    input: str, 
    session_id: str = "default", 
    file_paths: Optional[str] = None,
    access_token: Optional[str] = None, 
    current_user: User = Depends(get_current_user)
):
    """
    SSE endpoint for multi-round chat with user context and file paths.
    file_paths can be passed as comma-separated string.
    access_token can be passed as query param for SSE support.
    """
    # Pass user info and file paths to orchestrator
    user_context = {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name
    }
    
    # Parse file paths if provided
    file_paths_list = None
    if file_paths:
        file_paths_list = [p.strip() for p in file_paths.split(',') if p.strip()]
    
    return StreamingResponse(
        orchestrator.chat_stream(session_id, input, user_context=user_context, file_paths=file_paths_list),
        media_type="text/event-stream"
    )

@app.post("/api/task")
async def create_task(payload: dict = Body(...), current_user: User = Depends(get_current_user)):
    """
    Synchronous endpoint for task planning (demo).
    """
    user_input = payload.get("input", "")
    plan = await orchestrator.run_workflow(user_input)
    return plan

@app.post("/api/react")
async def react_task(payload: dict = Body(...), current_user: User = Depends(get_current_user)):
    """
    Synchronous endpoint for ReAct loop execution.
    """
    user_input = payload.get("input", "")
    result = await orchestrator.run_react_loop(user_input)
    return {"result": result}

@app.websocket("/ws/task/{trace_id}")
async def websocket_task_stream(websocket: WebSocket, trace_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for trace_id: {trace_id}")
    try:
        while True:
            data = await websocket.receive_text()
            client_msg = json.loads(data)
            
            if client_msg.get("action") == "start":
                # ... existing logic ...
                pass
            
            elif client_msg.get("action") == "react":
                user_input = client_msg.get("input", "")
                
                # Mocking the ReAct loop progress for UI
                await websocket.send_text(json.dumps({
                    "type": "thought",
                    "content": "I should check the available tools for this request.",
                    "agent": "ReActAgent"
                }, ensure_ascii=False))
                
                result = await orchestrator.run_react_loop(user_input)
                
                await websocket.send_text(json.dumps({
                    "type": "result",
                    "content": result,
                    "trace_id": trace_id
                }, ensure_ascii=False))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for trace_id: {trace_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
