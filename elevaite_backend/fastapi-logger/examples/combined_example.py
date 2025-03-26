import os
import sys
import time
from fastapi import FastAPI, Request
import uvicorn

# Add parent directory to path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi_logger import FastAPILogger

# Create our FastAPI app
app = FastAPI()

# Configure AWS CloudWatch parameters
log_group = os.environ.get("AWS_LOG_GROUP", "elevaite-example-logs")
log_stream = os.environ.get("AWS_LOG_STREAM", f"example-run-{int(time.time())}")

# Configure OpenTelemetry
service_name = "combined-service"
otlp_endpoint = os.environ.get("OTLP_ENDPOINT", "http://localhost:4317")

# Attach the logger to FastAPI and Uvicorn with both CloudWatch and OpenTelemetry
FastAPILogger.attach_to_uvicorn(
    # CloudWatch configuration
    cloudwatch_enabled=True,
    log_group=log_group,
    log_stream=log_stream,
    filter_fastapi=True,
    
    # OpenTelemetry configuration
    service_name=service_name,
    otlp_endpoint=otlp_endpoint, 
    configure_otel=True,
    resource_attributes={
        "deployment.environment": "example",
        "cloud.provider": "aws"
    }
)

# Get a reference to the logger
logger = FastAPILogger(
    name="combined-example",
    # CloudWatch configuration
    cloudwatch_enabled=True,
    log_group=log_group,
    log_stream=log_stream,
    
    # OpenTelemetry configuration
    service_name=service_name,
    otlp_endpoint=otlp_endpoint,
    configure_otel=True,
    resource_attributes={
        "deployment.environment": "example",
        "cloud.provider": "aws"
    }
).get_logger()

# Get the tracer from the global provider
from opentelemetry import trace
tracer = trace.get_tracer("combined-example")

@app.middleware("http")
async def add_tracing_context(request: Request, call_next):
    """Add tracing context to each request and send to both systems."""
    with tracer.start_as_current_span(
        f"{request.method} {request.url.path}",
        attributes={
            "http.method": request.method,
            "http.url": str(request.url),
            "http.schema": request.url.scheme,
            "http.host": request.url.netloc,
            "http.target": request.url.path,
        }
    ) as span:
        # Add user-agent to span
        if "user-agent" in request.headers:
            span.set_attribute("http.user_agent", request.headers["user-agent"])
        
        # Process the request - this log goes to both CloudWatch and includes trace IDs
        logger.info(f"Processing request: {request.method} {request.url.path}")
        response = await call_next(request)
        
        # Add response info to span
        span.set_attribute("http.status_code", response.status_code)
        
        return response

@app.get("/")
async def root():
    with tracer.start_as_current_span("root_operation") as span:
        logger.info("Processing request to root endpoint")
        return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    with tracer.start_as_current_span("get_item_operation") as span:
        logger.info(f"Retrieving item with ID: {item_id}")
        span.set_attribute("item.id", item_id)
        
        # Simulate a database query
        with tracer.start_as_current_span("database_query") as child_span:
            logger.info(f"Querying database for item {item_id}")
            # Simulate database latency
            time.sleep(0.1)
        
        return {"item_id": item_id, "name": f"Item {item_id}"}

# Print information about where to find logs and traces
print(f"\nRunning example FastAPI app with CloudWatch and OpenTelemetry enabled")
print(f"Service Name: {service_name}")
print(f"OTLP Endpoint: {otlp_endpoint}")
print(f"Log Group: {log_group}")
print(f"Log Stream: {log_stream}")
print("\nTo view CloudWatch logs, visit:")
print(
    f"https://console.aws.amazon.com/cloudwatch/home?region={os.environ.get('AWS_REGION', 'us-east-1')}#logsV2:log-groups/log-group/{log_group}/log-events/{log_stream}"
)
print("\nTo view traces, make sure you have an OpenTelemetry collector running.")
print("If you're using Jaeger, visit: http://localhost:16686")
print("\nPress Ctrl+C to quit")

if __name__ == "__main__":
    # Check for AWS credentials
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get(
        "AWS_SECRET_ACCESS_KEY"
    ):
        print("\nWARNING: AWS credentials not found in environment variables.")
        print(
            "Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION to enable CloudWatch logging."
        )
        print("OpenTelemetry tracing will still work if a collector is available.")

    # Run the FastAPI app with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)