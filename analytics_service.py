"""
Analytics Service.

Produces business analytics from a cleaned DataFrame:
- KPIs (total revenue, avg order value, growth %, customer counts, etc.)
- Revenue trend over time
- Top performing categories / products
- Customer insights
- Chart-ready data for the frontend
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from .etl_service import ETLService


class AnalyticsService:
    """Compute business KPIs and chart data from cleaned tabular data."""

    @classmethod
    def analyze(cls, df: pd.DataFrame, col_types: Dict[str, str]) -> Dict[str, Any]:
        """Run full analytics pipeline.

        Returns a dict with: kpis, charts, top_categories, time_series, summary_stats.
        """
        date_col = ETLService.find_date_column(df, col_types)
        revenue_col = ETLService.find_revenue_column(df, col_types)
        category_col = ETLService.find_category_column(df, col_types)

        result: Dict[str, Any] = {
            "kpis": {},
            "charts": [],
            "summary_stats": {},
            "meta": {
                "date_column": date_col,
                "revenue_column": revenue_col,
                "category_column": category_col,
            },
        }

        # ---------- KPIs ----------
        kpis: Dict[str, Any] = {"total_records": int(len(df))}

        if revenue_col:
            rev = pd.to_numeric(df[revenue_col], errors="coerce").dropna()
            kpis["total_revenue"] = float(round(rev.sum(), 2))
            kpis["average_value"] = float(round(rev.mean(), 2)) if len(rev) else 0.0
            kpis["median_value"] = float(round(rev.median(), 2)) if len(rev) else 0.0
            kpis["max_value"] = float(round(rev.max(), 2)) if len(rev) else 0.0
            kpis["min_value"] = float(round(rev.min(), 2)) if len(rev) else 0.0

        if category_col:
            kpis["unique_categories"] = int(df[category_col].nunique())

        if date_col:
            dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
            if len(dates):
                kpis["date_range_start"] = str(dates.min().date())
                kpis["date_range_end"] = str(dates.max().date())
                kpis["span_days"] = int((dates.max() - dates.min()).days)

        # Growth %: compare last week vs previous week if date+revenue exist
        if date_col and revenue_col:
            tmp = df[[date_col, revenue_col]].copy()
            tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
            tmp[revenue_col] = pd.to_numeric(tmp[revenue_col], errors="coerce")
            tmp = tmp.dropna()
            if not tmp.empty:
                tmp = tmp.sort_values(date_col)
                tmp["_week"] = tmp[date_col].dt.to_period("W")
                weekly = tmp.groupby("_week")[revenue_col].sum()
                if len(weekly) >= 2:
                    last, prev = float(weekly.iloc[-1]), float(weekly.iloc[-2])
                    growth = ((last - prev) / prev * 100.0) if prev else 0.0
                    kpis["week_over_week_growth_pct"] = round(growth, 2)
                    kpis["last_week_revenue"] = round(last, 2)
                    kpis["previous_week_revenue"] = round(prev, 2)

        result["kpis"] = kpis

        # ---------- Time series chart ----------
        if date_col and revenue_col:
            tmp = df[[date_col, revenue_col]].copy()
            tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
            tmp[revenue_col] = pd.to_numeric(tmp[revenue_col], errors="coerce")
            tmp = tmp.dropna()
            if not tmp.empty:
                daily = (
                    tmp.groupby(tmp[date_col].dt.date)[revenue_col]
                    .sum()
                    .reset_index()
                    .rename(columns={date_col: "date", revenue_col: "value"})
                )
                daily["date"] = daily["date"].astype(str)
                result["charts"].append({
                    "title": "Revenue Trend Over Time",
                    "type": "line",
                    "x_key": "date",
                    "y_keys": ["value"],
                    "data": daily.tail(60).to_dict(orient="records"),
                })

        # ---------- Category breakdown ----------
        if category_col and revenue_col:
            tmp = df[[category_col, revenue_col]].copy()
            tmp[revenue_col] = pd.to_numeric(tmp[revenue_col], errors="coerce")
            tmp = tmp.dropna()
            if not tmp.empty:
                top = (
                    tmp.groupby(category_col)[revenue_col]
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                    .reset_index()
                    .rename(columns={category_col: "name", revenue_col: "value"})
                )
                result["charts"].append({
                    "title": f"Top {len(top)} by {category_col.replace('_', ' ').title()}",
                    "type": "bar",
                    "x_key": "name",
                    "y_keys": ["value"],
                    "data": top.to_dict(orient="records"),
                })
                # pie chart for share
                result["charts"].append({
                    "title": f"Share by {category_col.replace('_', ' ').title()}",
                    "type": "pie",
                    "x_key": "name",
                    "y_keys": ["value"],
                    "data": top.head(6).to_dict(orient="records"),
                })

        # ---------- Customer / volume insights ----------
        if category_col:
            counts = (
                df[category_col]
                .value_counts()
                .head(10)
                .reset_index()
            )
            counts.columns = ["name", "value"]
            result["charts"].append({
                "title": f"Volume by {category_col.replace('_', ' ').title()}",
                "type": "bar",
                "x_key": "name",
                "y_keys": ["value"],
                "data": counts.to_dict(orient="records"),
            })

        # ---------- Numeric summary stats ----------
        numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
        if numeric_cols:
            desc = df[numeric_cols].describe().round(2).to_dict()
            # convert numpy types to python primitives
            result["summary_stats"] = {
                col: {k: float(v) for k, v in stats.items()}
                for col, stats in desc.items()
            }

        return result
