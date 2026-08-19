import pytest
from search_cli.filters import (
    FilterParseError,
    build_dimension_filter_groups,
    parse_single_filter,
)


def test_parse_simple_contains():
    res = parse_single_filter("query contains python")
    assert res == {
        "dimension": "query",
        "operator": "contains",
        "expression": "python",
    }


def test_parse_quotes_and_spaces():
    res = parse_single_filter('query contains "best python courses"')
    assert res == {
        "dimension": "query",
        "operator": "contains",
        "expression": "best python courses",
    }


def test_parse_equals_and_operators():
    res = parse_single_filter("country == usa")
    assert res == {
        "dimension": "country",
        "operator": "equals",
        "expression": "usa",
    }

    res2 = parse_single_filter("device != mobile")
    assert res2 == {
        "dimension": "device",
        "operator": "notEquals",
        "expression": "mobile",
    }

    res3 = parse_single_filter("query regex ^tutorial")
    assert res3 == {
        "dimension": "query",
        "operator": "includingRegex",
        "expression": "^tutorial",
    }

    res4 = parse_single_filter("page !contains /tags/")
    assert res4 == {
        "dimension": "page",
        "operator": "notContains",
        "expression": "/tags/",
    }


def test_dimension_aliases():
    res = parse_single_filter("search_appearance equals AMP_ARTICLE")
    assert res["dimension"] == "searchAppearance"
    assert res["operator"] == "equals"
    assert res["expression"] == "AMP_ARTICLE"


def test_invalid_dimension():
    with pytest.raises(FilterParseError, match="Invalid dimension 'clicks'"):
        parse_single_filter("clicks == 50")


def test_invalid_operator():
    with pytest.raises(FilterParseError, match="Invalid operator 'greater_than'"):
        parse_single_filter("query greater_than 50")


def test_build_dimension_filter_groups():
    filter_list = [
        "query contains api",
        "country == usa; device == desktop",
    ]
    groups = build_dimension_filter_groups(filter_list)
    assert len(groups) == 1
    assert groups[0]["groupType"] == "and"
    assert len(groups[0]["filters"]) == 3
    assert groups[0]["filters"][0]["dimension"] == "query"
    assert groups[0]["filters"][1]["dimension"] == "country"
    assert groups[0]["filters"][2]["dimension"] == "device"
