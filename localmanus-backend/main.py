from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from core.orchestrator import Orchestrator
from core.database import create_db_and_tables, get_session
from core.models import User, UserCreate, UserRead, Token
from core.auth import authenticate_user, create_access_token, get_password_hash, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from sqlmodel import Session, select
import json
import logging
import uuid
import asyncio
from datetime import timedelta
from dotenv import load_dotenv
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalManus-Backend")

load_dotenv()
app = FastAPI(title="LocalManus API Gateway")
orchestrator = Orchestrator()

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

@app.get("/")
async def root():
    return {"status": "LocalManus API is running", "version": "0.1.0"}

@app.get("/api/chat")
async def chat_sse(input: str, session_id: str = "default", access_token: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """
    SSE endpoint for multi-round chat with user context.
    access_token can be passed as query param for SSE support.
    """
    # Pass user info to orchestrator
    user_context = {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name
    }
    return StreamingResponse(
        orchestrator.chat_stream(session_id, input, user_context=user_context),
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
