"""In-memory table registry — stores loaded DataFrames by name."""

import pandas as pd

_registry: dict[str, pd.DataFrame] = {}


def get_registry() -> dict[str, pd.DataFrame]:
    """Return the full registry dict."""
    return _registry


def get_table(name: str) -> pd.DataFrame:
    """Return a single table by name, raising KeyError if missing."""
    if name not in _registry:
        available = sorted(_registry.keys())
        raise KeyError(
            f"Table '{name}' not found. "
            f"Available tables: {available}"
        )
    return _registry[name]


def set_registry(tables: dict[str, pd.DataFrame]) -> None:
    """Replace the entire registry (useful for testing)."""
    global _registry
    _registry = dict(tables)


def update_registry(tables: dict[str, pd.DataFrame]) -> None:
    """Merge new tables into the existing registry."""
    _registry.update(tables)


def clear_registry() -> None:
    """Remove all tables from the registry."""
    global _registry
    _registry = {}


def load_sources(sources: list[str]) -> None:
    """Load one or more file sources into the registry."""
    from .loader import load_source

    for source in sources:
        tables = load_source(source)
        update_registry(tables)
