import json
from search_cli.formatter import (
    format_csv,
    format_json,
    format_table,
    sort_rows,
)

SAMPLE_ROWS = [
    {
        "keys": ["python tutorial", "https://example.com/python"],
        "clicks": 150,
        "impressions": 2000,
        "ctr": 0.075,
        "position": 3.2,
    },
    {
        "keys": ["google api guide", "https://example.com/api"],
        "clicks": 500,
        "impressions": 5000,
        "ctr": 0.10,
        "position": 1.5,
    },
]


def test_sort_rows():
    sorted_clicks_desc = sort_rows(SAMPLE_ROWS, sort_by="clicks", descending=True)
    assert sorted_clicks_desc[0]["clicks"] == 500
    assert sorted_clicks_desc[1]["clicks"] == 150

    sorted_clicks_asc = sort_rows(SAMPLE_ROWS, sort_by="clicks", descending=False)
    assert sorted_clicks_asc[0]["clicks"] == 150

    sorted_pos = sort_rows(SAMPLE_ROWS, sort_by="position", descending=False)
    assert sorted_pos[0]["position"] == 1.5


def test_format_csv():
    csv_out = format_csv(SAMPLE_ROWS, dimensions=["query", "page"])
    lines = csv_out.strip().splitlines()
    assert len(lines) == 3
    assert lines[0] == "Query,Page,Clicks,Impressions,CTR,Position"
    assert "python tutorial,https://example.com/python,150,2000,0.0750,3.20" in lines[1]


def test_format_json():
    json_out = format_json(SAMPLE_ROWS, dimensions=["query", "page"], pretty=False)
    data = json.loads(json_out)
    assert data["rowCount"] == 2
    assert len(data["rows"]) == 2
    assert data["rows"][0]["query"] == "python tutorial"
    assert data["rows"][0]["clicks"] == 150


def test_format_table():
    table = format_table(SAMPLE_ROWS, dimensions=["query", "page"], title="Test Table")
    assert table.title == "Test Table"
    assert len(table.columns) == 6  # query, page, clicks, impressions, ctr, position
