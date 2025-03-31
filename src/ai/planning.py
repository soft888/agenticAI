import logging
import json
from typing import Dict, List, Any
import httpx
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

class PlanningModule:
    def __init__(self, api_key: str, endpoint: str):
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version="2023-05-15",
            azure_endpoint=endpoint
        )
    
    async def create_plan(self, user_request: str, available_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create a plan based on the user request and available tools."""
        try:
            # Create a prompt for the LLM
            tools_description = "\n".join([
                f"Tool: {tool['name']}\nDescription: {tool['description']}\nParameters: {json.dumps(tool['parameters'])}\n"
                for tool in available_tools
            ])
            
            prompt = f"""
            User Request: {user_request}
            
            Available Tools:
            {tools_description}
            
            Create a plan to fulfill the user request using the available tools.
            The plan should be a JSON array of actions, where each action is an object with 'tool_name' and 'parameters'.
            Only use tools that are listed above.
            
            Example Plan:
            [
                {{
                    "tool_name": "example_tool",
                    "parameters": {{
                        "param1": "value1",
                        "param2": "value2"
                    }}
                }}
            ]
            
            Return only the JSON array, no additional text.
            """
            
            # Call the LLM to generate a plan
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Extract and parse the plan
            plan_text = response.choices[0].message.content.strip()
            plan = json.loads(plan_text)
            
            # Validate the plan
            self._validate_plan(plan, available_tools)
            
            return plan
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            raise
    
    def _validate_plan(self, plan: List[Dict[str, Any]], available_tools: List[Dict[str, Any]]) -> None:
        """Validate the generated plan."""
        tool_names = [tool["name"] for tool in available_tools]
        
        for step in plan:
            if step["tool_name"] not in tool_names:
                raise ValueError(f"Tool {step['tool_name']} is not available")
            
            # Could add more validation here, such as parameter checking