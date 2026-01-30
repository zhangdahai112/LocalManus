from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from core.orchestrator import Orchestrator
import json
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalManus-Backend")

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

@app.get("/")
async def root():
    return {"status": "LocalManus API is running", "version": "0.1.0"}

@app.post("/api/task")
async def create_task(payload: dict = Body(...)):
    """
    Synchronous endpoint for task planning (demo).
    """
    user_input = payload.get("input", "")
    plan = await orchestrator.run_workflow(user_input)
    return plan

@app.post("/api/react")
async def react_task(payload: dict = Body(...)):
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
                }))
                
                result = await orchestrator.run_react_loop(user_input)
                
                await websocket.send_text(json.dumps({
                    "type": "result",
                    "content": result,
                    "trace_id": trace_id
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for trace_id: {trace_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
