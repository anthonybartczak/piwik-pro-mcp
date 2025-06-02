# Piwik PRO MCP Server 📊

A Model Context Protocol (MCP) server for interacting with Piwik PRO Analytics Suite. Access your analytics data, manage websites, create annotations.

## Features 🚀

- **List Websites**: View all tracked websites/apps in your Piwik PRO account
- **Get Website Details**: Retrieve detailed information about specific websites
- **Query Analytics**: Get key metrics like visitors, pageviews, and more
- **Create Annotations**: Add private or public annotations to your Piwik PRO analytics with optional timestamps
- **View Annotations**: List all annotations for specific websites

## Setup 🛠️

### Prerequisites

- Python 3.10 or higher
- Piwik PRO account with API access
- Client ID and Client Secret from Piwik PRO

### Installation

Follow the instructions from the [Set up your environment](https://modelcontextprotocol.io/quickstart/server#set-up-your-environment) section.

### Configuration

1. Create a `.env` file based on the provided `.env-example`

2. Edit the `.env` file and fill in your Piwik PRO API credentials & domain

## Claude Desktop Setup

To use this MCP server with Claude Desktop:

1. Install Claude Desktop from [claude.ai](https://claude.ai/download)

2. Open you Claude Desktop config file:

   ```bash
   # Windows
   code $env:AppData\Claude\claude_desktop_config.json

   #MacOS/Linux
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. Add this to your `claude_desktop_config.json` (adjust paths according to your system):
   ```json
   {
     "mcpServers": {
       "piwik-pro-mcp": {
         "command": "uv",
         "args": ["--directory", "C:\\Project_path", "run", "piwik_pro_mcp.py"]
       }
     }
   }
   ```

## Usage in Claude

Once configured, you can use commands like:

```
Show me the list of websites tracked in my Piwik PRO account.
```

```
Get visitor metrics for website ID X from 2023-01-01 to 2023-01-31.
```

```
Create a private annotation for website ID X with the content "Product Launch" for 2023-04-15.
```

## Development

To run the server directly for testing:

```bash
python piwik_pro_mcp.py
```

## API Endpoints

This MCP server uses the following Piwik PRO API endpoints:

- `/api/apps/v2` - List websites/apps
- `/api/apps/v2/{website_id}` - Get website details
- `/api/analytics/v1/query` - Query analytics data
- `/api/analytics/v1/manage/annotation/user/` - Create and retrieve annotations

## License

MIT
