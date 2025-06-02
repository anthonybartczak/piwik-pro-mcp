#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
import requests
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("piwik-pro-mcp")

# Load environment variables
load_dotenv()

# Piwik PRO API configuration
PIWIK_PRO_CLIENT_ID = os.getenv("PIWIK_PRO_CLIENT_ID")
PIWIK_PRO_CLIENT_SECRET = os.getenv("PIWIK_PRO_CLIENT_SECRET")
PIWIK_PRO_DOMAIN = os.getenv(
    "PIWIK_PRO_DOMAIN", "analytics.piwik.pro"
)  # Default domain

# Log configuration status
logger.info("Initializing Piwik PRO MCP server")
logger.debug(f"Domain: {PIWIK_PRO_DOMAIN}")
logger.debug(f"Client ID present: {bool(PIWIK_PRO_CLIENT_ID)}")
logger.debug(f"Client Secret present: {bool(PIWIK_PRO_CLIENT_SECRET)}")

# Base API URL
BASE_URL = f"https://{PIWIK_PRO_DOMAIN}"


# Models
class PiwikAnalytics:
    def __init__(self, client_id: str, client_secret: str, domain: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.domain = domain
        self.token = None
        self.token_expiry = None
        logger.info("PiwikAnalytics client initialized")

    def _get_auth_token(self):
        """Get OAuth2 token for Piwik PRO API."""
        current_timestamp = datetime.now().timestamp()
        if self.token and self.token_expiry and current_timestamp < self.token_expiry:
            logger.debug("Using existing auth token")
            return self.token
        logger.info("Requesting new auth token")
        auth_url = f"{BASE_URL}/auth/token"
        try:
            response = requests.post(
                auth_url,
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self.token_expiry = current_timestamp + expires_in
            logger.info("Successfully obtained new auth token")
            return self.token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get auth token: {str(e)}")
            raise Exception(f"Authentication failed: {str(e)}")

    def _make_api_call(
        self, endpoint: str, method: str = "GET", data: Dict = None, params: Dict = None
    ):
        """Make an API call to Piwik PRO."""
        logger.debug(f"Making API call to {endpoint} with method {method}")
        if data:
            logger.debug(f"Request body: {json.dumps(data, indent=2)}")
        if params:
            logger.debug(f"Request params: {json.dumps(params, indent=2)}")
        token = self._get_auth_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        url = f"{BASE_URL}{endpoint}"
        logger.debug(f"Full URL: {url}")
        logger.debug(
            f"Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, indent=2)}"
        )
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            response.raise_for_status()
            logger.debug(f"API call successful: {response.status_code}")
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.warning("Response was not JSON, returning text")
                return response.text
        except requests.exceptions.RequestException as e:
            error_msg = f"API call failed: {str(e)}"
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += (
                        f"\nError details: {json.dumps(error_details, indent=2)}"
                    )
                except json.JSONDecodeError:
                    error_msg += f"\nResponse text: {e.response.text}"
                error_msg += f"\nStatus code: {e.response.status_code}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def get_websites(self):
        """Get all websites/apps configured in Piwik PRO."""
        return self._make_api_call("/api/apps/v2")

    def get_website_details(self, website_id: str):
        """Get details for a specific website/app."""
        return self._make_api_call(f"/api/apps/v2/{website_id}")

    def get_metrics(
        self, website_id: str, date_from: str, date_to: str, columns: List[str]
    ):
        """Get analytics metrics for a website.

        Args:
            website_id: The ID of the website/app to get metrics for
            date_from: Start date in YYYY-MM-DD format
            date_to: End date in YYYY-MM-DD format
            columns: List of columns to retrieve. Supported columns:
                - visits: sessions (Total number of sessions)
                - pageviews: page_views (Total number of page views)
                - bounce_rate: bounce_rate (Percentage of sessions with only one page view)
                - avg_time_on_site: session_total_time (Total time spent on site, in seconds)
                - unique_visitors: visitors (Number of unique visitors)
                - conversion_rate: goal_conversion_rate (Percentage of sessions with goal conversions)
                - revenue: revenue (Total revenue)
                - cart_abandonment: abandoned_cart_rate (Percentage of sessions with abandoned carts)
                - avg_order_value: revenue/ecommerce_conversions (Average revenue per order)
                - exit_rate: exit_rate (Percentage of sessions ending on a page)
                - entry_rate: entry_rate (Percentage of sessions starting on a page)
        """
        metric_mapping = {
            "visits": "sessions",
            "pageviews": "page_views",
            "bounce_rate": "bounce_rate",
            "avg_time_on_site": "session_total_time",
            "unique_visitors": "visitors",
            "conversion_rate": "goal_conversion_rate",
            "revenue": "revenue",
            "cart_abandonment": "abandoned_cart_rate",
            "exit_rate": "exit_rate",
            "entry_rate": "entry_rate",
        }

        # Convert columns to column objects with proper IDs
        column_configs = []
        for column in columns:
            if column in metric_mapping:
                column_config = {"column_id": metric_mapping[column]}
                column_configs.append(column_config)
            else:
                logger.warning(f"Unknown column: {column}")

        data = {
            "website_id": website_id,
            "date_from": date_from,
            "date_to": date_to,
            "columns": column_configs,
            "format": "json",
            "column_format": "id",
            "offset": 0,
            "limit": 100,
            "options": {"sampling": 1.0},
        }
        return self._make_api_call("/api/analytics/v1/query", method="POST", data=data)

    def create_annotation(
        self,
        website_id: str,
        content: str,
        date: str = None,
        visibility: str = "private",
    ):
        """Create an annotation for a website.

        Args:
            website_id: The ID of the website/app to create an annotation for
            content: Content of the annotation (max 150 characters)
            date: Date for the annotation in YYYY-MM-DD format (defaults to today if not provided)
            visibility: Visibility of the annotation ("private" or "public", defaults to "private")
        """
        data = {
            "data": {
                "type": "UserAnnotation",
                "attributes": {
                    "content": content,
                    "website_id": website_id,
                    "date": date or datetime.now().strftime("%Y-%m-%d"),
                    "visibility": visibility,
                },
            }
        }
        return self._make_api_call(
            "/api/analytics/v1/manage/annotation/user/", method="POST", data=data
        )

    def get_annotations(self, website_id: str):
        """Get all annotations for a website."""
        return self._make_api_call(
            f"/api/analytics/v1/manage/annotation/user?website_id={website_id}"
        )


# Initialize Piwik PRO client
piwik = None
if PIWIK_PRO_CLIENT_ID and PIWIK_PRO_CLIENT_SECRET:
    try:
        piwik = PiwikAnalytics(
            client_id=PIWIK_PRO_CLIENT_ID,
            client_secret=PIWIK_PRO_CLIENT_SECRET,
            domain=PIWIK_PRO_DOMAIN,
        )
        logger.info("Piwik PRO client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Piwik PRO client: {str(e)}")
else:
    logger.warning("Piwik PRO client not initialized - missing credentials")

# Initialize FastMCP server
mcp = FastMCP("piwik-pro")
logger.info("FastMCP server initialized")


@mcp.tool()
async def list_websites() -> str:
    """List all websites/apps tracked in Piwik PRO."""
    logger.info("Executing list_websites tool")
    if not piwik:
        error_msg = "Piwik PRO API client not initialized. Check credentials."
        logger.error(error_msg)
        raise Exception(error_msg)
    try:
        websites = piwik.get_websites()
        logger.info("Successfully retrieved websites")
        return json.dumps(websites, indent=2)
    except Exception as e:
        logger.error(f"Error in list_websites: {str(e)}")
        raise Exception(str(e))


@mcp.tool()
async def get_website_details(website_id: str) -> str:
    """Get details for a specific website/app.

    Args:
        website_id: The ID of the website/app to get details for
    """
    if not piwik:
        raise Exception("Piwik PRO API client not initialized. Check credentials.")
    if not website_id:
        raise Exception("website_id is required")
    try:
        details = piwik.get_website_details(website_id)
        return json.dumps(details, indent=2)
    except Exception as e:
        raise Exception(str(e))


@mcp.tool()
async def get_metrics(
    website_id: str, date_from: str, date_to: str, columns: List[str]
) -> str:
    """Get analytics metrics for a website.

    Args:
        website_id: The ID of the website/app to get metrics for
        date_from: Start date in YYYY-MM-DD format
        date_to: End date in YYYY-MM-DD format
        columns: List of columns to retrieve. Supported columns:
            - visits: sessions (Total number of sessions)
            - pageviews: page_views (Total number of page views)
            - bounce_rate: bounce_rate (Percentage of sessions with only one page view)
            - avg_time_on_site: session_total_time (Total time spent on site, in seconds)
            - unique_visitors: visitors (Number of unique visitors)
            - conversion_rate: goal_conversion_rate (Percentage of sessions with goal conversions)
            - revenue: revenue (Total revenue)
            - cart_abandonment: abandoned_cart_rate (Percentage of sessions with abandoned carts)
            - avg_order_value: revenue/ecommerce_conversions (Average revenue per order)
            - exit_rate: exit_rate (Percentage of sessions ending on a page)
            - entry_rate: entry_rate (Percentage of sessions starting on a page)
    """
    if not piwik:
        raise Exception("Piwik PRO API client not initialized. Check credentials.")

    if not website_id:
        raise Exception("website_id is required")
    if not date_from:
        raise Exception("date_from is required")
    if not date_to:
        raise Exception("date_to is required")
    if not columns:
        raise Exception("At least one column is required")

    try:
        result = piwik.get_metrics(website_id, date_from, date_to, columns)
        return json.dumps(result, indent=2)
    except Exception as e:
        raise Exception(str(e))


@mcp.tool()
async def create_annotation(
    website_id: str, content: str, date: str = None, visibility: str = "private"
) -> str:
    """Create an annotation for a website.

    Args:
        website_id: The ID of the website/app to create an annotation for
        content: Content of the annotation (max 150 characters)
        date: Date for the annotation in YYYY-MM-DD format (defaults to today if not provided)
        visibility: Visibility of the annotation ("private" or "public", defaults to "private")
    """
    if not piwik:
        raise Exception("Piwik PRO API client not initialized. Check credentials.")
    if not website_id:
        raise Exception("website_id is required")
    if not content:
        raise Exception("content is required")
    if len(content) > 150:
        raise Exception("content must be 150 characters or less")
    if visibility not in ["private", "public"]:
        raise Exception("visibility must be 'private' or 'public'")
    try:
        result = piwik.create_annotation(website_id, content, date, visibility)
        return json.dumps(result, indent=2)
    except Exception as e:
        raise Exception(str(e))


@mcp.tool()
async def get_annotations(website_id: str) -> str:
    """Get all annotations for a website.

    Args:
        website_id: The ID of the website/app to get annotations for
    """
    if not piwik:
        raise Exception("Piwik PRO API client not initialized. Check credentials.")
    if not website_id:
        raise Exception("website_id is required")
    try:
        result = piwik.get_annotations(website_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        raise Exception(str(e))


if __name__ == "__main__":
    logger.info("Starting Piwik PRO MCP server")
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
