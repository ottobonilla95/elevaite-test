"""
Kevel Tools (ported from Agent Studio)

These are local tools for the workflow-core-sdk that call the Kevel API.
They are registered like other local SDK tools so they can be resolved by name.

Environment variables:
- KEVEL_API_KEY: API key for Kevel
- KEVEL_API_BASE_URL: Base URL (default https://api.kevel.co/v1)
- KEVEL_NETWORK_ID: Network ID (default 11679)
"""

from __future__ import annotations

import json
import os
import requests
from typing import Dict

from .decorators import function_schema

# Config from environment (with sane defaults)
KEVEL_API_KEY = os.getenv("KEVEL_API_KEY")
KEVEL_API_BASE = os.getenv("KEVEL_API_BASE_URL", "https://api.kevel.co/v1")
try:
    KEVEL_NETWORK_ID = int(os.getenv("KEVEL_NETWORK_ID", "11679"))
except ValueError:
    KEVEL_NETWORK_ID = 11679


@function_schema
def kevel_get_sites() -> str:
    """
    Get all available sites from a Kevel network.

    Returns a JSON string:
    {
      "success": true|false,
      "message": str,
      "sites": [ {"Id": int, "Name": str, "Domain": str}, ... ],
      "error": str | null
    }
    """
    try:
        if not KEVEL_API_KEY:
            return json.dumps(
                {
                    "success": False,
                    "message": "Kevel API key not configured",
                    "error": "Missing KEVEL_API_KEY in environment variables",
                }
            )

        headers = {
            "X-Adzerk-ApiKey": KEVEL_API_KEY,
            "Content-Type": "application/json",
        }

        # Try different possible endpoints for sites
        endpoints_to_try = [
            f"{KEVEL_API_BASE}/site",
            f"{KEVEL_API_BASE}/network/{KEVEL_NETWORK_ID}/site",
            f"{KEVEL_API_BASE}/advertiser/site",
        ]

        last_error = None
        response = None
        for endpoint in endpoints_to_try:
            try:
                r = requests.get(endpoint, headers=headers, timeout=10)
                # Debug logging (trim to avoid huge logs)
                print(
                    f"[Kevel] Sites endpoint={endpoint} status={r.status_code} body={r.text[:200]}..."
                )
                if r.status_code == 200:
                    response = r
                    break
                else:
                    last_error = f"HTTP {r.status_code}: {r.text[:200]}"
            except Exception as e:  # network or other error
                last_error = str(e)
                continue
        else:
            # If loop completes without break
            return json.dumps(
                {
                    "success": False,
                    "message": "Failed to retrieve sites from all attempted endpoints",
                    "error": f"Last error: {last_error}",
                    "attempted_endpoints": endpoints_to_try,
                }
            )

        assert response is not None
        if response.status_code == 200:
            sites = response.json()
            return json.dumps(
                {
                    "success": True,
                    "message": f"Retrieved {len(sites)} sites from network {KEVEL_NETWORK_ID}",
                    "sites": sites,
                }
            )
        else:
            return json.dumps(
                {
                    "success": False,
                    "message": f"Failed to retrieve sites: HTTP {response.status_code}",
                    "error": response.text,
                }
            )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error connecting to Kevel API",
                "error": str(e),
            }
        )


@function_schema
def kevel_get_ad_types() -> str:
    """
    Get available ad types (sizes) from a Kevel network and generate unique element IDs.

    Returns a JSON string:
    {
      "success": true|false,
      "message": str,
      "ad_types": [ {"Id": int, "Name": str, "Width": int, "Height": int, "element_id": str}, ... ],
      "error": str | null
    }
    """
    try:
        import uuid

        if not KEVEL_API_KEY:
            return json.dumps(
                {
                    "success": False,
                    "message": "Kevel API key not configured",
                    "error": "Missing KEVEL_API_KEY in environment variables",
                }
            )

        headers = {
            "X-Adzerk-ApiKey": KEVEL_API_KEY,
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"{KEVEL_API_BASE}/adtypes",
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
            response_data = response.json()

            # Extract the items array from the response
            if isinstance(response_data, dict) and "items" in response_data:
                ad_types = response_data["items"]
            else:
                ad_types = response_data  # Fallback for direct array response

            # Add unique element IDs to each ad type
            for ad_type in ad_types:
                unique_id = str(uuid.uuid4())[:8]
                ad_type["element_id"] = f"azk{unique_id}"

            return json.dumps(
                {
                    "success": True,
                    "message": f"Retrieved {len(ad_types)} ad types from network {KEVEL_NETWORK_ID} with unique element IDs",
                    "ad_types": ad_types,
                }
            )
        else:
            return json.dumps(
                {
                    "success": False,
                    "message": f"Failed to retrieve ad types: HTTP {response.status_code}",
                    "error": response.text,
                }
            )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error connecting to Kevel API",
                "error": str(e),
            }
        )


@function_schema
def kevel_debug_api() -> str:
    """
    Debug tool to explore Kevel API endpoints and help troubleshoot connectivity.

    Returns a JSON string with an array of endpoints tested and their statuses.
    """
    try:
        if not KEVEL_API_KEY:
            return json.dumps(
                {
                    "success": False,
                    "message": "Kevel API key not configured",
                    "error": "Missing KEVEL_API_KEY in environment variables",
                }
            )

        headers = {
            "X-Adzerk-ApiKey": KEVEL_API_KEY,
            "Content-Type": "application/json",
        }

        endpoints_to_test = [
            "/",
            "/network",
            f"/network/{KEVEL_NETWORK_ID}",
            "/site",
            f"/network/{KEVEL_NETWORK_ID}/site",
            "/adtype",
            f"/network/{KEVEL_NETWORK_ID}/adtype",
            "/advertiser",
            "/channel",
        ]

        results: list[Dict[str, object]] = []
        for endpoint in endpoints_to_test:
            try:
                url = f"{KEVEL_API_BASE}{endpoint}"
                response = requests.get(url, headers=headers, timeout=5)
                results.append(
                    {
                        "endpoint": endpoint,
                        "url": url,
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                        "response_size": len(response.text),
                        "error": None
                        if response.status_code == 200
                        else response.text[:200],
                    }
                )
            except Exception as e:  # network or other error
                results.append(
                    {
                        "endpoint": endpoint,
                        "url": f"{KEVEL_API_BASE}{endpoint}",
                        "status_code": None,
                        "success": False,
                        "response_size": 0,
                        "error": str(e),
                    }
                )

        return json.dumps(
            {
                "success": True,
                "message": f"Tested {len(endpoints_to_test)} endpoints",
                "api_base": KEVEL_API_BASE,
                "network_id": KEVEL_NETWORK_ID,
                "results": results,
            }
        )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "message": "Error during API debug",
                "error": str(e),
            }
        )


# Export store and schemas for aggregation in basic_tools
KEVEL_TOOL_STORE = {
    "kevel_get_sites": kevel_get_sites,
    "kevel_get_ad_types": kevel_get_ad_types,
    "kevel_debug_api": kevel_debug_api,
}

KEVEL_TOOL_SCHEMAS = {
    name: func.openai_schema for name, func in KEVEL_TOOL_STORE.items()
}
