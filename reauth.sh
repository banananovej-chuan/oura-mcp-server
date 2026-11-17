#!/bin/bash
# Re-run the Oura OAuth flow using the client credentials from Claude Desktop's config.
set -e
cd "$HOME/Desktop/vibecoding/oura-mcp-server"
eval "$(python3 -c '
import json, os, shlex
f = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
for k, v in json.load(open(f))["mcpServers"]["oura"]["env"].items():
    print(f"export {k}={shlex.quote(v)}")
')"
exec .venv/bin/python -m oura_mcp_server auth
