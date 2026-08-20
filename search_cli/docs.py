"""Structured schema and documentation for AI Agents and CLI users."""

import json
from typing import Any, Dict

CLI_AGENT_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SearchCLI_Agent_Specification",
    "description": "Complete specification and usage guide for AI agents interacting with search-cli.",
    "version": "0.1.0",
    "commands": {
        "query": {
            "description": "Query Google Search Console Search Analytics performance data (clicks, impressions, CTR, position).",
            "arguments": {},
            "options": {
                "--site": {
                    "type": "string",
                    "short": "-s",
                    "required": False,
                    "default": "Configured default_site",
                    "description": "Property URL. Prefix with 'sc-domain:' for domain properties (e.g., 'sc-domain:example.com') or full URL prefix (e.g., 'https://example.com/').",
                },
                "--start-date": {
                    "type": "string",
                    "format": "YYYY-MM-DD",
                    "required": False,
                    "default": "Calculated from --days and --end-date",
                    "description": "Start date for metrics (inclusive).",
                },
                "--end-date": {
                    "type": "string",
                    "format": "YYYY-MM-DD",
                    "required": False,
                    "default": "3 days ago for 'final' data; today for 'all' data",
                    "description": "End date for metrics (inclusive).",
                },
                "--days": {
                    "type": "integer",
                    "default": 28,
                    "description": "Number of days to look back when --start-date is omitted.",
                },
                "--dimension": {
                    "type": "array",
                    "short": "-d",
                    "default": ["query"],
                    "allowed_values": ["query", "page", "country", "device", "date", "searchAppearance"],
                    "description": "Dimensions to group by. Can be repeated or comma-separated.",
                },
                "--filter": {
                    "type": "array",
                    "short": "-f",
                    "default": [],
                    "description": "Dimension filter expression in '<dimension> <operator> <value>' syntax. Can be repeated.",
                    "filter_syntax": {
                        "dimensions": ["query", "page", "country", "device", "searchAppearance"],
                        "operators": {
                            "contains": "Substring match (synonyms: contains, include, has)",
                            "!contains": "Negative substring match (synonyms: !contains, not_contains, exclude)",
                            "==": "Exact match (synonyms: ==, =, equals, eq)",
                            "!=": "Negative exact match (synonyms: !=, not_equals, ne)",
                            "regex": "Regular expression match (synonyms: regex, ~, includingRegex)",
                            "!regex": "Negative regex match (synonyms: !regex, !~, excludingRegex)",
                        },
                        "examples": [
                            "query contains seo",
                            "page == https://example.com/blog",
                            "country == usa",
                            "device != mobile",
                            "query regex ^how to",
                            "page !contains /category/",
                        ],
                    },
                },
                "--search-type": {
                    "type": "string",
                    "short": "-t",
                    "default": "web",
                    "allowed_values": ["web", "image", "video", "news", "discover", "googleNews"],
                    "description": "Filter by search type or feed.",
                },
                "--data-state": {
                    "type": "string",
                    "default": "final",
                    "allowed_values": ["final", "all"],
                    "description": "'final' includes only finalized aggregated data (approx. 2-3 days lag). 'all' includes fresh, provisional data.",
                },
                "--aggregation-type": {
                    "type": "string",
                    "default": "auto",
                    "allowed_values": ["auto", "byPage", "byProperty"],
                    "description": "How data is aggregated across dimensions.",
                },
                "--limit": {
                    "type": "integer",
                    "short": "-l",
                    "default": 25,
                    "min": 1,
                    "max": 25000,
                    "description": "Maximum number of rows returned.",
                },
                "--offset": {
                    "type": "integer",
                    "default": 0,
                    "description": "Starting row offset for pagination.",
                },
                "--sort-by": {
                    "type": "string",
                    "default": "clicks",
                    "description": "Column to sort by: 'clicks', 'impressions', 'ctr', 'position', or dimension names like 'query', 'page'.",
                },
                "--asc": {
                    "type": "boolean",
                    "default": False,
                    "description": "Sort in ascending order instead of descending.",
                },
                "--format": {
                    "type": "string",
                    "default": "table",
                    "allowed_values": ["table", "json", "csv", "tsv"],
                    "description": "Output format. Use 'json' when parsing outputs in code/scripts.",
                },
                "--output": {
                    "type": "string",
                    "short": "-o",
                    "description": "File path to save the output directly.",
                },
            },
            "json_output_schema": {
                "metadata": {
                    "site": "string",
                    "startDate": "YYYY-MM-DD",
                    "endDate": "YYYY-MM-DD",
                    "searchType": "string",
                    "dimensions": ["string"],
                    "responseAggregationType": "string",
                },
                "rowCount": "integer",
                "rows": [
                    {
                        "<dimension_name>": "string",
                        "clicks": "integer",
                        "impressions": "integer",
                        "ctr": "float (0.0 to 1.0)",
                        "position": "float (1.0+)",
                    }
                ],
            },
        },
        "sites list": {
            "description": "List all verified properties accessible to the authenticated account.",
            "options": {
                "--format": {"type": "string", "allowed_values": ["table", "json", "csv"], "default": "table"}
            },
        },
        "sites default": {
            "description": "Set the default site property URL for all subsequent queries.",
            "arguments": {
                "site_url": {"type": "string", "required": True, "description": "e.g. 'sc-domain:example.com' or 'https://example.com/'"}
            },
        },
        "inspect": {
            "description": "Inspect Google index status, verdict, crawl state, and canonical URL for a specific URL.",
            "arguments": {
                "url": {"type": "string", "required": True, "description": "URL to inspect"}
            },
            "options": {
                "--site": {"type": "string", "short": "-s", "description": "Property URL containing the URL"},
                "--format": {"type": "string", "allowed_values": ["table", "json"], "default": "table"},
            },
        },
        "sitemaps list": {
            "description": "List submitted sitemaps, submission/download timestamps, and error/warning counts.",
            "options": {
                "--site": {"type": "string", "short": "-s", "description": "Property URL"}
            },
        },
        "auth status": {
            "description": "Check whether credentials exist, current auth type (oauth or service_account), and token details.",
        },
        "auth login": {
            "description": "Interactive OAuth 2.0 login flow in web browser.",
            "options": {
                "--credentials": {"type": "string", "short": "-c", "description": "Path to client_secrets.json"},
                "--client-id": {"type": "string", "description": "OAuth Client ID string"},
                "--client-secret": {"type": "string", "description": "OAuth Client Secret string"},
                "--port": {"type": "integer", "short": "-p", "default": 0},
                "--no-browser": {"type": "boolean", "default": False},
            },
        },
        "auth service-account": {
            "description": "Configure a Google Cloud Service Account JSON key for headless execution.",
            "options": {
                "--key": {"type": "string", "short": "-k", "required": True, "description": "Path to service_account.json"}
            },
        },
        "config list": {
            "description": "List all configured defaults and settings.",
        },
        "config set": {
            "description": "Set a persistent config key and value.",
            "arguments": {
                "key": {"type": "string", "required": True},
                "value": {"type": "string", "required": True},
            },
        },
    },
    "agent_tips": [
        "Always recommend using --format json when piping or programmatically processing search analytics data.",
        "To query without specifying --site every time, first call `search-cli sites default <site_url>`.",
        "Google Search Console final data has a 2-3 day lag. For today's provisional data, pass `--data-state all`.",
        "Country codes in filters are 3-letter ISO-3166-1-alpha-3 codes in lowercase (e.g., 'usa', 'gbr', 'deu', 'fra', 'can').",
        "Device dimension values are: 'desktop', 'mobile', 'tablet'.",
    ],
}

