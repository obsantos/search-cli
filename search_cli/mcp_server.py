"""Model Context Protocol (MCP) server for Google Search Console."""

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from mcp.server.mcpserver import MCPServer

from search_cli import __version__
from search_cli.auth import get_auth_status
from search_cli.client import SearchConsoleClient
from search_cli.config import get_config_value
from search_cli.filters import FilterParseError, build_dimension_filter_groups
from search_cli.formatter import sort_rows

# Initialize the official MCP Server instance
mcp_server = MCPServer(
    name="search-console",
    version=__version__,
    description=(
        "Google Search Console MCP Server: Query Search Analytics metrics "
        "(clicks, impressions, CTR, position), inspect URL indexing status, "
        "and inspect sitemaps."
    ),
    instructions=(
        "Use this tool to interact with Google Search Console data. "
        "Before querying, you can call list_properties to see verified properties. "
        "Search analytics query results contain clicks, impressions, CTR, and average position."
    ),
)


@mcp_server.tool()
def get_authentication_status() -> Dict[str, Any]:
    """Check whether search-cli is authenticated and return account details."""
    return get_auth_status()


@mcp_server.tool()
def list_properties() -> List[Dict[str, Any]]:
    """List all verified Google Search Console properties accessible to the authenticated account."""
    client = SearchConsoleClient()
    sites = client.list_sites()
    default_site = get_config_value("default_site")
    
    result = []
    for s in sites:
        site_url = s.get("siteUrl", "")
        result.append({
            "siteUrl": site_url,
            "permissionLevel": s.get("permissionLevel", "unknown"),
            "isDefault": site_url == default_site,
        })
    return result


@mcp_server.tool()
def query_search_analytics(
    site_url: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days: int = 28,
    dimensions: Optional[List[str]] = None,
    filters: Optional[List[str]] = None,
    search_type: str = "web",
    data_state: str = "final",
    limit: int = 25,
    offset: int = 0,
    sort_by: str = "clicks",
    ascending: bool = False,
) -> Dict[str, Any]:
    """Query Google Search Console search performance metrics.

    Args:
        site_url: Property URL (e.g. 'sc-domain:example.com' or 'https://example.com/').
                  If omitted, uses configured default_site.
        start_date: Start date in YYYY-MM-DD format (inclusive).
        end_date: End date in YYYY-MM-DD format (inclusive). Defaults to 3 days ago for 'final' data.
        days: Number of days to look back if start_date is not provided (default: 28).
        dimensions: Dimensions to group by. Allowed: 'query', 'page', 'country', 'device', 'date', 'searchAppearance'.
        filters: Filter expressions in '<dimension> <operator> <value>' format.
                 Operators: 'contains', '!contains', '==', '!=', 'regex', '!regex'.
                 Example: ["query contains pricing", "country == usa"]
        search_type: Search type: 'web', 'image', 'video', 'news', 'discover', 'googleNews'.
        data_state: Freshness state: 'final' (finalized aggregated data) or 'all' (fresh provisional data).
        limit: Max rows returned (1-25000, default: 25).
        offset: Starting row offset for pagination (0-indexed).
        sort_by: Column to sort by: 'clicks', 'impressions', 'ctr', 'position', or dimension names.
        ascending: Whether to sort ascending instead of descending.

    Returns:
        Structured dictionary containing query metadata, row count, and rows with metrics.
    """
    resolved_site = site_url or get_config_value("default_site")
    if not resolved_site:
        raise ValueError(
            "No site URL provided and no default site configured. "
            "Pass site_url (e.g. 'sc-domain:example.com') or call list_properties first."
        )

    today = date.today()
    if not end_date:
        lag_days = 0 if data_state == "all" else 3
        calc_end = today - timedelta(days=lag_days)
        end_date_str = calc_end.strftime("%Y-%m-%d")
    else:
        end_date_str = end_date

    if not start_date:
        end_dt = date.fromisoformat(end_date_str)
        calc_start = end_dt - timedelta(days=days)
        start_date_str = calc_start.strftime("%Y-%m-%d")
    else:
        start_date_str = start_date

    # Normalise dimensions
    flat_dims: List[str] = []
    if dimensions:
        for dim_arg in dimensions:
            for d in dim_arg.split(","):
                d_clean = d.strip()
                if d_clean:
                    if d_clean.lower() in ("searchappearance", "search_appearance"):
                        flat_dims.append("searchAppearance")
                    else:
                        flat_dims.append(d_clean.lower())
    if not flat_dims:
        flat_dims = ["query"]

    # Parse filters
    filter_groups = build_dimension_filter_groups(filters) if filters else None

    client = SearchConsoleClient()
    response = client.query_search_analytics(
        site_url=resolved_site,
        start_date=start_date_str,
        end_date=end_date_str,
        dimensions=flat_dims,
        dimension_filter_groups=filter_groups,
        search_type=search_type,
        data_state=data_state,
        row_limit=limit,
        start_row=offset,
    )

    raw_rows = response.get("rows", [])
    sorted_data = sort_rows(
        raw_rows,
        sort_by=sort_by,
        descending=not ascending,
        dimensions=flat_dims,
    )

    # Format rows nicely with mapped dimension names
    formatted_rows = []
    for r in sorted_data:
        keys = r.get("keys", [])
        entry: Dict[str, Any] = {}
        for i, dim in enumerate(flat_dims):
            if i < len(keys):
                entry[dim] = keys[i]
        entry["clicks"] = int(r.get("clicks", 0))
        entry["impressions"] = int(r.get("impressions", 0))
        entry["ctr"] = round(float(r.get("ctr", 0.0)), 4)
        entry["position"] = round(float(r.get("position", 0.0)), 1)
        formatted_rows.append(entry)

    return {
        "metadata": {
            "site": resolved_site,
            "startDate": start_date_str,
            "endDate": end_date_str,
            "searchType": search_type,
            "dimensions": flat_dims,
            "dataState": data_state,
        },
        "rowCount": len(formatted_rows),
        "rows": formatted_rows,
    }


