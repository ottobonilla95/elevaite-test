import hashlib
import ipaddress
from typing import Optional
from fastapi import Request


def _anonymize_ip_for_fingerprint(ip_address: str) -> str:
    """
    Anonymize IP address for fingerprinting to balance security with privacy.

    For IPv4: Uses first 3 octets (e.g., 192.168.1.100 -> 192.168.1.0)
    For IPv6: Uses first 64 bits (network portion)

    Args:
        ip_address: The IP address to anonymize

    Returns:
        Anonymized IP address string
    """
    if not ip_address or ip_address == "unknown":
        return "unknown"

    try:
        ip = ipaddress.ip_address(ip_address)

        if isinstance(ip, ipaddress.IPv4Address):
            # For IPv4, use /24 network (first 3 octets)
            network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
            return str(network.network_address)
        elif isinstance(ip, ipaddress.IPv6Address):
            # For IPv6, use /64 network (standard subnet size)
            network = ipaddress.IPv6Network(f"{ip}/64", strict=False)
            return str(network.network_address)
        else:
            return "unknown"

    except (ipaddress.AddressValueError, ValueError):
        # If IP parsing fails, return a generic identifier
        return "unknown"


def generate_device_fingerprint(
    request: Request, user_id: int, additional_data: Optional[str] = None
) -> str:
    """
    Generate a device fingerprint based on request headers and user context.

    This creates a semi-persistent identifier for a device/browser combination
    that can be used to track MFA verifications for 24-hour bypass.

    Privacy Features:
    - IP addresses are anonymized to network level (IPv4 /24, IPv6 /64)
    - Only essential headers are used for fingerprinting
    - No personally identifiable information is stored

    Args:
        request: FastAPI request object
        user_id: User ID to include in fingerprint
        additional_data: Optional additional data to include

    Returns:
        SHA256 hash representing the device fingerprint
    """
    # Collect fingerprinting data
    fingerprint_data = []

    # User ID (to make fingerprint user-specific)
    fingerprint_data.append(str(user_id))

    # User Agent (browser/app identifier)
    user_agent = request.headers.get("user-agent", "unknown")
    fingerprint_data.append(user_agent)

    # Accept headers (browser capabilities)
    accept = request.headers.get("accept", "")
    fingerprint_data.append(accept)

    # Accept-Language (user's language preferences)
    accept_language = request.headers.get("accept-language", "")
    fingerprint_data.append(accept_language)

    # Accept-Encoding (compression support)
    accept_encoding = request.headers.get("accept-encoding", "")
    fingerprint_data.append(accept_encoding)

    # Client IP (with privacy considerations)
    # Use only network portion to balance security with privacy
    client_ip = get_client_ip(request)
    privacy_ip = _anonymize_ip_for_fingerprint(client_ip)
    fingerprint_data.append(privacy_ip)

    # Custom headers that might indicate device type
    x_forwarded_for = request.headers.get("x-forwarded-for", "")
    fingerprint_data.append(x_forwarded_for)

    # Additional data if provided
    if additional_data:
        fingerprint_data.append(additional_data)

    # Combine all data
    combined_data = "|".join(fingerprint_data)

    # Generate SHA256 hash
    fingerprint = hashlib.sha256(combined_data.encode("utf-8")).hexdigest()

    return fingerprint


def get_client_ip(request: Request) -> str:
    """
    Extract the client IP address from the request.

    Handles various proxy headers and fallbacks.
    """
    # Check for X-Forwarded-For header (common with proxies/load balancers)
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        return x_forwarded_for.split(",")[0].strip()

    # Check for X-Real-IP header (nginx proxy)
    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return x_real_ip.strip()

    # Fallback to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


def is_device_fingerprint_valid(
    stored_fingerprint: str, current_fingerprint: str, tolerance: float = 0.8
) -> bool:
    """
    Check if two device fingerprints are similar enough to be considered the same device.

    This allows for some variation in headers while maintaining security.

    Args:
        stored_fingerprint: Previously stored fingerprint
        current_fingerprint: Current request fingerprint
        tolerance: Similarity threshold (0.0 to 1.0)

    Returns:
        True if fingerprints are similar enough
    """
    # For now, use exact matching for security
    # In the future, could implement fuzzy matching for better UX
    return stored_fingerprint == current_fingerprint


def get_device_info_for_logging(request: Request) -> dict:
    """
    Extract device information for logging purposes.

    Uses anonymized IP for privacy while maintaining security value.

    Returns a dictionary with device/browser information.
    """
    client_ip = get_client_ip(request)
    return {
        "user_agent": request.headers.get("user-agent", "unknown"),
        "ip_address": _anonymize_ip_for_fingerprint(client_ip),
        "accept_language": request.headers.get("accept-language", ""),
        "platform": extract_platform_from_user_agent(
            request.headers.get("user-agent", "")
        ),
    }


def extract_platform_from_user_agent(user_agent: str) -> str:
    """
    Extract platform information from user agent string.

    Returns a simplified platform identifier.
    """
    user_agent_lower = user_agent.lower()

    # Check for mobile platforms first (more specific)
    if "android" in user_agent_lower:
        return "Android"
    elif "iphone" in user_agent_lower or "ipad" in user_agent_lower:
        return "iOS"
    elif "windows" in user_agent_lower:
        return "Windows"
    elif "macintosh" in user_agent_lower or "mac os" in user_agent_lower:
        return "macOS"
    elif "linux" in user_agent_lower:
        return "Linux"
    else:
        return "Unknown"
