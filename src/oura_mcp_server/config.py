import os
from dataclasses import dataclass

from dotenv import load_dotenv

_ = load_dotenv()


@dataclass
class Config:
    access_token: str
    api_base_url: str
    client_id: str
    client_secret: str


_config_instance: Config | None = None


def load_config() -> Config:
    """Load configuration from environment variables.

    Supports two auth modes:
    1. OAuth2 (recommended): Set OURA_CLIENT_ID + OURA_CLIENT_SECRET, then run `oura-mcp-server auth`
    2. PAT (legacy): Set OURA_ACCESS_TOKEN directly
    """
    access_token = os.getenv("OURA_ACCESS_TOKEN", "")
    client_id = os.getenv("OURA_CLIENT_ID", "")
    client_secret = os.getenv("OURA_CLIENT_SECRET", "")
    api_base_url = os.getenv(
        "OURA_API_BASE_URL", "https://api.ouraring.com/v2/usercollection"
    )

    # If no PAT but OAuth credentials exist, try to load stored token
    if not access_token and client_id and client_secret:
        from oura_mcp_server.auth.oauth import get_access_token
        token = get_access_token(client_id, client_secret)
        if token:
            access_token = token

    return Config(
        access_token=access_token,
        api_base_url=api_base_url,
        client_id=client_id,
        client_secret=client_secret,
    )


def get_config() -> Config:
    """Get singleton config instance."""
    global _config_instance, _token_mtime
    mtime = _current_token_mtime()
    if _config_instance is None or mtime != _token_mtime:
        # Reload when the token file changes (e.g. after `oura-mcp-server auth`
        # in a terminal) so a running server never keeps a stale token.
        _config_instance = load_config()
        _token_mtime = _current_token_mtime()
    return _config_instance


_token_mtime: float | None = None


def _current_token_mtime() -> float | None:
    from oura_mcp_server.auth.oauth import TOKEN_FILE
    try:
        return TOKEN_FILE.stat().st_mtime
    except OSError:
        return None


def reload_config() -> Config:
    """Force reload config (e.g. after token refresh)."""
    global _config_instance
    _config_instance = load_config()
    return _config_instance
