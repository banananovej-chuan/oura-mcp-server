"""Oura Ring MCP Server entry point."""

import logging

from mcp.server.fastmcp import FastMCP

import oura_mcp_server.mcp_instance as mcp_module
from oura_mcp_server.api.client import setup_api_client
from oura_mcp_server.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oura_mcp_server")

# Load config
config = get_config()

# Create FastMCP instance
mcp = FastMCP("oura", lifespan=setup_api_client)

# Set shared instance to break circular imports
mcp_module.mcp = mcp

# Import tools — they self-register via @mcp.tool() decorators
from oura_mcp_server.tools.auth import oura_auth_status, oura_get_profile, oura_get_ring_config  # noqa: E402, F401
from oura_mcp_server.tools.sleep import oura_get_sleep, oura_get_sleep_period  # noqa: E402, F401
from oura_mcp_server.tools.activity import oura_get_activity, oura_get_workout  # noqa: E402, F401
from oura_mcp_server.tools.readiness import oura_get_readiness  # noqa: E402, F401
from oura_mcp_server.tools.heart import oura_get_heart_rate  # noqa: E402, F401
from oura_mcp_server.tools.body import oura_get_spo2, oura_get_resilience  # noqa: E402, F401
from oura_mcp_server.tools.tags import oura_get_tags  # noqa: E402, F401
from oura_mcp_server.tools.analytics import (  # noqa: E402, F401
    oura_sleep_trend,
    oura_activity_trend,
    oura_readiness_trend,
    oura_recovery_status,
)
from oura_mcp_server.tools.correlations import (  # noqa: E402, F401
    oura_correlate,
    oura_sleep_activity_correlation,
    oura_hrv_analysis,
    oura_weekly_report,
)


def main():
    """Run the MCP server, or handle 'auth' subcommand."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        _run_auth()
        return

    logger.info("Starting Oura Ring MCP server...")
    mcp.run()


def _run_auth():
    """Run the OAuth2 authorization flow."""
    from oura_mcp_server.auth.oauth import run_oauth_flow

    config = get_config()
    if not config.client_id or not config.client_secret:
        print("Error: OURA_CLIENT_ID and OURA_CLIENT_SECRET must be set.")
        print("")
        print("1. Go to https://cloud.ouraring.com and create an application")
        print("2. Set redirect URI to: http://localhost:8099/callback")
        print("3. Add to your .env file:")
        print("   OURA_CLIENT_ID=your_client_id")
        print("   OURA_CLIENT_SECRET=your_client_secret")
        import sys
        sys.exit(1)

    success = run_oauth_flow(config.client_id, config.client_secret)
    import sys
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
