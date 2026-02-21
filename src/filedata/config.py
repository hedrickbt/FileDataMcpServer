"""Configuration — reads settings from environment variables / .env file."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_sources() -> list[str]:
    """Return the list of configured file sources.

    Reads ``FILEDATA_SOURCES`` — a comma-separated list of local paths
    and/or HTTPS URLs.
    """
    raw = os.getenv("FILEDATA_SOURCES", "")
    return [s.strip() for s in raw.split(",") if s.strip()]


def get_transport() -> str:
    """Return the MCP transport to use: 'stdio' (default) or 'sse'."""
    return os.getenv("FILEDATA_TRANSPORT", "stdio").lower()


def get_host() -> str:
    """Return the SSE server host (used when transport='sse')."""
    return os.getenv("FILEDATA_HOST", "0.0.0.0")


def get_port() -> int:
    """Return the SSE server port (used when transport='sse')."""
    return int(os.getenv("FILEDATA_PORT", "8000"))
