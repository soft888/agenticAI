import logging
from fastapi import FastAPI, HTTPException, Depends
from src.security.auth import authenticate_request
from src.orchestrator.orchestrator import Orchestrator
from src.registry.registry import ToolRegistry

app = FastAPI(title="MCP Controller")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

orchestrator = Orchestrator()
registry = ToolRegistry()

@app.post("/execute_tool")
async def execute_tool(tool_name: str, params: dict, token: str = Depends(authenticate_request)):
    """Execute a tool through the MCP orchestrator."""
    try:
        # Check if tool exists
        if not registry.tool_exists(tool_name):
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        # Get tool details
        tool = registry.get_tool(tool_name)
        
        # Execute the tool
        result = await orchestrator.execute_tool(tool, params)
        
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_tools")
async def list_tools(token: str = Depends(authenticate_request)):
    """List all available tools in the registry."""
    try:
        tools = registry.list_tools()
        return {"status": "success", "tools": tools}
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))