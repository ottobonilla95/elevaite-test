# Elevaite Logger

A specialized logging utility designed for elevAIte FastAPI applications with AWS CloudWatch integration, OpenTelemetry support, and code annotation capabilities.

## Basic Usage

### Creating a Logger

```python
from fastapi_logger import ElevaiteLogger

# Create a basic logger
logger = ElevaiteLogger().get_logger()
logger.info("This is a log message")

# Create a logger with CloudWatch integration
cloud_logger = ElevaiteLogger(
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
from fastapi_logger import ElevaiteLogger

app = FastAPI()

# Attach the logger to FastAPI and Uvicorn
# This redirects all FastAPI and Uvicorn logs through our logger
ElevaiteLogger.attach_to_uvicorn(
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

## Advanced Features: Code Annotation

Elevaite Logger introduces a powerful code annotation system that allows for detailed logging of function execution:

### Function Capture Decorator

Log all function calls with input parameters and return values:

```python
from fastapi_logger import ElevaiteLogger

elevaite_logger = ElevaiteLogger()

@elevaite_logger.capture
def calculate_sum(a, b):
    return a + b

result = calculate_sum(5, 10)  # Will log function inputs and outputs
```

### Expression Watching

Log specific expressions or string values:

```python
@elevaite_logger.capture
def process_user(name, age):
    # Log an expression
    elevaite_logger.watch(f"Processing user {name} with age {age}")
    
    # More code here...
    return result
```

### Variable Snapshots

Log variable values with descriptive names:

```python
@elevaite_logger.capture
def calculate_values(x, y):
    # Calculate and log the product
    product = x * y
    elevaite_logger.snapshot("product", product)
    
    # This will log: "Variable snapshot: product = 35"
    return product
```

### Combined Logging

You can use multiple logging techniques within the same function:

```python
@elevaite_logger.capture
def complex_operation(a, b, c):
    # Log the starting inputs
    elevaite_logger.watch(f"Starting operation with inputs {a}, {b}, {c}")
    
    # Calculate intermediate value and log it
    intermediate = a * b
    elevaite_logger.snapshot("intermediate", intermediate)
    
    # Log intermediate result
    elevaite_logger.watch(f"Intermediate result: {intermediate}")
    
    # Calculate final result and log it
    final_result = intermediate + c
    elevaite_logger.snapshot("final_result", final_result)
    
    return final_result
```

## Example

See the `examples/decorator_example.py` file for a complete example of using the annotation system with FastAPI.

## Configuration Options

The `ElevaiteLogger` class accepts the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| name | str | "elevaite_logger" | Name of the logger |
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

## OpenTelemetry Integration

The logger can be configured to work with OpenTelemetry:

```python
logger = ElevaiteLogger(
    configure_otel=True,
    service_name="my-service",
    otlp_endpoint="http://localhost:4317"
).get_logger()
```

This will send traces to the specified OpenTelemetry collector, which can then forward them to various observability backends.