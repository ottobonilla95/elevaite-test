#!/usr/bin/env python
"""Simple test script to verify decorator functionality."""

import os
import sys
import time

# Add parent directory to path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi_logger import ElevaiteLogger

# Initialize the logger
elevaite_logger = ElevaiteLogger(
    name="test-run",
    cloudwatch_enabled=False,
)

# Get the standard logger for regular logging
logger = elevaite_logger.get_logger()

print("Testing Elevaite Logger decorator functionality...")

# Example 1: Basic function decorator with capture
@elevaite_logger.capture
def add_numbers(a, b):
    return a + b

# Example 2: Function with watch
@elevaite_logger.capture
def process_user(name, age):
    # Log an expression using the watch function
    elevaite_logger.watch(f"Processing user {name} with age {age}")
    
    result = f"{name} is {age} years old"
    return result

# Example 3: Function with snapshot
@elevaite_logger.capture
def calculate_values(x, y):
    # Calculate value and log it
    product = x * y
    elevaite_logger.snapshot("product", product)
    
    # Calculate another value and log it
    sum_value = x + y
    elevaite_logger.snapshot("sum_value", sum_value)
    
    return {
        "product": product,
        "sum": sum_value
    }

# Example 4: Combined logging techniques
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


if __name__ == "__main__":
    print("\nRunning example 1: add_numbers")
    result = add_numbers(5, 10)
    print(f"Result: {result}")
    
    print("\nRunning example 2: process_user")
    result = process_user("Alice", 30)
    print(f"Result: {result}")
    
    print("\nRunning example 3: calculate_values")
    result = calculate_values(3, 4)
    print(f"Result: {result}")
    
    print("\nRunning example 4: complex_operation")
    result = complex_operation(2, 3, 4)
    print(f"Result: {result}")
    
    print("\nAll examples completed!")