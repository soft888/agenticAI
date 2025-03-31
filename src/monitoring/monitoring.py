import logging
from datetime import datetime
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry with Azure Monitor
configure_azure_monitor(
    connection_string="InstrumentationKey=your-app-insights-instrumentation-key"
)

tracer = trace.get_tracer(__name__)

class MonitoringService:
    def __init__(self):
        self.tracer = tracer
    
    def start_span(self, name: str, kind=SpanKind.INTERNAL):
        """Start a new monitoring span."""
        return self.tracer.start_as_current_span(name, kind=kind)
    
    def log_tool_execution(self, tool_name: str, params: dict, result: dict, execution_time: float):
        """Log a tool execution to Azure Monitor."""
        with self.tracer.start_as_current_span(f"tool_execution_{tool_name}") as span:
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("tool.params", str(params))
            span.set_attribute("tool.result", str(result))
            span.set_attribute("tool.execution_time", execution_time)
            span.set_status(Status(StatusCode.OK))
            
            logger.info(f"Tool {tool_name} executed in {execution_time:.2f}s")
    
    def log_error(self, tool_name: str, error_message: str):
        """Log an error during tool execution."""
        with self.tracer.start_as_current_span(f"tool_error_{tool_name}") as span:
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("error.message", error_message)
            span.set_status(Status(StatusCode.ERROR))
            
            logger.error(f"Error executing tool {tool_name}: {error_message}")