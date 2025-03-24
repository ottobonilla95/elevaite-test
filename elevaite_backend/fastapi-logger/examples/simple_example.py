import os
import sys
import time
from fastapi import FastAPI
import uvicorn

# Add parent directory to path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi_logger import FastAPILogger

# Create our FastAPI app
app = FastAPI()

# Configure AWS CloudWatch parameters
log_group = os.environ.get("AWS_LOG_GROUP", "elevaite-example-logs")
log_stream = os.environ.get("AWS_LOG_STREAM", f"example-run-{int(time.time())}")

# Attach the logger to FastAPI and Uvicorn with CloudWatch enabled
FastAPILogger.attach_to_uvicorn(
    cloudwatch_enabled=True,
    log_group=log_group,
    log_stream=log_stream,
    filter_fastapi=True,  # Filter out standard FastAPI logs
)

# Get a reference to the logger for use in route handlers
logger = FastAPILogger(
    name="example-app",
    cloudwatch_enabled=True,
    log_group=log_group,
    log_stream=log_stream,
).get_logger()


@app.get("/")
async def root():
    logger.info("Processing request to root endpoint")
    return {"message": "Hello World"}


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    logger.info(f"Retrieving item with ID: {item_id}")
    return {"item_id": item_id, "name": f"Item {item_id}"}


# Print information about where to find the logs
print(f"\nRunning example FastAPI app with CloudWatch logging enabled")
print(f"Log Group: {log_group}")
print(f"Log Stream: {log_stream}")
print("\nTo view these logs, visit:")
print(
    f"https://console.aws.amazon.com/cloudwatch/home?region={os.environ.get('AWS_REGION', 'us-east-1')}#logsV2:log-groups/log-group/{log_group}/log-events/{log_stream}"
)
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

    # Run the FastAPI app with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
