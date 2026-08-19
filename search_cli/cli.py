"""Main CLI interface for search-cli."""

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
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
from search_cli.filters import FilterParseError, build_dimension_filter_groups
from search_cli.formatter import (
    format_csv,
    format_json,
    format_table,
    sort_rows,
)

app = typer.Typer(
    name="search-cli",
    help="CLI tool for querying Google Search Console Search Analytics API.",
    no_args_is_help=True,
    add_completion=False,
)

auth_app = typer.Typer(help="Manage Google Search Console authentication.")
sites_app = typer.Typer(help="Manage and view Search Console properties.")
config_app = typer.Typer(help="Manage CLI configuration and defaults.")
sitemaps_app = typer.Typer(help="Manage and view sitemaps.")

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
        None, "--version", "-v", help="Show the version and exit.", callback=version_callback, is_eager=True
    ),
):
    """search-cli: Google Search Console Search Analytics in your terminal."""
    pass


# ==============================================================================
# Auth Commands
# ==============================================================================

@auth_app.command("login")
def auth_login(
    credentials: Optional[Path] = typer.Option(
        None,
        "--credentials",
        "-c",
        help="Path to Google Cloud OAuth client_secrets.json file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    port: int = typer.Option(
        0,
        "--port",
        "-p",
        help="Local server port for OAuth redirect callback (0 selects free port).",
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Do not automatically open a web browser.",
    ),
):
    """Authenticate via OAuth 2.0 user flow in your browser."""
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
        help="Path to Google Cloud Service Account JSON key file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
):
    """Configure a Google Cloud Service Account key for authentication."""
    try:
        set_service_account(key)
        console.print(f"[bold green]✓ Configured service account key:[/bold green] {key.resolve()}")
    except Exception as e:
        err_console.print(f"[bold red]Failed to configure service account:[/bold red] {e}")
        raise typer.Exit(1)


