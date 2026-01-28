import os
import sys
import time
from fastapi import FastAPI
import uvicorn

# Add parent directory to path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi_logger import ElevaiteLogger

# Create our FastAPI app
app = FastAPI()

# Configure AWS CloudWatch parameters (optional)
log_group = os.environ.get("AWS_LOG_GROUP", "elevaite-example-logs")
log_stream = os.environ.get("AWS_LOG_STREAM", f"decorator-example-{int(time.time())}")

# Initialize the logger
elevaite_logger = ElevaiteLogger(
    name="decorator-example",
    cloudwatch_enabled=False,  # Set to True to enable CloudWatch logging
    log_group=log_group,
    log_stream=log_stream,
)

# Get the standard logger for regular logging
logger = elevaite_logger.get_logger()


# Example 1: Basic function decorator with capture
@elevaite_logger.capture
def add_numbers(a, b):
    return a + b


# Example 2: Function with watch annotation
@elevaite_logger.capture
def process_user(name, age):
    # Log an expression using the watch function
    elevaite_logger.watch(f"Processing user {name} with age {age}")

    result = f"{name} is {age} years old"
    return result


# Example 3: Function with snapshot annotation
@elevaite_logger.capture
def calculate_values(x, y):
    # Calculate value and log it
    product = x * y
    elevaite_logger.snapshot("product", product)

    # Calculate another value and log it
    sum_value = x + y
    elevaite_logger.snapshot("sum_value", sum_value)

    return {"product": product, "sum": sum_value}


# Example 4: Combined annotations
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


@app.get("/")
async def root():
    logger.info("Processing request to root endpoint")

    # Demonstrate the decorated functions
    add_result = add_numbers(5, 10)
    logger.info(f"Addition result: {add_result}")

    user_result = process_user("Alice", 30)
    logger.info(f"User processing result: {user_result}")

    calc_result = calculate_values(3, 4)
    logger.info(f"Calculation results: {calc_result}")

    complex_result = complex_operation(2, 3, 4)
    logger.info(f"Complex operation result: {complex_result}")

    return {
        "message": "Check the console for logging output",
        "add_result": add_result,
        "user_result": user_result,
        "calc_result": calc_result,
        "complex_result": complex_result,
    }


if __name__ == "__main__":
    print("\nRunning example FastAPI app with decorator-based logging")
    print("Access the endpoint at http://localhost:8000")
    print("\nPress Ctrl+C to quit")

    # Run the FastAPI app with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
