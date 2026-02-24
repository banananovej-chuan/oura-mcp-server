"""Authentication status and profile tools."""

from oura_mcp_server.api.client import get_personal_info, get_ring_configuration
from oura_mcp_server.config import get_config
from oura_mcp_server.mcp_instance import mcp


@mcp.tool()
async def oura_auth_status() -> str:
    """Check if the Oura Ring API connection is working.

    Validates your Personal Access Token by making a test API call.
    If not authenticated, provides instructions for setting up credentials.
    """
    config = get_config()
    if not config.access_token:
        return (
            "Not authenticated.\n\n"
            "To authenticate, set the OURA_ACCESS_TOKEN environment variable:\n"
            "1. Go to https://cloud.ouraring.com/personal-access-tokens\n"
            "2. Create a new Personal Access Token\n"
            "3. Set OURA_ACCESS_TOKEN=<token> in your .env file"
        )

    result = await get_personal_info()
    if isinstance(result, dict) and result.get("error"):
        return f"Token found but authentication failed: {result.get('message')}"

    email = result.get("email", "unknown")
    age = result.get("age")
    info = f"email={email}"
    if age:
        info += f", age={age}"
    return f"Authenticated successfully. Connected to Oura account ({info})."


@mcp.tool()
async def oura_get_profile() -> str:
    """Get your Oura Ring personal profile information.

    Returns age, weight, height, biological sex, and email.
    """
    result = await get_personal_info()
    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    lines = ["Oura Profile"]
    fields = [
        ("email", "Email"),
        ("age", "Age"),
        ("weight", "Weight (kg)"),
        ("height", "Height (m)"),
        ("biological_sex", "Biological Sex"),
    ]
    for key, label in fields:
        val = result.get(key)
        if val is not None:
            lines.append(f"  {label}: {val}")
    return "\n".join(lines)


@mcp.tool()
async def oura_get_ring_config() -> str:
    """Get Oura Ring hardware information.

    Returns ring model, color, design, firmware version, and size.
    """
    result = await get_ring_configuration()
    if isinstance(result, dict) and result.get("error"):
        return f"Error: {result.get('message')}"

    items = result.get("data", [])
    if not items:
        return "No ring configuration data found."

    lines = ["Ring Configuration"]
    for ring in items:
        lines.append(f"\n  Hardware Type: {ring.get('hardware_type', 'N/A')}")
        lines.append(f"  Color: {ring.get('color', 'N/A')}")
        lines.append(f"  Design: {ring.get('design', 'N/A')}")
        lines.append(f"  Firmware: {ring.get('firmware_version', 'N/A')}")
        lines.append(f"  Size: {ring.get('size', 'N/A')}")
        set_up = ring.get("set_up_at")
        if set_up:
            lines.append(f"  Set Up: {set_up[:10]}")
    return "\n".join(lines)
