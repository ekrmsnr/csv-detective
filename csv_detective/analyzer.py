from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


class CSVAnalyzer:
    """Analyzes a CSV file and exposes statistics."""

    def __init__(self, path: Path, sep: str = ",", encoding: str = "utf-8") -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise ValueError(f"File not found: '{self.path}'")
        if not self.path.suffix.lower() == ".csv":
            raise ValueError(f"Not a CSV file: '{self.path}'")

        self._sep = sep
        self._encoding = encoding
        self._df: pd.DataFrame | None = None

    # ------------------------------------------------------------------ #
    #  Loading                                                             #
    # ------------------------------------------------------------------ #

    def load(self) -> None:
        try:
            self._df = pd.read_csv(self.path, sep=self._sep, encoding=self._encoding, low_memory=False)
        except UnicodeDecodeError:
            self._df = pd.read_csv(self.path, sep=self._sep, encoding="latin-1", low_memory=False)

    def _df_required(self) -> pd.DataFrame:
        if self._df is None:
            raise RuntimeError("Call load() first.")
        return self._df

    # ------------------------------------------------------------------ #
    #  File info                                                           #
    # ------------------------------------------------------------------ #

    def file_info(self) -> dict:
        df = self._df_required()
        size = self.path.stat().st_size
        return {
            "filename": self.path.name,
            "rows": len(df),
            "columns": len(df.columns),
            "file_size": _human_size(size),
            "duplicate_rows": int(df.duplicated().sum()),
            "total_cells": len(df) * len(df.columns),
            "missing_cells": int(df.isnull().sum().sum()),
        }

    # ------------------------------------------------------------------ #
    #  Column profiles                                                     #
    # ------------------------------------------------------------------ #

    def column_profiles(self) -> list[dict]:
        df = self._df_required()
        profiles = []
        for col in df.columns:
            series = df[col]
            dtype = _infer_type(series)
            missing = int(series.isnull().sum())
            missing_pct = round(missing / len(series) * 100, 1) if len(series) else 0
            unique = int(series.nunique())

            profile: dict[str, Any] = {
                "name": col,
                "type": dtype,
                "missing": missing,
                "missing_pct": missing_pct,
                "unique": unique,
            }

            if dtype == "numeric":
                num = pd.to_numeric(series, errors="coerce").dropna().astype(float)
                if len(num):
                    q1, q3 = num.quantile(0.25), num.quantile(0.75)
                    iqr = q3 - q1
                    outliers = int(((num < q1 - 1.5 * iqr) | (num > q3 + 1.5 * iqr)).sum())
                    profile.update({
                        "mean": round(float(num.mean()), 4),
                        "median": round(float(num.median()), 4),
                        "std": round(float(num.std()), 4),
                        "min": round(float(num.min()), 4),
                        "max": round(float(num.max()), 4),
                        "outliers": outliers,
                    })

            elif dtype == "categorical":
                top = series.value_counts().head(5)
                profile["top_values"] = [
                    {"value": str(v), "count": int(c)}
                    for v, c in top.items()
                ]

            profiles.append(profile)
        return profiles

    # ------------------------------------------------------------------ #
    #  Summary                                                             #
    # ------------------------------------------------------------------ #

    def summary(self) -> dict:
        df = self._df_required()
        profiles = self.column_profiles()
        numeric_cols = [p for p in profiles if p["type"] == "numeric"]
        cat_cols = [p for p in profiles if p["type"] == "categorical"]
        date_cols = [p for p in profiles if p["type"] == "datetime"]
        cols_with_missing = [p for p in profiles if p["missing"] > 0]
        cols_with_outliers = [p for p in numeric_cols if p.get("outliers", 0) > 0]

        return {
            "numeric_cols": len(numeric_cols),
            "categorical_cols": len(cat_cols),
            "datetime_cols": len(date_cols),
            "cols_with_missing": len(cols_with_missing),
            "cols_with_outliers": len(cols_with_outliers),
        }


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _infer_type(series: pd.Series) -> str:
    # Try numeric
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    num = pd.to_numeric(series.dropna(), errors="coerce")
    if num.notna().sum() / max(len(series.dropna()), 1) > 0.8:
        return "numeric"
    # Try datetime
    if series.dropna().astype(str).str.match(
        r"\d{4}[-/]\d{2}[-/]\d{2}"
    ).mean() > 0.5:
        return "datetime"
    # Try boolean
    uniq = set(series.dropna().astype(str).str.lower().unique())
    if uniq <= {"true", "false", "yes", "no", "1", "0"}:
        return "boolean"
    return "categorical"


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
