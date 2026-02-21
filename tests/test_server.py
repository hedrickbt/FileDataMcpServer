"""Tests for all MCP tool endpoints in filedata.server."""

import json

import numpy as np
import pandas as pd
import pytest

from filedata.registry import set_registry
from filedata.server import get_columns, get_table_info, get_tables, query_table


# ─────────────────────────────────────────────────────────────────────────────
# get_tables
# ─────────────────────────────────────────────────────────────────────────────

class TestGetTables:
    def test_empty_registry_returns_empty_list(self):
        assert get_tables() == []

    def test_returns_sorted_table_names(self, populated_registry):
        result = get_tables()
        assert result == ["employees", "products"]

    def test_single_table(self):
        set_registry({"data": pd.DataFrame({"x": [1, 2, 3]})})
        assert get_tables() == ["data"]

    def test_multiple_tables_sorted(self):
        set_registry(
            {
                "zebra": pd.DataFrame({"a": [1]}),
                "apple": pd.DataFrame({"b": [2]}),
                "mango": pd.DataFrame({"c": [3]}),
            }
        )
        assert get_tables() == ["apple", "mango", "zebra"]

    def test_returns_list_type(self, populated_registry):
        assert isinstance(get_tables(), list)


# ─────────────────────────────────────────────────────────────────────────────
# get_columns
# ─────────────────────────────────────────────────────────────────────────────

class TestGetColumns:
    def test_returns_correct_column_names(self, populated_registry):
        result = get_columns("employees")
        names = [c["name"] for c in result]
        assert names == ["name", "age", "city", "salary"]

    def test_each_entry_has_name_and_dtype(self, populated_registry):
        result = get_columns("employees")
        for col in result:
            assert "name" in col
            assert "dtype" in col

    def test_integer_column_dtype(self, populated_registry):
        result = get_columns("employees")
        age = next(c for c in result if c["name"] == "age")
        assert "int" in age["dtype"]

    def test_float_column_dtype(self, populated_registry):
        result = get_columns("products")
        price = next(c for c in result if c["name"] == "price")
        assert "float" in price["dtype"]

    def test_string_column_dtype(self, populated_registry):
        result = get_columns("employees")
        name_col = next(c for c in result if c["name"] == "name")
        # pandas >= 3 / Python 3.14 uses "str"; older pandas uses "object"
        assert name_col["dtype"] in ("object", "str")

    def test_unknown_table_raises_key_error(self, populated_registry):
        with pytest.raises(KeyError, match="not found"):
            get_columns("nonexistent")

    def test_empty_dataframe_returns_empty_list(self):
        set_registry({"empty": pd.DataFrame()})
        assert get_columns("empty") == []

    def test_column_order_preserved(self):
        cols = ["z", "a", "m"]
        set_registry({"t": pd.DataFrame({c: [1] for c in cols})})
        result = get_columns("t")
        assert [r["name"] for r in result] == cols


# ─────────────────────────────────────────────────────────────────────────────
# query_table
# ─────────────────────────────────────────────────────────────────────────────

class TestQueryTable:
    def test_returns_json_string(self, populated_registry):
        result = query_table("employees")
        assert isinstance(result, str)
        rows = json.loads(result)
        assert isinstance(rows, list)

    def test_returns_all_rows_by_default(self, populated_registry):
        rows = json.loads(query_table("employees"))
        assert len(rows) == 4

    def test_row_fields_match_columns(self, populated_registry):
        rows = json.loads(query_table("employees"))
        assert set(rows[0].keys()) == {"name", "age", "city", "salary"}

    def test_first_row_values(self, populated_registry):
        rows = json.loads(query_table("employees"))
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == 30

    def test_limit_restricts_row_count(self, populated_registry):
        rows = json.loads(query_table("employees", limit=2))
        assert len(rows) == 2

    def test_limit_of_one(self, populated_registry):
        rows = json.loads(query_table("employees", limit=1))
        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"

    def test_offset_skips_rows(self, populated_registry):
        rows = json.loads(query_table("employees", limit=2, offset=2))
        assert len(rows) == 2
        assert rows[0]["name"] == "Carol"

    def test_offset_beyond_end_returns_empty(self, populated_registry):
        rows = json.loads(query_table("employees", offset=100))
        assert rows == []

    def test_limit_hard_cap_at_1000(self):
        # Build a 1500-row table; even with limit=9999, should return ≤1000
        big_df = pd.DataFrame({"v": range(1500)})
        set_registry({"big": big_df})
        rows = json.loads(query_table("big", limit=9999))
        assert len(rows) == 1000

    def test_limit_minimum_is_one(self, populated_registry):
        rows = json.loads(query_table("employees", limit=0))
        assert len(rows) == 1

    def test_unknown_table_raises_key_error(self, populated_registry):
        with pytest.raises(KeyError, match="not found"):
            query_table("nonexistent")

    def test_empty_table_returns_empty_json_array(self):
        set_registry({"empty": pd.DataFrame({"a": pd.Series([], dtype=int)})})
        rows = json.loads(query_table("empty"))
        assert rows == []


# ─────────────────────────────────────────────────────────────────────────────
# get_table_info
# ─────────────────────────────────────────────────────────────────────────────

class TestGetTableInfo:
    def test_returns_table_name(self, populated_registry):
        info = get_table_info("employees")
        assert info["table_name"] == "employees"

    def test_returns_row_count(self, populated_registry):
        info = get_table_info("employees")
        assert info["row_count"] == 4

    def test_returns_column_count(self, populated_registry):
        info = get_table_info("employees")
        assert info["column_count"] == 4

    def test_columns_list_has_correct_fields(self, populated_registry):
        info = get_table_info("employees")
        for col in info["columns"]:
            assert "name" in col
            assert "dtype" in col
            assert "null_count" in col
            assert "null_pct" in col

    def test_null_count_zero_for_clean_data(self, populated_registry):
        info = get_table_info("employees")
        for col in info["columns"]:
            assert col["null_count"] == 0
            assert col["null_pct"] == 0.0

    def test_null_count_detected(self):
        df = pd.DataFrame({"a": [1.0, None, 3.0], "b": ["x", "y", None]})
        set_registry({"sparse": df})
        info = get_table_info("sparse")
        a_col = next(c for c in info["columns"] if c["name"] == "a")
        b_col = next(c for c in info["columns"] if c["name"] == "b")
        assert a_col["null_count"] == 1
        assert b_col["null_count"] == 1

    def test_null_pct_calculation(self):
        df = pd.DataFrame({"x": [1.0, None, None, None]})  # 3/4 = 75%
        set_registry({"pct": df})
        info = get_table_info("pct")
        col = info["columns"][0]
        assert col["null_pct"] == 75.0

    def test_sample_contains_up_to_five_rows(self, populated_registry):
        info = get_table_info("employees")
        assert len(info["sample"]) == 4  # table only has 4 rows

    def test_sample_capped_at_five(self):
        df = pd.DataFrame({"v": range(20)})
        set_registry({"large": df})
        info = get_table_info("large")
        assert len(info["sample"]) == 5

    def test_sample_is_list_of_dicts(self, populated_registry):
        info = get_table_info("employees")
        assert isinstance(info["sample"], list)
        assert isinstance(info["sample"][0], dict)

    def test_unknown_table_raises_key_error(self, populated_registry):
        with pytest.raises(KeyError, match="not found"):
            get_table_info("nonexistent")

    def test_result_is_json_serialisable(self, populated_registry):
        info = get_table_info("employees")
        # Should not raise
        json.dumps(info)
