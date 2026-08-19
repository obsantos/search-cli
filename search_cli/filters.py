"""Filter parser for Google Search Console API dimension filters."""

import re
import shlex
from typing import Any, Dict, List, Optional, Tuple

VALID_DIMENSIONS = {
    "query": "query",
    "page": "page",
    "country": "country",
    "device": "device",
    "searchappearance": "searchAppearance",
    "search_appearance": "searchAppearance",
}

OPERATOR_MAP = {
    "contains": "contains",
    "include": "contains",
    "has": "contains",
    "in": "contains",
    "!contains": "notContains",
    "not_contains": "notContains",
    "notcontains": "notContains",
    "exclude": "notContains",
    "doesnotcontain": "notContains",
    "==": "equals",
    "=": "equals",
    "equals": "equals",
    "equal": "equals",
    "eq": "equals",
    "!=": "notEquals",
    "not_equals": "notEquals",
    "notequals": "notEquals",
    "ne": "notEquals",
    "regex": "includingRegex",
    "~": "includingRegex",
    "matches": "includingRegex",
    "includingregex": "includingRegex",
    "including_regex": "includingRegex",
    "!regex": "excludingRegex",
    "!~": "excludingRegex",
    "not_regex": "excludingRegex",
    "notregex": "excludingRegex",
    "excludingregex": "excludingRegex",
    "excluding_regex": "excludingRegex",
}


class FilterParseError(ValueError):
    """Raised when a filter string cannot be parsed."""
    pass


def parse_single_filter(filter_str: str) -> Dict[str, str]:
    """Parse a single filter string like 'query contains shoes' or 'device == mobile'."""
    filter_str = filter_str.strip()
    if not filter_str:
        raise FilterParseError("Empty filter string provided.")

    # Try split with shlex to respect quotes
    try:
        tokens = shlex.split(filter_str)
    except ValueError as e:
        raise FilterParseError(f"Invalid filter syntax: {e}")

    if len(tokens) < 3:
        # Check if user passed something like 'country=usa' or 'query!=foo'
        # Try regex split
        match = re.match(r"^([a-zA-Z_]+)\s*(==|!=|=|~|!~)\s*(.+)$", filter_str)
        if match:
            dim_raw, op_raw, val_raw = match.groups()
            tokens = [dim_raw, op_raw, val_raw.strip('"\'')]
        else:
            raise FilterParseError(
                f"Filter '{filter_str}' is invalid. Expected format: '<dimension> <operator> <value>'. "
                f"Example: 'query contains \"shoes\"' or 'country == usa'"
            )

    dim_token = tokens[0].lower()
    op_token = tokens[1].lower()
    val_token = " ".join(tokens[2:])  # Join remaining tokens in case of unquoted space

    canonical_dim = VALID_DIMENSIONS.get(dim_token)
    if not canonical_dim:
        valid_dims = ", ".join(sorted(set(VALID_DIMENSIONS.values())))
        raise FilterParseError(
            f"Invalid dimension '{tokens[0]}'. Allowed dimensions: {valid_dims}"
        )

    canonical_op = OPERATOR_MAP.get(op_token)
    if not canonical_op:
        valid_ops = "contains, !contains, equals (==), not_equals (!=), regex (~), !regex (!~)"
        raise FilterParseError(
            f"Invalid operator '{tokens[1]}'. Allowed operators: {valid_ops}"
        )

    return {
        "dimension": canonical_dim,
        "operator": canonical_op,
        "expression": val_token,
    }


def build_dimension_filter_groups(
    filter_strings: Optional[List[str]],
    group_type: str = "and",
) -> List[Dict[str, Any]]:
    """Build GSC dimensionFilterGroups structure from a list of filter strings."""
    if not filter_strings:
        return []

    filters = []
    for item in filter_strings:
        # Allow comma-separated filters or repeated arguments
        if ";" in item:
            sub_items = [s.strip() for s in item.split(";") if s.strip()]
        else:
            sub_items = [item]

        for f_str in sub_items:
            filters.append(parse_single_filter(f_str))

    if not filters:
        return []

    return [
        {
            "groupType": group_type,
            "filters": filters,
        }
    ]
