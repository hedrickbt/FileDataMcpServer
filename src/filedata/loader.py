"""File loading logic — local paths and HTTPS URLs, CSV and Excel."""

import tempfile
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".xlsm"}


def load_source(source: str) -> dict[str, pd.DataFrame]:
    """Load a CSV or Excel file from a local path or HTTPS URL.

    Returns a dict of ``table_name -> DataFrame``.

    - CSV files produce one table named after the file stem.
    - Excel files produce one table per sheet, named after the sheet tab.
    """
    source = source.strip()
    if source.startswith("https://") or source.startswith("http://"):
        return _load_from_url(source)
    return _load_from_path(Path(source))


def _load_from_path(path: Path) -> dict[str, pd.DataFrame]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    if suffix == ".csv":
        return {path.stem: pd.read_csv(path)}

    # Excel — each sheet becomes its own table
    return _load_excel(path)


def _load_excel(path: Path) -> dict[str, pd.DataFrame]:
    excel_file = pd.ExcelFile(path)
    tables: dict[str, pd.DataFrame] = {}
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        tables[str(sheet_name)] = df
    return tables


def _load_from_url(url: str) -> dict[str, pd.DataFrame]:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}' in URL. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch '{url}': {exc}") from exc

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = Path(tmp.name)

    try:
        result = _load_from_path(tmp_path)

        # CSV: rename the temp-filename key to the URL's filename stem
        if suffix == ".csv":
            url_stem = Path(parsed.path).stem
            result = {url_stem: next(iter(result.values()))}

        return result
    finally:
        tmp_path.unlink(missing_ok=True)
