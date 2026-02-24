"""Async HTTP client for Oura Ring API v2."""

import logging
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from oura_mcp_server.config import get_config

logger = logging.getLogger("oura_mcp_server.api")

# Global client instance
_httpx_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def setup_api_client(_app: FastMCP):
    """Lifespan context manager for httpx client cleanup."""
    try:
        yield
    finally:
        global _httpx_client
        if _httpx_client and not _httpx_client.is_closed:
            await _httpx_client.aclose()
            _httpx_client = None


def _get_headers() -> dict[str, str]:
    """Build auth headers for Oura API."""
    config = get_config()
    return {
        "Authorization": f"Bearer {config.access_token}",
        "Accept": "application/json",
    }


async def _get_client() -> httpx.AsyncClient:
    """Get or create the shared async HTTP client."""
    global _httpx_client
    if _httpx_client is None or _httpx_client.is_closed:
        _httpx_client = httpx.AsyncClient(timeout=30.0)
    return _httpx_client


async def api_get(
    endpoint: str,
    params: dict[str, str] | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Make an authenticated GET request to the Oura API v2.

    Args:
        endpoint: API endpoint path (e.g. '/daily_sleep')
        params: Optional query parameters

    Returns:
        Parsed JSON response or error dict
    """
    config = get_config()
    if not config.access_token:
        return {
            "error": True,
            "message": (
                "No Oura access token configured. "
                "Set OURA_CLIENT_ID + OURA_CLIENT_SECRET and run 'oura-mcp-server auth', "
                "or set OURA_ACCESS_TOKEN directly."
            ),
        }

    client = await _get_client()
    url = f"{config.api_base_url}/{endpoint}"

    try:
        response = await client.get(url, headers=_get_headers(), params=params)

        # Auto-refresh on 401 if OAuth credentials available
        if response.status_code == 401 and config.client_id and config.client_secret:
            from oura_mcp_server.auth.oauth import load_tokens, refresh_access_token
            from oura_mcp_server.config import reload_config
            tokens = load_tokens()
            if tokens and tokens.get("refresh_token"):
                new_tokens = refresh_access_token(
                    config.client_id, config.client_secret, tokens["refresh_token"]
                )
                if new_tokens:
                    config = reload_config()
                    response = await client.get(url, headers=_get_headers(), params=params)

        response.raise_for_status()

        if response.status_code == 204 or not response.content:
            return {"data": []}

        return response.json()

    except httpx.HTTPStatusError as e:
        return _handle_http_error(e)
    except httpx.RequestError as e:
        logger.error("Request error: %s", e)
        return {
            "error": True,
            "message": f"Network error: {e}. Check your internet connection.",
        }


def _handle_http_error(e: httpx.HTTPStatusError) -> dict[str, Any]:
    """Convert HTTP errors to user-friendly messages."""
    status = e.response.status_code
    messages = {
        401: (
            "Authentication failed. Your Oura access token may be invalid or expired. "
            "Run 'oura-mcp-server auth' to re-authenticate via OAuth2."
        ),
        403: "Access denied. Your token may not have the required scopes.",
        429: "Rate limited (5000 req/5min). Please wait a moment and try again.",
        500: "Oura API server error. Try again later.",
        503: "Oura API is temporarily unavailable. Try again later.",
    }
    message = messages.get(status, f"HTTP {status}: {e.response.text[:200]}")
    logger.error("HTTP error %d: %s", status, message)
    return {"error": True, "message": message}


# ---------- Endpoint-specific functions ----------


async def get_personal_info() -> dict[str, Any]:
    """Get personal info (age, weight, height, email)."""
    config = get_config()
    client = await _get_client()
    url = f"{config.api_base_url}/personal_info"
    try:
        response = await client.get(url, headers=_get_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": True, "message": str(e)}


async def get_ring_configuration() -> dict[str, Any]:
    """Get ring hardware info."""
    return await api_get("ring_configuration")


async def get_daily_sleep(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get daily sleep summaries."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await api_get("daily_sleep", params)


async def get_sleep_periods(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get individual sleep period data."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await api_get("sleep", params)


async def get_daily_activity(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get daily activity summaries."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await api_get("daily_activity", params)


async def get_workouts(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get workout sessions."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await api_get("workout", params)


async def get_daily_readiness(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get daily readiness scores."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await api_get("daily_readiness", params)


async def get_heart_rate(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get heart rate data (5-min intervals)."""
    params = {}
    if start_date:
        params["start_datetime"] = f"{start_date}T00:00:00+00:00"
    if end_date:
        params["end_datetime"] = f"{end_date}T23:59:59+00:00"
    return await api_get("heartrate", params)


async def get_daily_spo2(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get blood oxygen (SpO2) data."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await api_get("daily_spo2", params)


async def get_daily_resilience(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get stress resilience data."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await api_get("daily_resilience", params)


async def get_tags(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get user tags."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    return await api_get("tag", params)