QUERY_HELP_EPILOG = """
[bold yellow]AI AGENT QUERY GUIDE & EXAMPLES:[/bold yellow]

[bold cyan]1. Top queries in last 28 days (JSON format):[/bold cyan]
  $ search-cli query --site sc-domain:example.com --limit 10 --format json

[bold cyan]2. Multi-dimension breakdown (Query + Landing Page):[/bold cyan]
  $ search-cli query --dimension query,page --limit 50 --sort-by clicks

[bold cyan]3. Filter queries by substring or regex:[/bold cyan]
  $ search-cli query --filter "query contains pricing"
  $ search-cli query --filter "query regex ^how to"
  $ search-cli query --filter "page !contains /category/"

[bold cyan]4. Filter by Country and Device:[/bold cyan]
  $ search-cli query --dimension query --filter "country == usa" --filter "device == mobile"
  [dim](Note: Countries use 3-letter ISO codes like usa, gbr, deu, fra)[/dim]

[bold cyan]5. Specific date range & fresh provisional data:[/bold cyan]
  $ search-cli query --start-date 2026-01-01 --end-date 2026-01-31 --data-state all

[bold cyan]6. Export directly to CSV file:[/bold cyan]
  $ search-cli query --dimension query,page,country --format csv --output report.csv

[bold cyan]7. Automated AI Inspection / Schema:[/bold cyan]
  $ search-cli guide --json
"""

MAIN_HELP_EPILOG = """
[bold yellow]QUICK START FOR AI AGENTS & USERS:[/bold yellow]

  [bold]Step 1: Check Auth Status[/bold]
  $ search-cli auth status

  [bold]Step 2: List Verified Sites[/bold]
  $ search-cli sites list

  [bold]Step 3: Set Default Site (eliminates need for --site flag)[/bold]
  $ search-cli sites default "sc-domain:example.com"

  [bold]Step 4: Query Search Performance[/bold]
  $ search-cli query --format json --limit 25

  [bold]Get Complete Machine-Readable Schema:[/bold]
  $ search-cli guide --json
"""
