# FastAPI Logger

A specialized logging utility designed for elevAIte FastAPI applications with AWS CloudWatch integration.

## Basic Usage

### Creating a Logger

```python
from fastapi_logger import FastAPILogger

# Create a basic logger
logger = FastAPILogger().get_logger()
logger.info("This is a log message")

# Create a logger with CloudWatch integration
cloud_logger = FastAPILogger(
    cloudwatch_enabled=True,
    log_group="my-fastapi-app",
    log_stream="app-logs",
    filter_fastapi=True  # Optional: filter out standard FastAPI logs
).get_logger()

cloud_logger.info("This log will also be sent to CloudWatch")
```

### Integrating with FastAPI and Uvicorn

```python
from fastapi import FastAPI
from fastapi_logger import FastAPILogger

app = FastAPI()

# Attach the logger to FastAPI and Uvicorn
# This redirects all FastAPI and Uvicorn logs through our logger
FastAPILogger.attach_to_uvicorn(
    cloudwatch_enabled=True,
    log_group="my-fastapi-app",
    log_stream="app-logs",
    filter_fastapi=True  # Optional: filter out standard FastAPI logs
)

@app.get("/")
async def root():
    # These logs will be captured and optionally sent to CloudWatch
    app.logger.info("Processing request to root endpoint")
    return {"message": "Hello World"}
```

## Configuration Options

The `FastAPILogger` class accepts the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| name | str | "fastapi_logger" | Name of the logger |
| level | int | logging.DEBUG | Logging level |
| stream | TextIO | sys.stdout | Output stream for logs |
| cloudwatch_enabled | bool | False | Whether to send logs to CloudWatch |
| log_group | str | None | CloudWatch log group name (required if cloudwatch_enabled is True) |
| log_stream | str | None | CloudWatch log stream name (required if cloudwatch_enabled is True) |
| filter_fastapi | bool | False | Whether to filter out standard FastAPI logs when sending to CloudWatch |
| service_name | str | "fastapi-service" | Service name for OpenTelemetry (used if configure_otel is True) |
| otlp_endpoint | Optional[str] | None | OpenTelemetry collector endpoint (e.g. 'http://localhost:4317') |
| configure_otel | bool | False | Whether to configure OpenTelemetry with this logger instance |
| resource_attributes | Optional[Dict[str, str]] | None | Additional resource attributes for OpenTelemetry |

## AWS Credentials

To use the CloudWatch integration, ensure you have configured AWS credentials:

1. Through environment variables:
   ```
   AWS_ACCESS_KEY_ID
   AWS_SECRET_ACCESS_KEY
   AWS_REGION
   ```

2. Through AWS configuration files (`~/.aws/credentials` and `~/.aws/config`)

3. Through IAM roles (if running on EC2, ECS, or Lambda)