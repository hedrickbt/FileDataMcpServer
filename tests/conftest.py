"""Shared pytest fixtures for the FileData MCP Server test suite."""

from pathlib import Path

import pandas as pd
import pytest

from filedata.registry import clear_registry, set_registry

# ── Helpers ───────────────────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _employees_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Carol", "Dave"],
            "age": [30, 25, 35, 28],
            "city": ["New York", "San Francisco", "Chicago", "Austin"],
            "salary": [75000, 85000, 65000, 70000],
        }
    )


def _products_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "product": ["Widget", "Gadget", "Gizmo"],
            "price": [9.99, 19.99, 4.99],
            "stock": [100, 50, 200],
        }
    )


# ── Auto-reset ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_registry():
    """Clear the in-memory registry before and after every test."""
    clear_registry()
    yield
    clear_registry()


# ── Registry fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def populated_registry() -> dict[str, pd.DataFrame]:
    """Populate registry with two sample tables and return them."""
    tables = {
        "employees": _employees_df(),
        "products": _products_df(),
    }
    set_registry(tables)
    return tables


# ── File fixtures (written to tmp_path so tests are isolated) ─────────────────

@pytest.fixture
def sample_csv_path(tmp_path) -> Path:
    """Write a CSV file and return its path."""
    path = tmp_path / "employees.csv"
    _employees_df().to_csv(path, index=False)
    return path


@pytest.fixture
def sample_excel_path(tmp_path) -> Path:
    """Write an Excel file with two sheets (Q1, Q2) and return its path."""
    path = tmp_path / "report.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(
            {"product": ["Widget", "Gadget"], "revenue": [1000, 2000]}
        ).to_excel(writer, sheet_name="Q1", index=False)

        pd.DataFrame(
            {"product": ["Gizmo", "Thingamajig"], "revenue": [1500, 2500]}
        ).to_excel(writer, sheet_name="Q2", index=False)
    return path


@pytest.fixture
def sample_csv_bytes(sample_csv_path) -> bytes:
    """Return the raw bytes of the sample CSV (for URL-mock tests)."""
    return sample_csv_path.read_bytes()


@pytest.fixture
def sample_excel_bytes(sample_excel_path) -> bytes:
    """Return the raw bytes of the sample Excel (for URL-mock tests)."""
    return sample_excel_path.read_bytes()
