from fastapi_logger import elevaite_logger

logger = elevaite_logger.get_logger()


@elevaite_logger.capture
def add_numbers(a, b):
    return a + b


@elevaite_logger.capture
def process_user(name, age):
    """Process user information."""
    message = f"Processing user {name} with age {age}"
    logger.info(message)

    result = f"{name} is {age} years old"
    return result


@elevaite_logger.capture
def calculate_values(x, y):
    product = x * y
    logger.info(f"Variable: product = {product}")

    sum_value = x + y
    logger.info(f"Variable: sum_value = {sum_value}")

    return {"product": product, "sum": sum_value}
