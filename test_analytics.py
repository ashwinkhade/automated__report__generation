"""Unit tests for the Analytics service."""
import pandas as pd
from backend.services.etl_service import ETLService
from backend.services.analytics_service import AnalyticsService


def test_analytics_pipeline(tmp_path):
    df = pd.DataFrame({
        "order_date": pd.date_range("2025-01-01", periods=20),
        "product_category": ["A", "B"] * 10,
        "revenue": list(range(100, 120)),
    })
    p = tmp_path / "x.csv"
    df.to_csv(p, index=False)

    cleaned, meta = ETLService.run_pipeline(str(p))
    result = AnalyticsService.analyze(cleaned, meta["column_types"])

    assert "kpis" in result
    assert "total_revenue" in result["kpis"]
    assert len(result["charts"]) >= 1
    assert result["meta"]["date_column"] == "order_date"
    assert result["meta"]["revenue_column"] == "revenue"
