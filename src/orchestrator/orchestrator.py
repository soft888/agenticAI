import logging
import json
import uuid
import httpx
from typing import Dict, Any
from src.registry.registry import Tool
from kubernetes import client, config

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        try:
            # Try to load in-cluster config (for deployment in AKS)
            config.load_incluster_config()
        except:
            # Fall back to local kubeconfig
            config.load_kube_config()
        
        self.k8s_api = client.CoreV1Api()
        self.k8s_batch_api = client.BatchV1Api()
    
    async def execute_tool(self, tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool based on its configuration."""
        try:
            # Check if the tool has an endpoint (API) or needs to be executed as a container
            if tool.endpoint:
                # Call the API endpoint
                return await self._call_api_endpoint(tool, params)
            else:
                # Create a Kubernetes job to run the tool
                return await self._create_k8s_job(tool, params)
        except Exception as e:
            logger.error(f"Error executing tool {tool.name}: {str(e)}")
            raise
    
    async def _call_api_endpoint(self, tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call an API endpoint for the tool."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    tool.endpoint,
                    json=params,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {tool.endpoint}: {str(e)}")
            raise
    
    async def _create_k8s_job(self, tool: Tool, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Kubernetes job to run the tool."""
        job_name = f"{tool.name.lower()}-{uuid.uuid4().hex[:8]}"
        
        # Create the job specification
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=job_name),
            spec=client.V1JobSpec(
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(name=job_name),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=job_name,
                                image=tool.container_image,
                                env=[
                                    client.V1EnvVar(
                                        name="PARAMS",
                                        value=json.dumps(params)
                                    )
                                ]
                            )
                        ],
                        restart_policy="Never"
                    )
                ),
                backoff_limit=2
            )
        )
        
        # Create the job
        self.k8s_batch_api.create_namespaced_job(namespace="default", body=job)
        
        logger.info(f"Created job {job_name} to execute tool {tool.name}")
        
        # For simplicity, we'll return a job ID that could be used to check status later
        return {"job_id": job_name, "status": "submitted"}