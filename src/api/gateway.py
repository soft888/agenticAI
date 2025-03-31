import logging
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.security.auth import create_access_token, authenticate_request
from src.registry.registry import ToolRegistry
from src.ai.planning import PlanningModule
from src.ai.execution import ExecutionEngine
from src.ai.feedback import FeedbackLoop
from datetime import timedelta

app = FastAPI(title="MCP API Gateway")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
registry = ToolRegistry()
planning = PlanningModule(
    api_key="your-azure-openai-key",
    endpoint="your-azure-openai-endpoint"
)
execution = ExecutionEngine(
    mcp_controller_url="http://mcp-controller:8000",
    auth_token="internal-token"  # In production, use a secure token
)
feedback = FeedbackLoop(
    api_key="your-azure-openai-key",
    endpoint="your-azure-openai-endpoint"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return token."""
    # In a real application, verify credentials against a database
    if form_data.username != "test" or form_data.password != "test":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/agent/execute")
async def execute_agent(request: dict, token: str = Depends(authenticate_request)):
    """Execute the agent to fulfill a user request."""
    try:
        user_request = request.get("request")
        if not user_request:
            raise HTTPException(status_code=400, detail="Missing user request")
        
        # Get available tools
        tools = registry.list_tools()
        
        # Create a plan
        plan = await planning.create_plan(user_request, tools)
        logger.info(f"Created plan with {len(plan)} steps")
        
        # Execute the plan
        results = await execution.execute_plan(plan)
        logger.info(f"Executed plan with {len(results)} results")
        
        # Analyze results and provide feedback
        analysis = await feedback.analyze_results(user_request, plan, results)
        logger.info(f"Analysis completed: success={analysis['success']}")
        
        # Return the complete response
        return {
            "success": True,
            "plan": plan,
            "results": results,
            "analysis": analysis,
            "response": analysis["user_response"]
        }
    except Exception as e:
        logger.error(f"Error executing agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))