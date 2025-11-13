import os
import json
import time
import asyncio
import logging
import httpx
from dotenv import load_dotenv
from typing import Optional, Dict, Any

# Load env
current_dir = os.path.dirname(__file__)
env_path = os.path.join(current_dir, '..', '..', '.env')
load_dotenv(env_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class ServiceNowAgentClient:
    """Async client to interact with ServiceNow MITIE RFQ Extractor APIs."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        grant_type: str = "client_credentials",
        timeout: float = 10.0
    ):
        self.base_url = base_url or os.getenv("SERVICENOW_NOW_ASSIST_API_BASE_URL", "https://ven05499.service-now.com/")
        self.client_id = client_id or os.getenv("SERVICENOW_NOW_ASSIST_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SERVICENOW_NOW_ASSIST_CLIENT_SECRET")
        self.grant_type = grant_type
        self.timeout = timeout

        # Derived URLs
        self.oauth_url = f"{self.base_url.rstrip('/')}/oauth_token.do"
        self.table_url = f"{self.base_url.rstrip('/')}/api/now/table/u_mitie_quote_json_extractor"

        logger.info(f"ServiceNow OAuth URL: {self.oauth_url}")

    async def _get_access_token(self) -> str:
        """Fetch OAuth token for ServiceNow API."""
        data = {
            "grant_type": self.grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.oauth_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            token = token_data.get("access_token")
            if not token:
                raise ValueError("Failed to obtain ServiceNow access token")
            return token

    async def _request(self, method: str, url: str, headers: dict, **kwargs) -> Dict[str, Any]:
        """Generic HTTP request helper."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()

    async def trigger_quote_extraction(self, rfq_text: str, user_reference: str) -> Dict[str, Any]:
        """
        Main public method: triggers quote extraction and polls until completion.
        """
        if not rfq_text:
            return {"error": "Missing RFQ Content"}
        if not user_reference:
            return {"error": "Missing User Reference"}

        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Step 1: Trigger extraction
        payload = {
            "u_user_reference": user_reference,
            "u_quote_content": rfq_text
        }
        response = await self._request("POST", self.table_url, headers, json=payload)
        sys_id = response.get("result", {}).get("sys_id")
        if not sys_id:
            raise ValueError("No sys_id returned from ServiceNow trigger API")

        # Step 2: Poll for completion
        record_url = f"{self.table_url}/{sys_id}"
        poll_response = await self._poll_until_success(record_url, headers)
        return self._parse_model_output(poll_response)

    async def _poll_until_success(
        self,
        record_url: str,
        headers: dict,
        timeout_seconds: float = 45.0,
        poll_interval: float = 0.5
    ) -> Dict[str, Any]:
        """Poll until 'u_content_decision' == 'Success' or timeout."""
        start = time.monotonic()
        async with httpx.AsyncClient() as client:
            while True:
                if time.monotonic() - start > timeout_seconds:
                    raise TimeoutError("Timed out waiting for ServiceNow extraction")

                try:
                    response = await client.get(record_url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    decision = data.get("result", {}).get("u_content_decision")
                    if decision and decision.lower() == "success":
                        logger.info(f"Extraction success after {time.monotonic() - start:.1f}s")
                        return data
                    await asyncio.sleep(poll_interval)
                    logger.info(f"Polling for extraction completion: {decision} Elapsed Time {time.monotonic() - start:.1f}s")
                except Exception as e:
                    logger.warning(f"Polling error: {e}")
                    await asyncio.sleep(poll_interval)

    def _parse_model_output(self, snow_response: Dict[str, Any]) -> Dict[str, Any]:
        """Safely extract and parse nested model output JSON."""
        result = snow_response.get("result", {})
        content_str = result.get("u_llm_extracted_content", "{}")

        try:
            outer = json.loads(content_str)
        except json.JSONDecodeError:
            outer = {"model_output": content_str}

        model_output_str = outer.get("model_output", "{}")
        try:
            model_output_json = json.loads(model_output_str)
        except json.JSONDecodeError:
            model_output_json = {"content": model_output_str}

        outer["model_output"] = model_output_json
        return outer
