from search_cli.mcp_server import mcp_server, get_authentication_status
from unittest.mock import patch, MagicMock


def test_mcp_server_initialization():
    assert mcp_server.name == "search-console"
    assert "Google Search Console MCP Server" in mcp_server.description


def test_get_auth_status_tool():
    status = get_authentication_status()
    assert isinstance(status, dict)
    assert "authenticated" in status
    assert "type" in status


@patch("search_cli.mcp_server.SearchConsoleClient")
def test_list_properties_tool(mock_client_class):
    mock_instance = MagicMock()
    mock_instance.list_sites.return_value = [
        {"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"},
        {"siteUrl": "https://example.com/", "permissionLevel": "siteFullUser"},
    ]
    mock_client_class.return_value = mock_instance

    from search_cli.mcp_server import list_properties
    properties = list_properties()
    assert len(properties) == 2
    assert properties[0]["siteUrl"] == "sc-domain:example.com"
    assert properties[0]["permissionLevel"] == "siteOwner"


@patch("search_cli.mcp_server.SearchConsoleClient")
def test_query_search_analytics_tool(mock_client_class):
    mock_instance = MagicMock()
    mock_instance.query_search_analytics.return_value = {
        "rows": [
            {
                "keys": ["search cli", "https://example.com"],
                "clicks": 100,
                "impressions": 1000,
                "ctr": 0.10,
                "position": 2.5,
            }
        ]
    }
    mock_client_class.return_value = mock_instance

    from search_cli.mcp_server import query_search_analytics
    res = query_search_analytics(
        site_url="sc-domain:example.com",
        start_date="2026-01-01",
        end_date="2026-01-28",
        dimensions=["query", "page"],
    )

    assert res["rowCount"] == 1
    assert res["metadata"]["site"] == "sc-domain:example.com"
    assert len(res["rows"]) == 1
    assert res["rows"][0]["query"] == "search cli"
    assert res["rows"][0]["clicks"] == 100
    assert res["rows"][0]["impressions"] == 1000
    assert res["rows"][0]["ctr"] == 0.10
    assert res["rows"][0]["position"] == 2.5


@patch("search_cli.mcp_server.SearchConsoleClient")
def test_inspect_url_tool(mock_client_class):
    mock_instance = MagicMock()
    mock_instance.inspect_url.return_value = {
        "indexStatusResult": {
            "verdict": "PASS",
            "coverageState": "Submitted and indexed",
            "robotsTxtState": "ALLOWED",
            "indexingState": "INDEXING_ALLOWED",
            "lastCrawlTime": "2026-08-20T10:00:00Z",
            "userCanonical": "https://example.com/blog",
            "googleCanonical": "https://example.com/blog",
        }
    }
    mock_client_class.return_value = mock_instance

    from search_cli.mcp_server import inspect_url
    res = inspect_url(
        url="https://example.com/blog",
        site_url="sc-domain:example.com",
    )

    assert res["verdict"] == "PASS"
    assert res["coverageState"] == "Submitted and indexed"
    assert res["robotsTxtState"] == "ALLOWED"
