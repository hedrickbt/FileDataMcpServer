"""Tests for filedata.loader — local and HTTPS file loading."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from filedata.loader import load_source


# ─────────────────────────────────────────────────────────────────────────────
# Local CSV loading
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadCsvFromPath:
    def test_returns_single_table(self, sample_csv_path):
        tables = load_source(str(sample_csv_path))
        assert len(tables) == 1

    def test_table_named_after_file_stem(self, sample_csv_path):
        tables = load_source(str(sample_csv_path))
        assert "employees" in tables

    def test_correct_row_count(self, sample_csv_path):
        tables = load_source(str(sample_csv_path))
        assert len(tables["employees"]) == 4

    def test_correct_columns(self, sample_csv_path):
        tables = load_source(str(sample_csv_path))
        assert list(tables["employees"].columns) == ["name", "age", "city", "salary"]

    def test_returns_dataframe(self, sample_csv_path):
        tables = load_source(str(sample_csv_path))
        assert isinstance(tables["employees"], pd.DataFrame)

    def test_data_values_correct(self, sample_csv_path):
        tables = load_source(str(sample_csv_path))
        df = tables["employees"]
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[0]["age"] == 30


# ─────────────────────────────────────────────────────────────────────────────
# Local Excel loading
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadExcelFromPath:
    def test_returns_one_table_per_sheet(self, sample_excel_path):
        tables = load_source(str(sample_excel_path))
        assert set(tables.keys()) == {"Q1", "Q2"}

    def test_table_named_after_sheet_tab(self, sample_excel_path):
        tables = load_source(str(sample_excel_path))
        assert "Q1" in tables
        assert "Q2" in tables

    def test_sheet_correct_columns(self, sample_excel_path):
        tables = load_source(str(sample_excel_path))
        assert list(tables["Q1"].columns) == ["product", "revenue"]

    def test_sheet_correct_row_count(self, sample_excel_path):
        tables = load_source(str(sample_excel_path))
        assert len(tables["Q1"]) == 2
        assert len(tables["Q2"]) == 2

    def test_sheet_data_values(self, sample_excel_path):
        tables = load_source(str(sample_excel_path))
        assert tables["Q1"].iloc[0]["product"] == "Widget"
        assert tables["Q2"].iloc[0]["product"] == "Gizmo"

    def test_returns_dataframes(self, sample_excel_path):
        tables = load_source(str(sample_excel_path))
        for df in tables.values():
            assert isinstance(df, pd.DataFrame)

    def test_single_sheet_excel(self, tmp_path):
        path = tmp_path / "one_sheet.xlsx"
        pd.DataFrame({"x": [1, 2]}).to_excel(path, sheet_name="Data", index=False)
        tables = load_source(str(path))
        assert list(tables.keys()) == ["Data"]


# ─────────────────────────────────────────────────────────────────────────────
# Error cases — local files
# ─────────────────────────────────────────────────────────────────────────────

class TestLocalFileErrors:
    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_source(str(tmp_path / "ghost.csv"))

    def test_unsupported_extension_raises_value_error(self, tmp_path):
        bad = tmp_path / "data.json"
        bad.write_text('{"key": "value"}')
        with pytest.raises(ValueError, match="Unsupported"):
            load_source(str(bad))

    def test_txt_extension_raises_value_error(self, tmp_path):
        bad = tmp_path / "notes.txt"
        bad.write_text("hello")
        with pytest.raises(ValueError, match="Unsupported"):
            load_source(str(bad))


# ─────────────────────────────────────────────────────────────────────────────
# HTTPS URL loading
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadCsvFromUrl:
    def _make_mock_response(self, content: bytes) -> MagicMock:
        mock = MagicMock()
        mock.content = content
        mock.raise_for_status = MagicMock()
        return mock

    def test_loads_csv_from_url(self, sample_csv_bytes):
        with patch("filedata.loader.requests.get", return_value=self._make_mock_response(sample_csv_bytes)):
            tables = load_source("https://example.com/employees.csv")
        assert "employees" in tables

    def test_csv_url_table_named_after_url_stem(self, sample_csv_bytes):
        with patch("filedata.loader.requests.get", return_value=self._make_mock_response(sample_csv_bytes)):
            tables = load_source("https://example.com/employees.csv")
        assert list(tables.keys()) == ["employees"]

    def test_csv_url_row_count(self, sample_csv_bytes):
        with patch("filedata.loader.requests.get", return_value=self._make_mock_response(sample_csv_bytes)):
            tables = load_source("https://example.com/employees.csv")
        assert len(tables["employees"]) == 4

    def test_csv_url_columns(self, sample_csv_bytes):
        with patch("filedata.loader.requests.get", return_value=self._make_mock_response(sample_csv_bytes)):
            tables = load_source("https://example.com/employees.csv")
        assert list(tables["employees"].columns) == ["name", "age", "city", "salary"]


class TestLoadExcelFromUrl:
    def _make_mock_response(self, content: bytes) -> MagicMock:
        mock = MagicMock()
        mock.content = content
        mock.raise_for_status = MagicMock()
        return mock

    def test_loads_excel_from_url(self, sample_excel_bytes):
        with patch("filedata.loader.requests.get", return_value=self._make_mock_response(sample_excel_bytes)):
            tables = load_source("https://example.com/report.xlsx")
        assert "Q1" in tables
        assert "Q2" in tables

    def test_excel_url_sheet_columns(self, sample_excel_bytes):
        with patch("filedata.loader.requests.get", return_value=self._make_mock_response(sample_excel_bytes)):
            tables = load_source("https://example.com/report.xlsx")
        assert list(tables["Q1"].columns) == ["product", "revenue"]

    def test_excel_url_sheet_row_count(self, sample_excel_bytes):
        with patch("filedata.loader.requests.get", return_value=self._make_mock_response(sample_excel_bytes)):
            tables = load_source("https://example.com/report.xlsx")
        assert len(tables["Q1"]) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Error cases — URL loading
# ─────────────────────────────────────────────────────────────────────────────

class TestUrlErrors:
    def test_http_error_raises_runtime_error(self):
        mock = MagicMock()
        mock.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        with patch("filedata.loader.requests.get", return_value=mock):
            with pytest.raises(RuntimeError, match="Failed to fetch"):
                load_source("https://example.com/missing.csv")

    def test_connection_error_raises_runtime_error(self):
        with patch("filedata.loader.requests.get", side_effect=requests.ConnectionError("unreachable")):
            with pytest.raises(RuntimeError, match="Failed to fetch"):
                load_source("https://example.com/data.csv")

    def test_unsupported_extension_in_url_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported"):
            load_source("https://example.com/data.parquet")

    def test_timeout_raises_runtime_error(self):
        with patch("filedata.loader.requests.get", side_effect=requests.Timeout("timed out")):
            with pytest.raises(RuntimeError, match="Failed to fetch"):
                load_source("https://example.com/data.csv")