@auth_app.command("status")
def auth_status():
    """Show current authentication status."""
    status = get_auth_status()
    if not status.get("authenticated"):
        console.print(
            Panel(
                "[bold yellow]Not authenticated[/bold yellow]\n\n"
                "Run [bold cyan]search-cli auth login[/bold cyan] or [bold cyan]search-cli auth service-account[/bold cyan]",
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
    """Clear stored tokens and reset authentication settings."""
    auth_logout()
    console.print("[green]✓ Successfully logged out and cleared credentials.[/green]")


# ==============================================================================
# Sites Commands
# ==============================================================================

@sites_app.command("list")
def sites_list(
    service_account: Optional[str] = typer.Option(None, "--service-account", help="Path to service account file"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, csv"),
):
    """List all verified Search Console properties for the authenticated account."""
    try:
        client = SearchConsoleClient(service_account_file=service_account)
        sites = client.list_sites()

        if not sites:
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
    site_url: str = typer.Argument(..., help="Site URL to set as default (e.g. sc-domain:example.com or https://example.com)"),
):
    """Set the default Search Console property URL for queries."""
    set_config_value("default_site", site_url)
    console.print(f"[green]✓ Default site set to:[/green] [bold]{site_url}[/bold]")


# ==============================================================================
# Config Commands
# ==============================================================================

@config_app.command("list")
def config_list():
    """List current configuration values."""
    cfg = load_config()
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
def config_get(key: str = typer.Argument(..., help="Config key to retrieve")):
    """Get a configuration value."""
    val = get_config_value(key)
    if val is None:
        console.print(f"[yellow]Key '{key}' is not set.[/yellow]")
    else:
        console.print(f"{val}")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a configuration value."""
    set_config_value(key, value)
    console.print(f"[green]✓ Set '{key}' = '{value}'[/green]")


# ==============================================================================
# Query Command
# ==============================================================================

@app.command("query")
def query_command(
    site: Optional[str] = typer.Option(
        None,
        "--site",
        "-s",
        help="Site URL or property (e.g. 'sc-domain:example.com' or 'https://example.com'). Defaults to configured default_site.",
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Start date in YYYY-MM-DD format.",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end-date",
        help="End date in YYYY-MM-DD format.",
    ),
    days: int = typer.Option(
        28,
        "--days",
        help="Number of days to query (used if start-date is not specified).",
    ),
    dimensions: List[str] = typer.Option(
        ["query"],
        "--dimension",
        "-d",
        help="Dimensions to group by (e.g. query, page, country, device, date, searchAppearance). Can be repeated or comma-separated.",
    ),
    filters: Optional[List[str]] = typer.Option(
        None,
        "--filter",
        "-f",
        help="Dimension filter expression (e.g. 'query contains shoes', 'country == usa', 'page !contains /tag/'). Can be repeated.",
    ),
    search_type: str = typer.Option(
        "web",
        "--search-type",
        "-t",
        help="Search type: web, image, video, news, discover, googleNews.",
    ),
    data_state: str = typer.Option(
        "final",
        "--data-state",
        help="Data freshness: 'final' (stable aggregated) or 'all' (includes fresh/provisional data).",
    ),
    aggregation_type: str = typer.Option(
        "auto",
        "--aggregation-type",
        help="Aggregation type: 'auto', 'byPage', 'byProperty'.",
    ),
    limit: int = typer.Option(
        25,
        "--limit",
        "-l",
        help="Maximum rows to return (1-25000).",
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        help="Offset start row index.",
    ),
    sort_by: str = typer.Option(
        "clicks",
        "--sort-by",
        help="Column to sort by (clicks, impressions, ctr, position, or dimension name).",
    ),
    ascending: bool = typer.Option(
        False,
        "--asc",
        help="Sort ascending instead of descending.",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        help="Output format: table, json, csv, tsv.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save output to the specified file path.",
    ),
    service_account: Optional[str] = typer.Option(
        None,
        "--service-account",
        help="Optional path to service account JSON key file.",
    ),
):
    """Query Search Console search analytics performance metrics."""
    # 1. Resolve site
    site_url = site or get_config_value("default_site")
    if not site_url:
        err_console.print(
            "[bold red]Error:[/bold red] No site URL specified!\n"
            "Provide --site <URL> or set a default via: search-cli sites default <URL>"
        )
        raise typer.Exit(1)

    # 2. Resolve dates
    today = date.today()
    if not end_date:
        # GSC final data has ~3 days delay; if data_state == all, end date is yesterday or today
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
                # Handle camelCase for searchAppearance
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
            # If output file is given with table format, write text
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
    service_account: Optional[str] = typer.Option(None, "--service-account", help="Path to service account file"),
):
    """List submitted sitemaps and their crawl status for a site."""
    site_url = site or get_config_value("default_site")
    if not site_url:
        err_console.print("[bold red]Error:[/bold red] Please specify --site <URL>")
        raise typer.Exit(1)

    try:
        client = SearchConsoleClient(service_account_file=service_account)
        sitemaps = client.list_sitemaps(site_url)

        if not sitemaps:
            console.print(f"[yellow]No sitemaps found for {site_url}.[/yellow]")
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
    url: str = typer.Argument(..., help="Specific URL to inspect"),
    site: Optional[str] = typer.Option(
        None,
        "--site",
        "-s",
        help="Site/Property URL containing the inspected URL (defaults to configured default_site).",
    ),
    service_account: Optional[str] = typer.Option(None, "--service-account", help="Path to service account file"),
):
    """Inspect index status and crawl state of a URL."""
    site_url = site or get_config_value("default_site")
    if not site_url:
        err_console.print("[bold red]Error:[/bold red] Please specify --site <URL>")
        raise typer.Exit(1)

    try:
        client = SearchConsoleClient(service_account_file=service_account)
        with console.status(f"[cyan]Inspecting {url}...[/cyan]"):
            result = client.inspect_url(site_url=site_url, inspection_url=url)

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
