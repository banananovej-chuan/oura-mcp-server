# Oura Ring MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes Oura Ring health data to AI assistants like Claude. Access sleep, activity, readiness, heart rate, HRV, SpO2, and more — plus built-in analytics and correlation tools.

## Quick Start

### 1. Get an Oura Personal Access Token

1. Go to [cloud.ouraring.com/personal-access-tokens](https://cloud.ouraring.com/personal-access-tokens)
2. Create a new Personal Access Token
3. Copy the token

### 2. Install & Configure

#### Claude Desktop / Claude Code

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "oura": {
      "command": "uvx",
      "args": ["oura-mcp-server"],
      "env": {
        "OURA_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

#### Local Development

```bash
git clone https://github.com/banananovej-chuan/oura-mcp-server.git
cd oura-mcp-server
cp .env.example .env
# Edit .env with your OURA_ACCESS_TOKEN
uv run python -m oura_mcp_server
```

## Tools (20)

### Auth & Profile
| Tool | Description |
|------|-------------|
| `oura_auth_status` | Check if Oura PAT is valid and connection works |
| `oura_get_profile` | Get personal info (age, weight, height) |
| `oura_get_ring_config` | Get ring hardware info (model, color, firmware) |

### Sleep
| Tool | Description |
|------|-------------|
| `oura_get_sleep` | Daily sleep summary (score, duration, stages) |
| `oura_get_sleep_period` | Detailed sleep period (HR, HRV, stages timeline) |

### Activity
| Tool | Description |
|------|-------------|
| `oura_get_activity` | Daily activity summary (steps, calories, movement) |
| `oura_get_workout` | Workout sessions (type, duration, intensity) |

### Readiness & Heart
| Tool | Description |
|------|-------------|
| `oura_get_readiness` | Readiness score and contributors |
| `oura_get_heart_rate` | Heart rate data (5-min intervals) |

### Body & Tags
| Tool | Description |
|------|-------------|
| `oura_get_spo2` | Blood oxygen (SpO2) readings |
| `oura_get_resilience` | Stress resilience data |
| `oura_get_tags` | User-created tags (mood, symptoms, notes) |

### Analytics
| Tool | Description |
|------|-------------|
| `oura_sleep_trend` | Multi-day sleep analysis (avg score, consistency) |
| `oura_activity_trend` | Multi-day activity analysis (avg steps, calories) |
| `oura_readiness_trend` | Multi-day readiness analysis (score trend) |
| `oura_recovery_status` | Today's combined recovery snapshot |

### Correlations & Advanced
| Tool | Description |
|------|-------------|
| `oura_correlate` | Correlate any two metrics with Pearson coefficient |
| `oura_sleep_activity_correlation` | How activity affects next-night sleep |
| `oura_hrv_analysis` | HRV trend with baseline and anomaly detection |
| `oura_weekly_report` | Comprehensive weekly digest with week-over-week comparison |

## Example Prompts

- "How did I sleep last night?"
- "Show me my readiness trend for the past 2 weeks"
- "Is there a correlation between my steps and sleep quality?"
- "Give me a weekly health report for the last month"
- "What's my HRV trend looking like?"
- "How's my recovery status today?"

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
python tests/test_e2e.py

# Run server locally
uv run python -m oura_mcp_server
```

## License

MIT
