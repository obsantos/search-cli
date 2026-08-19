"""Google Search Console API client wrapper."""

from typing import Any, Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from search_cli.auth import get_credentials


class SearchConsoleClient:
    """Client for Google Search Console Search Analytics API."""

    def __init__(
        self,
        service_account_file: Optional[str] = None,
        client_secrets_file: Optional[str] = None,
    ):
        creds = get_credentials(
            service_account_file=service_account_file,
            client_secrets_file=client_secrets_file,
        )
        self.service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    def list_sites(self) -> List[Dict[str, Any]]:
        """List all verified sites accessible to the authenticated account."""
        try:
            response = self.service.sites().list().execute()
            return response.get("siteEntry", [])
        except HttpError as e:
            raise RuntimeError(f"Failed to list sites: {e}")

    def query_search_analytics(
        self,
        site_url: str,
        start_date: str,
        end_date: str,
        dimensions: Optional[List[str]] = None,
        dimension_filter_groups: Optional[List[Dict[str, Any]]] = None,
        search_type: str = "web",
        aggregation_type: str = "auto",
        data_state: str = "final",
        row_limit: int = 1000,
        start_row: int = 0,
    ) -> Dict[str, Any]:
        """Execute a search analytics query."""
        body: Dict[str, Any] = {
            "startDate": start_date,
            "endDate": end_date,
            "rowLimit": min(max(1, row_limit), 25000),
            "startRow": max(0, start_row),
            "type": search_type,
            "aggregationType": aggregation_type,
            "dataState": data_state,
        }

        if dimensions:
            body["dimensions"] = dimensions

        if dimension_filter_groups:
            body["dimensionFilterGroups"] = dimension_filter_groups

        try:
            response = (
                self.service.searchanalytics()
                .query(siteUrl=site_url, body=body)
                .execute()
            )
            return response
        except HttpError as e:
            raise RuntimeError(f"Search Console API error for '{site_url}': {e}")

    def list_sitemaps(self, site_url: str) -> List[Dict[str, Any]]:
        """List all sitemaps submitted for the site."""
        try:
            response = self.service.sitemaps().list(siteUrl=site_url).execute()
            return response.get("sitemap", [])
        except HttpError as e:
            raise RuntimeError(f"Failed to list sitemaps: {e}")

    def inspect_url(self, site_url: str, inspection_url: str) -> Dict[str, Any]:
        """Inspect a URL using the Search Console URL Inspection API."""
        try:
            body = {
                "siteUrl": site_url,
                "inspectionUrl": inspection_url,
            }
            response = self.service.urlInspection().index().inspect(body=body).execute()
            return response.get("inspectionResult", {})
        except HttpError as e:
            raise RuntimeError(f"URL Inspection API error: {e}")
