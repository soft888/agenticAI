import logging
import json
import time
from typing import Dict, List, Any
import httpx

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, mcp_controller_url: str, auth_token: str):
        self.mcp_controller_url = mcp_controller_url
        self.auth_token = auth_token
    
    async def execute_plan(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a plan by calling the MCP controller for each step."""
        results = []
        
        for step_index, step in enumerate(plan):
            tool_name = step["tool_name"]
            parameters = step["parameters"]
            
            logger.info(f"Executing step {step_index + 1}/{len(plan)}: {tool_name}")
            
            try:
                # Execute the tool via MCP controller
                start_time = time.time()
                result = await self._call_mcp_controller(tool_name, parameters)
                execution_time = time.time() - start_time
                
                # Log the result
                logger.info(f"Step {step_index + 1} completed in {execution_time:.2f}s")
                
                results.append({
                    "step": step_index + 1,
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "result": result,
                    "execution_time": execution_time
                })
            except Exception as e:
                logger.error(f"Error executing step {step_index + 1}: {str(e)}")
                # Add error to results
                results.append({
                    "step": step_index + 1,
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "error": str(e)
                })
                # Decide whether to continue or abort the plan
                # For simplicity, we'll continue
        
        return results
    
    async def _call_mcp_controller(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call the MCP controller to execute a tool."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_controller_url}/execute_tool",
                    params={"tool_name": tool_name},
                    json=parameters,
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=120.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling MCP controller: {str(e)}")
            raise