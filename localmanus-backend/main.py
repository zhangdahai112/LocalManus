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

@app.websocket("/ws/task/{trace_id}")
async def websocket_task_stream(websocket: WebSocket, trace_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for trace_id: {trace_id}")
    try:
        while True:
            # Placeholder for receiving data from frontend
            data = await websocket.receive_text()
            client_msg = json.loads(data)
            
            if client_msg.get("action") == "start":
                # Simulated orchestration stream
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": "Manager analyzing intent...",
                    "agent": "Manager"
                }))
                
                # Mock analysis
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": "Planner generating DAG...",
                    "agent": "Planner"
                }))

                # Mock result
                await websocket.send_text(json.dumps({
                    "type": "result",
                    "content": "DAG generated successfully. Ready for execution.",
                    "trace_id": trace_id
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for trace_id: {trace_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
