"""
Compare two Excel/CSV files on the shared columns `transaction ID` and `amount`.

Result categories:
    - matched           : same transaction ID in both files, same amount
    - mismatched        : same transaction ID in both files, different amount
    - missing_in_b      : transaction ID present in file A but not in B
    - missing_in_a      : transaction ID present in file B but not in A
    - null_rows         : rows where transaction ID or amount is empty/null
                          (collected from both files, with a source label)

Column matching is case-insensitive and whitespace-trimmed.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = ('transactionid', 'amount')


class CompareError(Exception):
    """Raised when files can't be compared (bad format, missing columns, etc.)."""


class FileOnDisk:
    """Tiny adapter so the Celery worker can pass file paths into compare_files().

    Quacks like a Django UploadedFile (has `.name` + `.read()`) but reads from disk.
    """

    def __init__(self, path: str, display_name: str | None = None):
        import os
        self._path = path
        self.name = display_name or os.path.basename(path)

    def read(self) -> bytes:
        with open(self._path, 'rb') as fh:
            return fh.read()


@dataclass
class CompareResult:
    matched: list[dict[str, Any]] = field(default_factory=list)
    mismatched: list[dict[str, Any]] = field(default_factory=list)
    missing_in_a: list[dict[str, Any]] = field(default_factory=list)
    missing_in_b: list[dict[str, Any]] = field(default_factory=list)
    null_rows: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(
            self.mismatched or self.missing_in_a or self.missing_in_b or self.null_rows
        )

    @property
    def total_issues(self) -> int:
        return (
            len(self.mismatched)
            + len(self.missing_in_a)
            + len(self.missing_in_b)
            + len(self.null_rows)
        )


def _identify_zip_payload(data: bytes) -> str | None:
    """If `data` is a ZIP, look at its entry names to identify the format.
    Returns a short kind string ('xlsx', 'numbers', 'ods') or None if unknown."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()
    except zipfile.BadZipFile:
        return None
    names_lower = {n.lower() for n in names}
    if any(n.startswith('xl/') for n in names_lower):
        return 'xlsx'
    if any(n.endswith('.iwa') for n in names_lower) or any(
        n.startswith('index/') for n in names_lower
    ):
        return 'numbers'
    if 'mimetype' in names_lower:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                mt = z.read('mimetype').decode('ascii', errors='ignore')
            if 'opendocument.spreadsheet' in mt:
                return 'ods'
        except Exception:
            pass
    return None


def _read_file(uploaded_file) -> pd.DataFrame:
    """Read an uploaded Django file into a pandas DataFrame."""
    name = uploaded_file.name.lower()
    data = uploaded_file.read()

    if name.endswith('.csv'):
        try:
            return pd.read_csv(io.BytesIO(data))
        except Exception as exc:
            raise CompareError(f"Couldn't parse {uploaded_file.name} as CSV: {exc}") from exc

    # For .xlsx/.xls — first check what the bytes actually are, since users often
    # rename Numbers/ODS files to .xlsx and pandas's error is cryptic.
    if data[:2] == b'PK':
        kind = _identify_zip_payload(data)
        if kind == 'numbers':
            raise CompareError(
                f"{uploaded_file.name} is an Apple Numbers file, not Excel. "
                f"In Numbers, choose File → Export To → Excel… and upload that file."
            )
        if kind == 'ods':
            raise CompareError(
                f"{uploaded_file.name} is an OpenDocument Spreadsheet (.ods), not Excel. "
                f"Save it as .xlsx and re-upload."
            )
        if kind is None:
            raise CompareError(
                f"{uploaded_file.name} looks like a ZIP file but isn't a valid Excel workbook. "
                f"Re-save it from Excel as .xlsx."
            )
        # kind == 'xlsx' — fall through to pandas
    elif data[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
        # Old-format .xls (OLE2 compound document). Needs xlrd, which we don't install.
        raise CompareError(
            f"{uploaded_file.name} is an old-format .xls file. "
            f"Open it in Excel and save it as .xlsx, then re-upload."
        )
    elif data[:5].lower() in (b'<html', b'<!doc'):
        raise CompareError(
            f"{uploaded_file.name} is actually an HTML file (some exports do this). "
            f"Open it in Excel and save it as a real .xlsx, then re-upload."
        )

    try:
        return pd.read_excel(io.BytesIO(data))
    except Exception as exc:
        raise CompareError(f"Couldn't parse {uploaded_file.name}: {exc}") from exc


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize headers so 'Transaction ID', 'transaction-id', 'transaction_id'
    and 'transactionid' all collapse to the same key."""
    df = df.copy()
    df.columns = [
        ''.join(ch for ch in str(c).lower() if ch.isalnum())
        for c in df.columns
    ]
    return df


