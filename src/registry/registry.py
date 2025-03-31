import json
import logging
from typing import Dict, List, Any
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

class Tool:
    def __init__(self, name: str, description: str, parameters: Dict, returns: Dict, 
                 container_image: str, endpoint: str):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.returns = returns
        self.container_image = container_image
        self.endpoint = endpoint

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(
            account_url="https://mcpstorage.blob.core.windows.net",
            credential=self.credential
        )
        self.container_client = self.blob_service_client.get_container_client("tool-registry")
        self._load_tools_from_storage()
    
    def _load_tools_from_storage(self):
        """Load tools from Azure Blob Storage."""
        try:
            blob_client = self.container_client.get_blob_client("tools.json")
            if blob_client.exists():
                blob_data = blob_client.download_blob()
                tools_data = json.loads(blob_data.readall().decode("utf-8"))
                for tool_data in tools_data:
                    tool = Tool(
                        name=tool_data["name"],
                        description=tool_data["description"],
                        parameters=tool_data["parameters"],
                        returns=tool_data["returns"],
                        container_image=tool_data["container_image"],
                        endpoint=tool_data["endpoint"]
                    )
                    self.tools[tool.name] = tool
                logger.info(f"Loaded {len(self.tools)} tools from storage")
            else:
                logger.warning("No tools.json found in storage")
        except Exception as e:
            logger.error(f"Error loading tools from storage: {str(e)}")
    
    def register_tool(self, tool: Tool) -> bool:
        """Register a new tool in the registry."""
        if tool.name in self.tools:
            logger.warning(f"Tool {tool.name} already exists")
            return False
        
        self.tools[tool.name] = tool
        self._save_tools_to_storage()
        return True
    
    def _save_tools_to_storage(self):
        """Save tools to Azure Blob Storage."""
        try:
            tools_data = []
            for tool in self.tools.values():
                tools_data.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "returns": tool.returns,
                    "container_image": tool.container_image,
                    "endpoint": tool.endpoint
                })
            
            blob_client = self.container_client.get_blob_client("tools.json")
            blob_client.upload_blob(json.dumps(tools_data), overwrite=True)
            logger.info("Saved tools to storage")
        except Exception as e:
            logger.error(f"Error saving tools to storage: {str(e)}")
    
    def tool_exists(self, tool_name: str) -> bool:
        """Check if a tool exists in the registry."""
        return tool_name in self.tools
    
    def get_tool(self, tool_name: str) -> Tool:
        """Get a tool from the registry."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        return self.tools[tool_name]
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools in the registry."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "returns": tool.returns
            }
            for tool in self.tools.values()
        ]