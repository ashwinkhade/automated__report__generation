"""Unit tests for the ETL service."""
import os
import tempfile
import pandas as pd
import pytest
from backend.services.etl_service import ETLService


@pytest.fixture
def sample_csv(tmp_path):
    df = pd.DataFrame({
        # row 1 and row 2 are exact duplicates → one must be removed
        "Order Date": ["2025-01-01", "2025-01-02", "2025-01-02", None, "2025-01-03"],
        "Product Category": ["A", "B", "B", "C", "B"],
        "Revenue ($)": [100, 200.5, 200.5, None, 300],
        "Customer": ["x", "y", "y", "z", "y"],
    })
    p = tmp_path / "sample.csv"
    df.to_csv(p, index=False)
    return str(p)


def test_load_and_clean(sample_csv):
    df, meta = ETLService.run_pipeline(sample_csv)
    # cleaned column names
    assert "order_date" in df.columns
    assert "product_category" in df.columns
    assert "revenue" in df.columns or "revenue_" in df.columns
    # duplicates removed
    assert meta["duplicates_removed"] >= 1
    # no NaNs after imputation
    assert df.isna().sum().sum() == 0


def test_column_type_detection(sample_csv):
    df, meta = ETLService.run_pipeline(sample_csv)
    types = meta["column_types"]
    assert any(t == "date" for t in types.values())
    assert any(t == "numeric" for t in types.values())
    assert any(t == "categorical" for t in types.values())
