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

# Configure OpenTelemetry
service_name = "example-service"
otlp_endpoint = os.environ.get("OTLP_ENDPOINT", "http://localhost:4317")

# Attach the logger to FastAPI and Uvicorn with OpenTelemetry enabled
FastAPILogger.attach_to_uvicorn(
    service_name=service_name,
    otlp_endpoint=otlp_endpoint, 
    configure_otel=True,
    resource_attributes={
        "deployment.environment": "example"
    }
)

# Get a reference to the logger with OpenTelemetry configured
logger = FastAPILogger(
    name="example-app",
    service_name=service_name,
    otlp_endpoint=otlp_endpoint,
    configure_otel=True,
    resource_attributes={
        "deployment.environment": "example"
    }
).get_logger()

# Get the tracer from the global provider
from opentelemetry import trace
tracer = trace.get_tracer("example-app")

@app.middleware("http")
async def add_tracing_context(request: Request, call_next):
    """Add tracing context to each request."""
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
        
        # Process the request
        logger.info(f"Processing request: {request.method} {request.url.path}")
        response = await call_next(request)
        
        # Add response info to span
        span.set_attribute("http.status_code", response.status_code)
        
        return response

@app.get("/")
async def root():
    with tracer.start_as_current_span("root_operation") as span:
        logger.info("Processing request to root endpoint")
        span.set_attribute("custom.attribute", "example value")
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
            child_span.set_attribute("database.query", f"SELECT * FROM items WHERE id = {item_id}")
        
        return {"item_id": item_id, "name": f"Item {item_id}"}

@app.get("/error")
async def trigger_error():
    with tracer.start_as_current_span("error_operation") as span:
        try:
            logger.info("About to trigger an error")
            # Intentionally raise an exception
            result = 1 / 0
            return {"result": result}
        except Exception as e:
            # Record the exception in the span
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            logger.error(f"An error occurred: {str(e)}")
            return {"error": str(e)}

# Print information about where to find the telemetry data
print(f"\nRunning example FastAPI app with OpenTelemetry enabled")
print(f"Service Name: {service_name}")
print(f"OTLP Endpoint: {otlp_endpoint}")
print("\nTo view traces, make sure you have an OpenTelemetry collector running.")
print("If you're using Jaeger, visit: http://localhost:16686")
print("\nPress Ctrl+C to quit")

if __name__ == "__main__":
    # Run the FastAPI app with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)