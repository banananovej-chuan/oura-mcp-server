"""OAuth2 authorization code flow for Oura Ring API.

Usage:
    oura-mcp-server auth   — opens browser, you copy the code from the redirect URL
"""

import json
import logging
import os
import time
import urllib.parse
import webbrowser
from pathlib import Path

import httpx

logger = logging.getLogger("oura_mcp_server.auth")

TOKEN_URL = "https://api.ouraring.com/oauth/token"
AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
ALL_SCOPES = "email personal daily heartrate workout tag session spo2"

# Token storage
TOKEN_FILE = Path.home() / ".oura-mcp-tokens.json"


def _get_redirect_uri() -> str:
    """Get redirect URI from env or default."""
    return os.getenv("OURA_REDIRECT_URI", "https://www.chuan.cz/")


def _get_token_path() -> Path:
    return TOKEN_FILE


def save_tokens(tokens: dict) -> None:
    """Save OAuth tokens to disk."""
    tokens["saved_at"] = time.time()
    _get_token_path().write_text(json.dumps(tokens, indent=2))
    _get_token_path().chmod(0o600)
    logger.info("Tokens saved to %s", _get_token_path())


def load_tokens() -> dict | None:
    """Load OAuth tokens from disk. Returns None if not found."""
    path = _get_token_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def clear_tokens() -> None:
    """Remove stored tokens."""
    path = _get_token_path()
    if path.exists():
        path.unlink()


def get_access_token(client_id: str, client_secret: str) -> str | None:
    """Get a valid access token, refreshing if needed.

    Returns the access token string or None if no tokens are available.
    """
    tokens = load_tokens()
    if not tokens:
        return None

    # Check if token is expired (with 60s buffer)
    saved_at = tokens.get("saved_at", 0)
    expires_in = tokens.get("expires_in", 0)
    if time.time() > saved_at + expires_in - 60:
        # Try refresh
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return None
        new_tokens = refresh_access_token(client_id, client_secret, refresh_token)
        if new_tokens:
            return new_tokens.get("access_token")
        return None

    return tokens.get("access_token")


def refresh_access_token(
    client_id: str, client_secret: str, refresh_token: str
) -> dict | None:
    """Exchange a refresh token for a new access token."""
    try:
        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        tokens = response.json()
        save_tokens(tokens)
        logger.info("Token refreshed successfully.")
        return tokens
    except Exception as e:
        logger.error("Token refresh failed: %s", e)
        return None


def exchange_code_for_token(
    client_id: str, client_secret: str, code: str
) -> dict | None:
    """Exchange authorization code for access + refresh tokens."""
    redirect_uri = _get_redirect_uri()
    try:
        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        tokens = response.json()
        save_tokens(tokens)
        return tokens
    except Exception as e:
        logger.error("Code exchange failed: %s", e)
        return None


def run_oauth_flow(client_id: str, client_secret: str) -> bool:
    """Run the OAuth2 authorization code flow with manual code copy.

    1. Open the browser to Oura's authorization page
    2. User authorizes and gets redirected to the redirect URI
    3. User copies the 'code' parameter from the URL bar
    4. Exchange the code for tokens
    5. Save tokens to disk

    Returns True on success.
    """
    redirect_uri = _get_redirect_uri()

    # Build authorization URL
    auth_params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": ALL_SCOPES,
    })
    auth_url = f"{AUTHORIZE_URL}?{auth_params}"

    print(f"\nOpening browser for Oura authorization...")
    print(f"\n  URL: {auth_url}\n")
    print("If the browser doesn't open, copy the URL above and paste it manually.")
    print(f"\nAfter authorizing, you'll be redirected to {redirect_uri}")
    print("Copy the FULL URL from your browser's address bar and paste it here.")
    print("(It will look like: {redirect_uri}?code=XXXXX&scope=...)\n")

    webbrowser.open(auth_url)

    # Wait for user to paste the redirect URL or code
    user_input = input("Paste the redirect URL or just the code: ").strip()

    # Extract code from URL or use raw input
    if "code=" in user_input:
        parsed = urllib.parse.urlparse(user_input)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
    else:
        code = user_input

    if not code:
        print("No authorization code found.")
        return False

    # Exchange code for tokens
    print("Exchanging authorization code for tokens...")
    tokens = exchange_code_for_token(client_id, client_secret, code)
    if not tokens:
        print("Failed to exchange code for tokens.")
        return False

    print(f"\nAuthorization successful!")
    print(f"  Access token: {tokens['access_token'][:8]}...")
    print(f"  Expires in: {tokens.get('expires_in', 0) // 3600} hours")
    print(f"  Tokens saved to: {_get_token_path()}")
    return True
