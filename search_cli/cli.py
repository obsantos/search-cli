"""Main CLI interface for search-cli."""

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from search_cli import __version__
from search_cli.auth import (
    AuthError,
    get_auth_status,
    login_oauth,
    logout as auth_logout,
    set_service_account,
)
from search_cli.client import SearchConsoleClient
from search_cli.config import (
    get_config_value,
    load_config,
    save_config,
    set_config_value,
)
from search_cli.docs import (
    CLI_AGENT_SCHEMA,
    MAIN_HELP_EPILOG,
    QUERY_HELP_EPILOG,
)
from search_cli.filters import FilterParseError, build_dimension_filter_groups
from search_cli.formatter import (
    format_csv,
    format_json,
    format_table,
    sort_rows,
)

app = typer.Typer(
    name="search-cli",
    help=(
        "Search Console CLI: Query Google Search Console Search Analytics API, "
        "inspect URL indexing status, manage properties, and view sitemaps."
    ),
    epilog=MAIN_HELP_EPILOG,
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

auth_app = typer.Typer(
    help="Manage Google Search Console authentication (OAuth2 and Service Account).",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
sites_app = typer.Typer(
    help="Manage and inspect verified Search Console properties.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
config_app = typer.Typer(
    help="Manage persistent CLI configuration and defaults.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
sitemaps_app = typer.Typer(
    help="Inspect submitted sitemaps and crawl error reports.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(auth_app, name="auth")
app.add_typer(sites_app, name="sites")
app.add_typer(config_app, name="config")
app.add_typer(sitemaps_app, name="sitemaps")

console = Console()
err_console = Console(stderr=True)


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]search-cli[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """search-cli: Fast, AI-agent friendly Google Search Console CLI."""
    pass


# ==============================================================================
# Agent Guide & Schema Command
# ==============================================================================

@app.command("guide")
def guide_command(
    as_json: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output full machine-readable JSON schema and specifications for AI agent tool callers.",
    ),
):
    """Display comprehensive AI Agent specification, parameter definitions, and query guide."""
    if as_json:
        console.print_json(data=CLI_AGENT_SCHEMA)
        return

    guide_md = f"""
# Search CLI - AI Agent & User Guide (v{__version__})

`search-cli` provides direct access to Google Search Console Search Analytics API.

## Recommended AI Agent Workflow
1. **Check Authentication**: `search-cli auth status`
2. **List Accessible Properties**: `search-cli sites list --format json`
3. **Set Default Property**: `search-cli sites default <siteUrl>`
4. **Execute Queries**: `search-cli query --format json [options]`

## Dimensions
* `query`: Search query entered by the user
* `page`: Full landing page URL
* `country`: 3-letter ISO-3166-1 alpha-3 country code (e.g. `usa`, `gbr`, `deu`, `fra`)
* `device`: Device category (`desktop`, `mobile`, `tablet`)
* `date`: Individual day date (`YYYY-MM-DD`)
* `searchAppearance`: Special search feature (e.g. `AMP_ARTICLE`, `REVIEW_SNIPPET`)

## Filter Syntax
Format: `<dimension> <operator> <value>`
* **Contains**: `query contains "seo"` or `page contains "/blog/"`
* **Excludes**: `query !contains internal` or `page !contains "/tag/"`
* **Exact match**: `country == usa` or `device == mobile`
* **Not equal**: `device != desktop`
* **Regex**: `query regex "^how to"` or `query !regex "brand"`

## Search Types
`web` (default), `image`, `video`, `news`, `discover`, `googleNews`

## Data Freshness
* `final` (default): Stable finalized aggregated data (~2-3 days lag)
* `all`: Includes provisional fresh data up to current day
"""
    console.print(Markdown(guide_md))


# ==============================================================================
# Auth Commands
# ==============================================================================

@auth_app.command("login")
def auth_login(
    credentials: Optional[Path] = typer.Option(
        None,
        "--credentials",
        "-c",
        help="Path to OAuth client_secrets.json file downloaded from Google Cloud Console.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    port: int = typer.Option(
        0,
        "--port",
        "-p",
        help="Local server port for OAuth callback (0 chooses random available port).",
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Do not automatically launch browser; prints authorization URL.",
    ),
):
    """Authenticate via OAuth 2.0 Authorization Code flow."""
    try:
        console.print("[cyan]Starting Google OAuth 2.0 authorization flow...[/cyan]")
        login_oauth(
            client_secrets_path=credentials,
            port=port,
            open_browser=not no_browser,
        )
        console.print("[bold green]✓ Successfully authenticated and saved token![/bold green]")
    except Exception as e:
        err_console.print(f"[bold red]Authentication failed:[/bold red] {e}")
        raise typer.Exit(1)


@auth_app.command("service-account")
def auth_service_account(
    key: Path = typer.Option(
        ...,
        "--key",
        "-k",
        help="Path to Google Cloud Service Account JSON private key file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
):
    """Configure a Google Cloud Service Account JSON key for headless execution."""
    try:
        set_service_account(key)
        console.print(f"[bold green]✓ Configured service account key:[/bold green] {key.resolve()}")
    except Exception as e:
        err_console.print(f"[bold red]Failed to configure service account:[/bold red] {e}")
        raise typer.Exit(1)


@auth_app.command("status")
def auth_status(
    as_json: bool = typer.Option(False, "--json", "-j", help="Output status as structured JSON."),
):
    """Check current authentication status and active credential details."""
    status = get_auth_status()
    if as_json:
        console.print_json(data=status)
        return

    if not status.get("authenticated"):
        console.print(
            Panel(
                "[bold yellow]Not authenticated[/bold yellow]\n\n"
                "To authenticate, run:\n"
                "  • OAuth (browser): [bold cyan]search-cli auth login --credentials client_secrets.json[/bold cyan]\n"
                "  • Service Account: [bold cyan]search-cli auth service-account --key service_account.json[/bold cyan]",
                title="Auth Status",
                border_style="yellow",
            )
        )
        return

    details_str = "\n".join(f"[bold]{k}:[/bold] {v}" for k, v in status["details"].items())
    console.print(
        Panel(
            f"[bold green]Authenticated[/bold green] (Type: [cyan]{status['type']}[/cyan])\n\n{details_str}",
            title="Auth Status",
            border_style="green",
        )
    )


@auth_app.command("logout")
def auth_logout_cmd():
    """Clear stored OAuth tokens and reset authentication settings."""
    auth_logout()
    console.print("[green]✓ Successfully logged out and cleared credentials.[/green]")


# ==============================================================================
# Sites Commands
# ==============================================================================

@sites_app.command("list")
def sites_list(
    service_account: Optional[str] = typer.Option(
        None,
        "--service-account",
        help="Optional path to service account key file.",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: 'table', 'json', or 'csv'.",
    ),
):
    """List all verified Search Console properties for the authenticated account."""
    try:
        client = SearchConsoleClient(service_account_file=service_account)
        sites = client.list_sites()

        if not sites:
            if format == "json":
                console.print_json(data=[])
            else:
                console.print("[yellow]No verified properties found for this account.[/yellow]")
            return

        default_site = get_config_value("default_site")

        if format == "json":
            console.print_json(data=sites)
        elif format == "csv":
            import csv
            out = csv.writer(sys.stdout)
            out.writerow(["Site URL", "Permission Level", "Default"])
            for s in sites:
                is_def = "yes" if s.get("siteUrl") == default_site else "no"
                out.writerow([s.get("siteUrl"), s.get("permissionLevel"), is_def])
        else:
            table = Table(title="Search Console Verified Properties", show_header=True, header_style="bold cyan")
            table.add_column("Site / Property URL", style="white")
            table.add_column("Permission Level", style="green")
            table.add_column("Default", justify="center", style="yellow")

            for s in sites:
                url = s.get("siteUrl", "")
                is_def = "★ default" if url == default_site else ""
                table.add_row(url, s.get("permissionLevel", "unknown"), is_def)

            console.print(table)
    except Exception as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@sites_app.command("default")
def sites_set_default(
    site_url: str = typer.Argument(
        ...,
        help="Site URL to set as default (e.g. 'sc-domain:example.com' or 'https://example.com/').",
    ),
):
    """Set the default Search Console property URL for all subsequent queries."""
    set_config_value("default_site", site_url)
    console.print(f"[green]✓ Default site set to:[/green] [bold]{site_url}[/bold]")


# ==============================================================================
# Config Commands
# ==============================================================================

@config_app.command("list")
def config_list(
    as_json: bool = typer.Option(False, "--json", "-j", help="Output configuration as JSON."),
):
    """List all saved configuration keys and values."""
    cfg = load_config()
    if as_json:
        console.print_json(data=cfg)
        return
    if not cfg:
        console.print("[dim]No configuration saved yet.[/dim]")
        return
    table = Table(title="Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    for k, v in sorted(cfg.items()):
        table.add_row(k, str(v))
    console.print(table)


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key to retrieve (e.g. 'default_site')"),
):
    """Get the value of a specific configuration key."""
    val = get_config_value(key)
    if val is None:
        console.print(f"[yellow]Key '{key}' is not set.[/yellow]")
    else:
        console.print(f"{val}")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key to set"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a persistent configuration key-value pair."""
    set_config_value(key, value)
    console.print(f"[green]✓ Set '{key}' = '{value}'[/green]")


# ==============================================================================
# Query Command
# ==============================================================================

@app.command(
    "query",
    help="Query Search Console search performance metrics (clicks, impressions, CTR, average position).",
    epilog=QUERY_HELP_EPILOG,
)
def query_command(
    site: Optional[str] = typer.Option(
        None,
        "--site",
        "-s",
        help=(
            "Site URL or property (e.g. 'sc-domain:example.com' or 'https://example.com/'). "
            "If omitted, uses the configured default_site."
        ),
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Start date in YYYY-MM-DD format (inclusive).",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end-date",
        help="End date in YYYY-MM-DD format (inclusive). Defaults to 3 days ago (for 'final') or today (for 'all').",
    ),
    days: int = typer.Option(
        28,
        "--days",
        help="Number of days to query if --start-date is not specified.",
    ),
    dimensions: List[str] = typer.Option(
        ["query"],
        "--dimension",
        "-d",
        help=(
            "Dimensions to group by: 'query', 'page', 'country', 'device', 'date', 'searchAppearance'. "
            "Can be repeated or comma-separated."
        ),
    ),
    filters: Optional[List[str]] = typer.Option(
        None,
        "--filter",
        "-f",
        help=(
            "Dimension filter expression: '<dimension> <operator> <value>'. "
            "Operators: contains, !contains, ==, !=, regex, !regex. Can be repeated."
        ),
    ),
    search_type: str = typer.Option(
        "web",
        "--search-type",
        "-t",
        help="Search type: 'web', 'image', 'video', 'news', 'discover', 'googleNews'.",
    ),
    data_state: str = typer.Option(
        "final",
        "--data-state",
        help="Data freshness: 'final' (finalized aggregated data) or 'all' (includes fresh provisional data).",
    ),
    aggregation_type: str = typer.Option(
        "auto",
        "--aggregation-type",
        help="Aggregation method: 'auto', 'byPage', 'byProperty'.",
    ),
    limit: int = typer.Option(
        25,
        "--limit",
        "-l",
        help="Maximum rows to return (integer between 1 and 25000).",
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        help="Starting row offset index for pagination (0-indexed).",
    ),
    sort_by: str = typer.Option(
        "clicks",
        "--sort-by",
        help="Column to sort by: 'clicks', 'impressions', 'ctr', 'position', or dimension names.",
    ),
    ascending: bool = typer.Option(
        False,
        "--asc",
        help="Sort in ascending order instead of descending.",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        help="Output format: 'table', 'json', 'csv', 'tsv'.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="File path to save the output results directly.",
    ),
    service_account: Optional[str] = typer.Option(
        None,
        "--service-account",
        help="Optional path to service account JSON key file override.",
    ),
):
    """Execute a Search Analytics query with rich filtering, dimensions, and formatting."""
    # 1. Resolve site
    site_url = site or get_config_value("default_site")
    if not site_url:
        err_console.print(
            "[bold red]Error: No site URL specified![/bold red]\n"
            "• Option 1: Provide [bold cyan]--site <URL>[/bold cyan] (e.g. --site sc-domain:example.com)\n"
            "• Option 2: Set a default site via [bold cyan]search-cli sites default <URL>[/bold cyan]\n"
            "• Option 3: List verified sites via [bold cyan]search-cli sites list[/bold cyan]"
        )
        raise typer.Exit(1)

    # 2. Resolve dates
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

    # 3. Parse dimensions
    flat_dims: List[str] = []
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

    # 4. Parse filters
    try:
        filter_groups = build_dimension_filter_groups(filters)
    except FilterParseError as e:
        err_console.print(f"[bold red]Filter Error:[/bold red] {e}")
        err_console.print(
            "[yellow]Hint for Agent:[/yellow] Filter format is '<dimension> <operator> <value>'.\n"
            "Allowed dimensions: query, page, country, device, searchAppearance\n"
            "Allowed operators: contains, !contains, ==, !=, regex, !regex\n"
            "Example: -f \"query contains pricing\" -f \"country == usa\""
        )
        raise typer.Exit(1)

    # 5. Execute API Query
    try:
        client = SearchConsoleClient(service_account_file=service_account)
        with console.status(f"[cyan]Querying Search Console for [bold]{site_url}[/bold] ({start_date_str} to {end_date_str})...[/cyan]"):
            response = client.query_search_analytics(
                site_url=site_url,
                start_date=start_date_str,
                end_date=end_date_str,
                dimensions=flat_dims,
                dimension_filter_groups=filter_groups,
                search_type=search_type,
                aggregation_type=aggregation_type,
                data_state=data_state,
                row_limit=limit,
                start_row=offset,
            )
    except Exception as e:
        err_console.print(f"[bold red]API Error:[/bold red] {e}")
        raise typer.Exit(1)

    raw_rows = response.get("rows", [])
    if not raw_rows:
        if format == "json":
            empty_payload = {
                "metadata": {
                    "site": site_url,
                    "startDate": start_date_str,
                    "endDate": end_date_str,
                    "searchType": search_type,
                    "dimensions": flat_dims,
                },
                "rowCount": 0,
                "rows": [],
            }
            console.print_json(data=empty_payload)
        else:
            console.print(f"[yellow]No search performance data returned for {site_url} ({start_date_str} to {end_date_str}).[/yellow]")
        return

    # 6. Sort rows
    rows = sort_rows(
        raw_rows,
        sort_by=sort_by,
        descending=not ascending,
        dimensions=flat_dims,
    )

    # 7. Format output
    metadata = {
        "site": site_url,
        "startDate": start_date_str,
        "endDate": end_date_str,
        "searchType": search_type,
        "dimensions": flat_dims,
        "responseAggregationType": response.get("responseAggregationType", aggregation_type),
    }

    title = f"Search Performance: {site_url} ({start_date_str} to {end_date_str})"

    if format == "json":
        output_str = format_json(rows, dimensions=flat_dims, response_metadata=metadata)
        if output:
            output.write_text(output_str, encoding="utf-8")
            console.print(f"[green]✓ Exported JSON to {output}[/green]")
        else:
            console.print_json(output_str)
    elif format == "csv":
        output_str = format_csv(rows, dimensions=flat_dims, delimiter=",")
        if output:
            output.write_text(output_str, encoding="utf-8")
            console.print(f"[green]✓ Exported CSV to {output}[/green]")
        else:
            sys.stdout.write(output_str)
    elif format == "tsv":
        output_str = format_csv(rows, dimensions=flat_dims, delimiter="\t")
        if output:
            output.write_text(output_str, encoding="utf-8")
            console.print(f"[green]✓ Exported TSV to {output}[/green]")
        else:
            sys.stdout.write(output_str)
    else:  # Table
        table = format_table(rows, dimensions=flat_dims, title=title)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                file_console = Console(file=f, force_terminal=False)
                file_console.print(table)
            console.print(f"[green]✓ Exported table to {output}[/green]")
        else:
            console.print(table)


# ==============================================================================
# Sitemaps Commands
# ==============================================================================

@sitemaps_app.command("list")
def sitemaps_list(
    site: Optional[str] = typer.Option(
        None,
        "--site",
        "-s",
        help="Site URL or property (defaults to configured default_site).",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: 'table' or 'json'.",
    ),
    service_account: Optional[str] = typer.Option(
        None,
        "--service-account",
        help="Optional path to service account file override.",
    ),
):
    """List submitted sitemaps and their crawl status for a site."""
    site_url = site or get_config_value("default_site")
    if not site_url:
        err_console.print("[bold red]Error: Please specify --site <URL>[/bold red]")
        raise typer.Exit(1)

    try:
        client = SearchConsoleClient(service_account_file=service_account)
        sitemaps = client.list_sitemaps(site_url)

        if not sitemaps:
            if format == "json":
                console.print_json(data=[])
            else:
                console.print(f"[yellow]No sitemaps found for {site_url}.[/yellow]")
            return

        if format == "json":
            console.print_json(data=sitemaps)
            return

        table = Table(title=f"Sitemaps for {site_url}", show_header=True, header_style="bold cyan")
        table.add_column("Sitemap Path", style="white")
        table.add_column("Last Submitted", style="blue")
        table.add_column("Last Downloaded", style="magenta")
        table.add_column("Type", style="yellow")
        table.add_column("Warnings / Errors", style="red")

        for sm in sitemaps:
            path = sm.get("path", "")
            submitted = sm.get("lastSubmitted", "-")
            downloaded = sm.get("lastDownloaded", "-")
            sm_type = sm.get("type", "sitemap")
            errors = f"W: {sm.get('warnings', 0)} / E: {sm.get('errors', 0)}"
            table.add_row(path, submitted, downloaded, sm_type, errors)

        console.print(table)
    except Exception as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


# ==============================================================================
# URL Inspection Command
# ==============================================================================

@app.command("inspect")
def inspect_url(
    url: str = typer.Argument(..., help="Specific page URL to inspect index status for"),
    site: Optional[str] = typer.Option(
        None,
        "--site",
        "-s",
        help="Site/Property URL containing the inspected URL (defaults to configured default_site).",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: 'table' or 'json'.",
    ),
    service_account: Optional[str] = typer.Option(
        None,
        "--service-account",
        help="Optional path to service account file override.",
    ),
):
    """Inspect Google index status, verdict, canonical URL, and crawl state for a URL."""
    site_url = site or get_config_value("default_site")
    if not site_url:
        err_console.print("[bold red]Error: Please specify --site <URL>[/bold red]")
        raise typer.Exit(1)

    try:
        client = SearchConsoleClient(service_account_file=service_account)
        with console.status(f"[cyan]Inspecting {url}...[/cyan]"):
            result = client.inspect_url(site_url=site_url, inspection_url=url)

        if format == "json":
            console.print_json(data=result)
            return

        idx_status = result.get("indexStatusResult", {})
        verdict = idx_status.get("verdict", "UNKNOWN")
        coverage_state = idx_status.get("coverageState", "Unknown")
        robots_txt = idx_status.get("robotsTxtState", "Unknown")
        indexing_state = idx_status.get("indexingState", "Unknown")
        last_crawl = idx_status.get("lastCrawlTime", "Never")
        user_canonical = idx_status.get("userCanonical", "-")
        google_canonical = idx_status.get("googleCanonical", "-")

        table = Table(title=f"URL Inspection: {url}", show_header=True, header_style="bold cyan")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Verdict", f"[bold green]{verdict}[/bold green]" if verdict == "PASS" else f"[bold red]{verdict}[/bold red]")
        table.add_row("Coverage State", coverage_state)
        table.add_row("Robots.txt State", robots_txt)
        table.add_row("Indexing State", indexing_state)
        table.add_row("Last Crawl Time", last_crawl)
        table.add_row("User Canonical", user_canonical)
        table.add_row("Google Canonical", google_canonical)

        console.print(table)
    except Exception as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
