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
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

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
    Also used to check if a password is temporary based on specific patterns.

    Args:
        email: User's email
        password: User's password

    Returns:
        Tuple[bool, str]: (is_temporary, message)
    """
    # Check for test credentials that should trigger password reset flow
    if email == "panagiotis.v@iopex.com" and password == "password123":
        return True, "Test account detected. Redirecting to password reset flow."

    # This is a heuristic to detect temporary passwords from the forgot-password flow
    if (
        len(password) >= 16
        and any(c.islower() for c in password)
        and any(c.isupper() for c in password)
        and any(c.isdigit() for c in password)
        and any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    ):
        return True, "Temporary password detected. Redirecting to password reset flow."

    return False, ""
