import asyncio
import sys
import os

# Add the project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orchestrator import Orchestrator
from core.config import AGENT_MODEL_CONFIGS
import agentscope

async def test_ppt_to_word_flow():
    print("=== Testing Orchestration Flow: PPT to Word ===")
    
    # Mocking AgentScope response if keys aren't set
    # In a real environment, it would call the LLM
    user_input = "帮我把一个 PPT 转成 Word"
    
    orchestrator = Orchestrator()
    try:
        print(f"User Input: {user_input}")
        print("Processing...")
        
        # This will fail without API keys, so we'll wrap it in a mock for demonstration
        # if keys are missing
        if os.getenv("OPENAI_API_KEY") == "your_api_key_here" or not os.getenv("OPENAI_API_KEY"):
             print("\n[MOCK MODE] (No API Key found, showing expected structure)")
             mock_plan = {
                 "trace_id": "demo-trace-123",
                 "intent": "Convert PPT to Word",
                 "plan": [
                     {
                         "step_id": 1,
                         "skill": "ppt_reader",
                         "args": {"file": "source.pptx"},
                         "dependencies": []
                     },
                     {
                         "step_id": 2,
                         "skill": "word_creator",
                         "args": {"content": "output_from_1", "target": "output.docx"},
                         "dependencies": [1]
                     }
                 ]
             }
             print(mock_plan)
        else:
            plan = await orchestrator.run_workflow(user_input)
            print("\nGenerated Plan:")
            print(plan)
            
    except Exception as e:
        print(f"Error during orchestration: {e}")

if __name__ == "__main__":
    asyncio.run(test_ppt_to_word_flow())
