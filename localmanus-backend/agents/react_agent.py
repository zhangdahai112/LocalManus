import json
import logging
from typing import List, Dict, Any, Optional
from agentscope.agents import DialogAgent
from agentscope.message import Msg
from core.skill_manager import SkillManager

logger = logging.getLogger("LocalManus-ReActAgent")

REACT_SYSTEM_PROMPT = """You are an agent that uses the ReAct (Reasoning and Acting) framework.
Your goal is to solve the user's request by alternating between Thought, Action, and Observation.

Available Tools:
{tools_metadata}

Response Format:
Thought: [Your reasoning about what to do next]
Action: [skill_name].[tool_name](parameter1="value", parameter2="value")
Observation: [The result of the action, which will be provided to you]

Continue this loop until you have the final answer.
Final Answer: [Your final response to the user]

Example:
Thought: I need to read the content of 'test.txt' to answer the question.
Action: fileops.read_file(file_path="test.txt")
Observation: Hello World
Thought: I have the content of the file. I can now answer the user.
Final Answer: The content of the file is 'Hello World'.
"""

class ReActAgent:
    def __init__(self, model_config_name: str, skill_manager: SkillManager):
        self.skill_manager = skill_manager
        self.tools_metadata = self._format_tools_metadata()
        self.agent = DialogAgent(
            name="ReActAgent",
            sys_prompt=REACT_SYSTEM_PROMPT.format(tools_metadata=self.tools_metadata),
            model_config_name=model_config_name
        )

    def _format_tools_metadata(self) -> str:
        tools = self.skill_manager.list_all_tools()
        formatted = ""
        for t in tools:
            formatted += f"- {t['skill']}.{t['name']}{t['parameters']}: {t['description']}\n"
        return formatted

    async def run(self, user_input: str, max_iterations: int = 5):
        msg = Msg(name="User", content=user_input, role="user")
        context = [msg]
        
        for i in range(max_iterations):
            response = self.agent(context)
            content = response.content
            logger.info(f"Iteration {i+1} Response: {content}")
            
            # Update context with agent's thought/action
            context.append(response)

            if "Final Answer:" in content:
                return content.split("Final Answer:")[1].strip()

            if "Action:" in content:
                action_line = [line for line in content.split("\n") if line.startswith("Action:")][0]
                action_str = action_line.replace("Action:", "").strip()
                
                try:
                    # Parse skill_name.tool_name(params)
                    skill_tool, params_str = action_str.split("(", 1)
                    params_str = params_str.rsplit(")", 1)[0]
                    skill_name, tool_name = skill_tool.split(".")
                    
                    # Very basic param parsing (eval is dangerous but for demo/internal use)
                    # A better way would be using regex or ast.literal_eval
                    params = eval(f"dict({params_str})")
                    
                    # Execute action
                    skill = self.skill_manager.get_skill(skill_name)
                    if not skill:
                        observation = f"Error: Skill '{skill_name}' not found."
                    else:
                        observation = await skill.execute(tool_name, **params)
                    
                    obs_msg = Msg(name="Observation", content=str(observation), role="user")
                    logger.info(f"Iteration {i+1} Observation: {observation}")
                    context.append(obs_msg)
                    
                except Exception as e:
                    error_msg = f"Error executing action: {str(e)}"
                    logger.error(error_msg)
                    obs_msg = Msg(name="Observation", content=error_msg, role="user")
                    context.append(obs_msg)
            else:
                # If no action or final answer, might be stuck
                break

        return "Failed to complete task within max iterations."