@mcp_server.tool()
def inspect_url(url: str, site_url: Optional[str] = None) -> Dict[str, Any]:
    """Inspect Google Search index coverage status, verdict, and crawl details for a specific URL.

    Args:
        url: Full URL of the page to inspect (e.g. 'https://example.com/blog/article').
        site_url: Property URL containing the URL. If omitted, uses default_site.

    Returns:
        Dictionary containing verdict, coverage state, indexing state, robots.txt state,
        last crawl time, and canonical URLs.
    """
    resolved_site = site_url or get_config_value("default_site")
    if not resolved_site:
        raise ValueError("No site URL provided. Pass site_url or set default site.")

    client = SearchConsoleClient()
    result = client.inspect_url(site_url=resolved_site, inspection_url=url)
    
    idx_status = result.get("indexStatusResult", {})
    return {
        "url": url,
        "siteUrl": resolved_site,
        "verdict": idx_status.get("verdict", "UNKNOWN"),
        "coverageState": idx_status.get("coverageState", "Unknown"),
        "indexingState": idx_status.get("indexingState", "Unknown"),
        "robotsTxtState": idx_status.get("robotsTxtState", "Unknown"),
        "lastCrawlTime": idx_status.get("lastCrawlTime", "Never"),
        "userCanonical": idx_status.get("userCanonical", None),
        "googleCanonical": idx_status.get("googleCanonical", None),
    }


@mcp_server.tool()
def list_sitemaps(site_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """List submitted sitemaps, submission/download timestamps, and error/warning counts for a site.

    Args:
        site_url: Property URL. If omitted, uses default_site.

    Returns:
        List of sitemaps with path, lastSubmitted, lastDownloaded, warnings, and errors.
    """
    resolved_site = site_url or get_config_value("default_site")
    if not resolved_site:
        raise ValueError("No site URL provided. Pass site_url or set default site.")

    client = SearchConsoleClient()
    return client.list_sitemaps(resolved_site)


def run_mcp_server(
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Run the MCP server with the specified transport."""
    if transport == "stdio":
        mcp_server.run(transport="stdio")
    elif transport in ("sse", "streamable-http"):
        mcp_server.run(transport=transport, host=host, port=port)
    else:
        raise ValueError(f"Unknown transport '{transport}'. Choose 'stdio', 'sse', or 'streamable-http'.")
