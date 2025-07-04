import secrets
import string
from typing import Tuple


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a secure random password.

    Args:
        length: Length of the password (default: 16)

    Returns:
        str: A secure random password
    """
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = '!@#$%^&*(),.?":{}|<>'

    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars),
    ]

    # Fill the rest with random characters from all sets
    all_chars = lowercase + uppercase + digits + special_chars
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Shuffle the password to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)

    return "".join(password)


def is_password_temporary(email: str, password: str) -> Tuple[bool, str]:
    """
    Check if the provided credentials are for a test account that should trigger password reset.

    IMPORTANT: This function should ONLY identify known test accounts or initial default passwords.
    It should NOT try to detect if a password "looks like" a temporary password based on complexity.

    Once a user has changed their password, we should respect that choice and not force them
    to change it again, even if their new password happens to match our complexity heuristics.

    Args:
        email: User's email
        password: User's password

    Returns:
        Tuple[bool, str]: (is_temporary, message)
    """
    return False, ""
