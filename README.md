# FileData MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes CSV and Excel files as queryable MCP tools — designed to work with OpenWebUI and other MCP clients.

## Features

- **CSV support** — each file becomes one table (named after the filename)
- **Excel support** — each sheet tab becomes its own table (named after the tab)
- **Flexible sources** — configure local file paths and/or HTTPS URLs
- **4 MCP tools** — list tables, inspect columns, query rows, get table summaries

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_tables()` | List all available table names |
| `get_columns(table_name)` | List columns + dtypes for a table |
| `query_table(table_name, limit, offset)` | Return rows as a JSON array |
| `get_table_info(table_name)` | Row count, column stats, 5-row sample |

---

## Quick Start

### 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set FILEDATA_SOURCES
```

Example `.env`:
```
FILEDATA_SOURCES=./data/sales.csv,./data/report.xlsx,https://example.com/data.csv
FILEDATA_TRANSPORT=stdio
```

### 3. Run

```bash
# stdio (default — for local MCP clients)
python -m filedata.server

# SSE / HTTP (for OpenWebUI)
FILEDATA_TRANSPORT=sse FILEDATA_PORT=8000 python -m filedata.server
```

---

## File Source Rules

| Source type | Table naming |
|-------------|-------------|
| `sales.csv` | Table name: `sales` |
| `report.xlsx` (sheet: `Q1`) | Table name: `Q1` |
| `https://host.com/data.csv` | Table name: `data` |
| `https://host.com/report.xlsx` (sheet: `Jan`) | Table name: `Jan` |

---

## OpenWebUI Setup

1. Set `FILEDATA_TRANSPORT=sse` and pick a port (e.g. `8000`)
2. Start the server: `python -m filedata.server`
3. In OpenWebUI → Settings → MCP Servers, add: `http://localhost:8000/sse`

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Supported Formats

- `.csv`
- `.xlsx` / `.xls` / `.xlsm`

## Dependencies

- [fastmcp](https://github.com/jlowin/fastmcp) — MCP server framework
- [pandas](https://pandas.pydata.org/) — file loading (CSV + Excel)
- [polars](https://pola.rs/) — available for advanced data operations
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel read/write engine
- [requests](https://requests.readthedocs.io/) — HTTPS file fetching
- [python-dotenv](https://github.com/theskumar/python-dotenv) — `.env` support

---

## Testing sse with mcptools
Make sure .env has FILEDATA_TRANSPORT=sse

In terminal window start the server
```bash
. .venv/bin/activate
python -m filedata.serve
```

In a different terminal use the client
```bash
brew tap f/mcptools
brew install mcp
mcp tools http://localhost:8000/sse
mcp call get_tables http://localhost:8000/sse
mcp call get_columns --params '{"table_name":"sales"}' http://localhost:8000/sse
mcp call get_table_info --params '{"table_name":"sales"}' http://localhost:8000/sse
mcp call query_table --params '{"table_name":"sales","limit":"1","offset":"1"}' http://localhost:8000/sse
```


*Inspiration: [No More SQL — Building an AI-powered CSV Analysis Agent with MCP](https://medium.com/@aktooall/no-more-sql-building-an-ai-powered-csv-analysis-agent-with-mcp-1716e89c3dba)*

*Example Code: [mcp csv analyzer](https://github.com/arunak1998/mcp_csv_analyser)
