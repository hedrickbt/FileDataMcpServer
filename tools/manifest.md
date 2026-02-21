# Tools Manifest

> Master index of all available tools. Always check here before writing a new script.

## FileData MCP Server (`src/filedata/`)

| Script | Description |
|--------|-------------|
| `server.py` | FastMCP server exposing `get_tables`, `get_columns`, `query_table`, and `get_table_info` as MCP tools. |
| `loader.py` | Loads CSV/Excel files from local paths or HTTPS URLs into pandas DataFrames. |
| `registry.py` | In-memory table registry (dict of name → DataFrame); supports get, set, update, clear. |
| `config.py` | Reads `FILEDATA_SOURCES`, `FILEDATA_TRANSPORT`, `FILEDATA_HOST`, `FILEDATA_PORT` from env / .env. |

---

## Memory Tools (`tools/memory/`)

| Script | Description |
|--------|-------------|
| `memory_read.py` | Reads memory entries from the database, outputting facts/preferences in markdown or JSON format. |
| `memory_write.py` | Writes new memory entries (facts, preferences, events, insights) to the database or updates MEMORY.md. |
| `memory_db.py` | Direct database operations for memory — search, list, delete entries by keyword or type. |
| `embed_memory.py` | Generates vector embeddings for memory entries to enable semantic similarity search. |
| `semantic_search.py` | Searches memory using vector embeddings for conceptually related results. |
| `hybrid_search.py` | Combined keyword + semantic search for best-of-both memory retrieval. |

---

*Last updated: 2026-02-20*
*Add new tools here immediately after creating them.*
