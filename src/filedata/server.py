"""FileData MCP Server — exposes CSV/Excel data as MCP tools via FastMCP."""

import json
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from .config import get_host, get_port, get_sources, get_transport
from .registry import get_registry, get_table, load_sources


# ── Lifespan: load configured sources on startup ─────────────────────────────

@asynccontextmanager
async def lifespan(server: FastMCP):
    sources = get_sources()
    if sources:
        load_sources(sources)
    yield


# ── Server instance ───────────────────────────────────────────────────────────

mcp = FastMCP("FileData", lifespan=lifespan)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_tables() -> list[str]:
    """Get a sorted list of all available table names.

    - CSV files contribute one table named after the file (without extension).
    - Excel files contribute one table per sheet, named after the sheet tab.

    Returns a list of table name strings.
    """
    return sorted(get_registry().keys())


@mcp.tool()
def get_columns(table_name: str) -> list[dict[str, str]]:
    """Get the column names and data types for a specific table.

    Args:
        table_name: Name of the table to inspect.

    Returns a list of dicts, each with:
        - ``name``: column name
        - ``dtype``: pandas dtype string (e.g. ``int64``, ``object``, ``float64``)
    """
    df = get_table(table_name)
    return [
        {"name": col, "dtype": str(df[col].dtype)}
        for col in df.columns
    ]


@mcp.tool()
def query_table(
    table_name: str,
    limit: int = 100,
    offset: int = 0,
) -> str:
    """Query rows from a table, returned as a JSON array of record objects.

    Args:
        table_name: Name of the table to query.
        limit: Maximum rows to return (default 100, hard cap 1000).
        offset: Number of rows to skip before returning results (default 0).

    Returns a JSON string — an array where each element is one row as an object.
    """
    limit = min(max(limit, 1), 1000)
    df = get_table(table_name)
    subset = df.iloc[offset: offset + limit]
    return subset.to_json(orient="records", date_format="iso", default_handler=str)


@mcp.tool()
def get_table_info(table_name: str) -> dict[str, Any]:
    """Get summary information about a table.

    Args:
        table_name: Name of the table to describe.

    Returns a dict with:
        - ``table_name``: the table name
        - ``row_count``: total number of rows
        - ``column_count``: number of columns
        - ``columns``: list of column descriptors (name, dtype, null_count, null_pct)
        - ``sample``: up to 5 rows as a list of record dicts
    """
    df = get_table(table_name)

    columns_info = [
        {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isna().sum()),
            "null_pct": round(float(df[col].isna().mean()) * 100, 1),
        }
        for col in df.columns
    ]

    # Convert sample to plain Python so it's always JSON-serialisable
    sample = json.loads(
        df.head(5).to_json(orient="records", date_format="iso", default_handler=str)
    )

    return {
        "table_name": table_name,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": columns_info,
        "sample": sample,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def run() -> None:
    """Start the MCP server using the configured transport."""
    transport = get_transport()
    if transport == "sse":
        mcp.run(transport="sse", host=get_host(), port=get_port())
    else:
        mcp.run()


if __name__ == "__main__":
    run()