def _check_required_columns(df: pd.DataFrame, label: str) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise CompareError(
            f"{label} is missing required column(s): "
            f"{', '.join(missing)}. "
            f"Each file must contain 'transaction ID' and 'amount'."
        )


def _coerce_amount(val):
    """Try to interpret a cell as a number. Returns (number_or_None, is_null)."""
    if val is None:
        return None, True
    if isinstance(val, float) and pd.isna(val):
        return None, True
    if isinstance(val, str) and val.strip() == '':
        return None, True
    try:
        return float(val), False
    except (TypeError, ValueError):
        return None, True  # treat un-coercible as null/invalid


def _is_null_id(val) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and pd.isna(val):
        return True
    if isinstance(val, str) and val.strip() == '':
        return True
    return False


def compare_files(file_a, file_b) -> CompareResult:
    """Top-level entry point used by the view.

    file_a, file_b: Django UploadedFile objects.
    Raises CompareError for user-visible problems (missing columns, parse errors).
    """
    df_a = _normalize_columns(_read_file(file_a))
    df_b = _normalize_columns(_read_file(file_b))

    _check_required_columns(df_a, f"File A ({file_a.name})")
    _check_required_columns(df_b, f"File B ({file_b.name})")

    result = CompareResult()

    # --- 1) Pull out rows with null transaction id or amount, per-file. ---
    def extract_nulls(df: pd.DataFrame, source: str) -> pd.DataFrame:
        bad_mask = df['transactionid'].apply(_is_null_id) | df['amount'].apply(
            lambda v: _coerce_amount(v)[1]
        )
        bad = df[bad_mask]
        for _, row in bad.iterrows():
            result.null_rows.append({
                'source': source,
                'transaction_id': row['transactionid'],
                'amount': row['amount'],
            })
        return df[~bad_mask]

    clean_a = extract_nulls(df_a, file_a.name)
    clean_b = extract_nulls(df_b, file_b.name)

    # --- 2) Build {id: amount} maps from the clean rows. ---
    #     If duplicate IDs appear, keep the first occurrence and flag the rest
    #     as nulls/anomalies so the user sees them.
    def build_map(df: pd.DataFrame, source: str) -> dict[str, float]:
        m: dict[str, float] = {}
        for _, row in df.iterrows():
            tid = str(row['transactionid']).strip()
            amt, _ = _coerce_amount(row['amount'])
            if tid in m:
                result.null_rows.append({
                    'source': source,
                    'transaction_id': tid,
                    'amount': row['amount'],
                    'note': 'duplicate transaction ID in this file',
                })
                continue
            m[tid] = amt
        return m

    map_a = build_map(clean_a, file_a.name)
    map_b = build_map(clean_b, file_b.name)

    # --- 3) Walk the union of IDs and bucket each one. ---
    all_ids = set(map_a) | set(map_b)
    for tid in sorted(all_ids):
        a_amt = map_a.get(tid)
        b_amt = map_b.get(tid)
        if tid not in map_b:
            result.missing_in_b.append({'transaction_id': tid, 'amount_a': a_amt})
        elif tid not in map_a:
            result.missing_in_a.append({'transaction_id': tid, 'amount_b': b_amt})
        elif a_amt != b_amt:
            result.mismatched.append({
                'transaction_id': tid,
                'amount_a': a_amt,
                'amount_b': b_amt,
            })
        else:
            result.matched.append({'transaction_id': tid, 'amount': a_amt})

    return result
