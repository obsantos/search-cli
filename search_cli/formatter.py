"""Output formatting for search analytics query results."""

import csv
import io
import json
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table


def sort_rows(
    rows: List[Dict[str, Any]],
    sort_by: Optional[str] = None,
    descending: bool = True,
    dimensions: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Sort query result rows by metric or dimension."""
    if not sort_by:
        return rows

    sort_col = sort_by.lower()
    dims = dimensions or []

    def get_sort_key(row: Dict[str, Any]):
        if sort_col in ("clicks", "impressions", "ctr", "position"):
            return row.get(sort_col, 0)
        # Dimension key lookup
        keys = row.get("keys", [])
        if sort_col in dims:
            idx = dims.index(sort_col)
            if idx < len(keys):
                return keys[idx]
        return 0

    return sorted(rows, key=get_sort_key, reverse=descending)


def format_table(
    rows: List[Dict[str, Any]],
    dimensions: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> Table:
    """Create a Rich Table displaying Search Analytics rows."""
    dims = dimensions or ["Item"]

    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        show_lines=False,
        show_footer=True,
    )

    # Add dimension columns
    for dim in dims:
        table.add_column(dim.capitalize(), style="white", overflow="fold")

    # Add metric columns
    table.add_column("Clicks", justify="right", style="green", footer_style="bold green")
    table.add_column("Impressions", justify="right", style="blue", footer_style="bold blue")
    table.add_column("CTR", justify="right", style="magenta", footer_style="bold magenta")
    table.add_column("Avg Position", justify="right", style="yellow", footer_style="bold yellow")

    total_clicks = 0
    total_impressions = 0
    weighted_pos_sum = 0.0

    for row in rows:
        keys = row.get("keys", [])
        clicks = int(row.get("clicks", 0))
        impressions = int(row.get("impressions", 0))
        ctr = float(row.get("ctr", 0.0))
        position = float(row.get("position", 0.0))

        total_clicks += clicks
        total_impressions += impressions
        weighted_pos_sum += position * impressions

        # Prepare dimension values
        dim_values = []
        for i in range(len(dims)):
            if i < len(keys):
                dim_values.append(str(keys[i]))
            else:
                dim_values.append("-")

        table.add_row(
            *dim_values,
            f"{clicks:,}",
            f"{impressions:,}",
            f"{ctr * 100:.2f}%",
            f"{position:.1f}",
        )

    # Compute aggregate footers
    total_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
    avg_pos = (weighted_pos_sum / total_impressions) if total_impressions > 0 else 0.0

    # Set footer values
    if len(dims) > 0:
        table.columns[0].footer = f"Total ({len(rows):,} rows)"
        for i in range(1, len(dims)):
            table.columns[i].footer = ""

    click_idx = len(dims)
    table.columns[click_idx].footer = f"{total_clicks:,}"
    table.columns[click_idx + 1].footer = f"{total_impressions:,}"
    table.columns[click_idx + 2].footer = f"{total_ctr:.2f}%"
    table.columns[click_idx + 3].footer = f"{avg_pos:.1f}"

    return table


def format_csv(
    rows: List[Dict[str, Any]],
    dimensions: Optional[List[str]] = None,
    delimiter: str = ",",
) -> str:
    """Format rows as CSV or TSV."""
    dims = dimensions or ["Item"]
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimiter)

    # Header
    headers = [d.capitalize() for d in dims] + ["Clicks", "Impressions", "CTR", "Position"]
    writer.writerow(headers)

    for row in rows:
        keys = row.get("keys", [])
        clicks = int(row.get("clicks", 0))
        impressions = int(row.get("impressions", 0))
        ctr = float(row.get("ctr", 0.0))
        position = float(row.get("position", 0.0))

        dim_values = []
        for i in range(len(dims)):
            if i < len(keys):
                dim_values.append(str(keys[i]))
            else:
                dim_values.append("")

        writer.writerow(dim_values + [clicks, impressions, f"{ctr:.4f}", f"{position:.2f}"])

    return output.getvalue()


def format_json(
    rows: List[Dict[str, Any]],
    dimensions: Optional[List[str]] = None,
    response_metadata: Optional[Dict[str, Any]] = None,
    pretty: bool = True,
) -> str:
    """Format rows and metadata as JSON."""
    dims = dimensions or []
    formatted_data = []

    for row in rows:
        keys = row.get("keys", [])
        entry: Dict[str, Any] = {}
        for i, dim in enumerate(dims):
            if i < len(keys):
                entry[dim] = keys[i]
        
        entry["clicks"] = row.get("clicks", 0)
        entry["impressions"] = row.get("impressions", 0)
        entry["ctr"] = row.get("ctr", 0.0)
        entry["position"] = row.get("position", 0.0)
        formatted_data.append(entry)

    payload = {
        "metadata": response_metadata or {},
        "rowCount": len(formatted_data),
        "rows": formatted_data,
    }

    return json.dumps(payload, indent=2 if pretty else None)
