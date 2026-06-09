"""
ETL Service.

Performs Extract-Transform-Load operations on uploaded datasets:
- Load CSV / Excel into a pandas DataFrame.
- Clean column names.
- Handle missing values (impute numeric with median, categorical with mode).
- Deduplicate rows.
- Coerce date columns and numeric columns where possible.
- Aggregate metrics for downstream analytics.
"""
from __future__ import annotations
import io
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ETLService:
    """Extract-Transform-Load pipeline for tabular business data."""

    @staticmethod
    def load_file(path: str) -> pd.DataFrame:
        """Load a CSV or Excel file from disk into a DataFrame."""
        path_lower = path.lower()
        try:
            if path_lower.endswith(".csv"):
                # Try multiple encodings to be safe
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        return pd.read_csv(path, encoding=enc)
                    except UnicodeDecodeError:
                        continue
                return pd.read_csv(path, encoding="utf-8", errors="ignore")
            elif path_lower.endswith((".xls", ".xlsx")):
                return pd.read_excel(path)
            else:
                raise ValueError(f"Unsupported file format: {path}")
        except Exception as e:
            logger.exception("Failed to load file %s", path)
            raise

    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Lowercase, strip, replace whitespace/symbols with underscore."""
        df = df.copy()
        df.columns = [
            re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")
            for c in df.columns
        ]
        return df

    @staticmethod
    def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
        """Heuristically detect semantic types: date | numeric | categorical."""
        types: Dict[str, str] = {}
        for col in df.columns:
            series = df[col]
            if pd.api.types.is_datetime64_any_dtype(series):
                types[col] = "date"
                continue
            # try to parse as date if name hints at it
            if any(k in col for k in ("date", "time", "month", "day", "year")):
                try:
                    pd.to_datetime(series, errors="raise")
                    types[col] = "date"
                    continue
                except Exception:
                    pass
            if pd.api.types.is_numeric_dtype(series):
                types[col] = "numeric"
            else:
                # attempt numeric coercion
                coerced = pd.to_numeric(series, errors="coerce")
                if coerced.notna().sum() / max(len(series), 1) > 0.8:
                    types[col] = "numeric"
                else:
                    types[col] = "categorical"
        return types

    @staticmethod
    def handle_missing_values(df: pd.DataFrame, col_types: Dict[str, str]) -> pd.DataFrame:
        """Impute numeric NaNs with median, categorical with mode."""
        df = df.copy()
        for col, t in col_types.items():
            if df[col].isna().sum() == 0:
                continue
            if t == "numeric":
                df[col] = pd.to_numeric(df[col], errors="coerce")
                median = df[col].median()
                df[col] = df[col].fillna(median if pd.notna(median) else 0)
            elif t == "date":
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df[col] = df[col].ffill().bfill()
            else:
                mode = df[col].mode()
                fill = mode.iloc[0] if not mode.empty else "Unknown"
                df[col] = df[col].fillna(fill)
        return df

    @staticmethod
    def transform(df: pd.DataFrame, col_types: Dict[str, str]) -> pd.DataFrame:
        """Coerce dtypes and drop full duplicates."""
        df = df.copy()
        for col, t in col_types.items():
            if t == "date":
                df[col] = pd.to_datetime(df[col], errors="coerce")
            elif t == "numeric":
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.drop_duplicates().reset_index(drop=True)
        return df

    @classmethod
    def run_pipeline(cls, path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Full ETL pipeline. Returns cleaned df + metadata."""
        raw = cls.load_file(path)
        original_rows = len(raw)
        df = cls.clean_column_names(raw)
        # null counts are computed BEFORE imputation, on the freshly-renamed frame
        null_counts = df.isna().sum().to_dict()
        col_types = cls.detect_column_types(df)
        df = cls.handle_missing_values(df, col_types)
        df = cls.transform(df, col_types)

        columns_meta = []
        for col in df.columns:
            sample_val = df[col].dropna().iloc[0] if df[col].dropna().shape[0] else None
            columns_meta.append({
                "name": col,
                "dtype": col_types.get(col, str(df[col].dtype)),
                "null_count": int(null_counts.get(col, 0)),
                "sample": str(sample_val) if sample_val is not None else None,
            })

        meta = {
            "original_rows": original_rows,
            "cleaned_rows": len(df),
            "duplicates_removed": original_rows - len(df),
            "columns_meta": columns_meta,
            "column_types": col_types,
        }
        return df, meta

    # ------------- Aggregations -----------------

    @staticmethod
    def find_date_column(df: pd.DataFrame, col_types: Dict[str, str]) -> Optional[str]:
        for col, t in col_types.items():
            if t == "date":
                return col
        return None

    @staticmethod
    def find_revenue_column(df: pd.DataFrame, col_types: Dict[str, str]) -> Optional[str]:
        candidates = ["revenue", "sales", "amount", "total", "price", "value", "income"]
        for col in df.columns:
            if col_types.get(col) == "numeric" and any(k in col for k in candidates):
                return col
        # fallback: first numeric column
        for col, t in col_types.items():
            if t == "numeric":
                return col
        return None

    @staticmethod
    def find_category_column(df: pd.DataFrame, col_types: Dict[str, str]) -> Optional[str]:
        candidates = ["product", "category", "region", "segment", "channel", "customer"]
        for col in df.columns:
            if col_types.get(col) == "categorical" and any(k in col for k in candidates):
                return col
        for col, t in col_types.items():
            if t == "categorical":
                return col
        return None
