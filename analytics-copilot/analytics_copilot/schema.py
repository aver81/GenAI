from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import warnings

import pandas as pd


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    dtype: str
    nullable: bool
    sample_values: list[str]
    is_likely_timestamp: bool
    original_dtype: str | None = None
    conversion_applied: bool = False
    parse_success_rate: float | None = None


@dataclass(frozen=True)
class TableSchema:
    table_name: str
    row_count: int
    columns: list[ColumnProfile]

    def to_prompt_text(self) -> str:
        lines = [f"Table: {self.table_name}", f"Rows: {self.row_count}", "Columns:"]
        for column in self.columns:
            samples = ", ".join(column.sample_values) if column.sample_values else "no non-null samples"
            timestamp_hint = " likely_timestamp" if column.is_likely_timestamp else ""
            conversion_hint = ""
            if column.conversion_applied:
                conversion_hint = (
                    f", converted_from={column.original_dtype}, "
                    f"parse_success={column.parse_success_rate:.0%}"
                )
            lines.append(
                f"- {column.name}: {column.dtype}, nullable={column.nullable}, "
                f"samples=[{samples}]{timestamp_hint}{conversion_hint}"
            )
        return "\n".join(lines)

    def as_records(self) -> list[dict[str, Any]]:
        return [
            {
                "column": column.name,
                "dtype": column.dtype,
                "nullable": column.nullable,
                "sample_values": ", ".join(column.sample_values),
                "likely_timestamp": column.is_likely_timestamp,
                "original_dtype": column.original_dtype,
                "conversion_applied": column.conversion_applied,
                "parse_success_rate": column.parse_success_rate,
            }
            for column in self.columns
        ]


def infer_schema(df: pd.DataFrame, table_name: str = "events", normalization_profiles=None) -> TableSchema:
    profile_by_name = {profile.name: profile for profile in normalization_profiles or []}
    columns = [_profile_column(df, name, profile_by_name.get(name)) for name in df.columns]
    return TableSchema(table_name=table_name, row_count=len(df), columns=columns)


def _profile_column(df: pd.DataFrame, name: str, normalization_profile=None) -> ColumnProfile:
    series = df[name]
    non_null = series.dropna()
    sample_values = [str(value) for value in non_null.astype(str).head(5).tolist()]
    dtype = _friendly_dtype(series)
    return ColumnProfile(
        name=name,
        dtype=dtype,
        nullable=series.isna().any(),
        sample_values=sample_values,
        is_likely_timestamp=_is_likely_timestamp(name, series),
        original_dtype=getattr(normalization_profile, "original_dtype", None),
        conversion_applied=bool(getattr(normalization_profile, "conversion_applied", False)),
        parse_success_rate=getattr(normalization_profile, "parse_success_rate", None),
    )


def _friendly_dtype(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "number"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "timestamp"
    parsed = _safe_to_datetime(series.dropna().head(50))
    if len(parsed) > 0 and parsed.notna().mean() >= 0.8:
        return "timestamp"
    return "text"


def _is_likely_timestamp(name: str, series: pd.Series) -> bool:
    lowered = name.lower()
    if any(token in lowered for token in ("time", "date", "created_at", "timestamp")):
        return True
    parsed = _safe_to_datetime(series.dropna().head(50))
    return len(parsed) > 0 and parsed.notna().mean() >= 0.8


def _safe_to_datetime(series: pd.Series) -> pd.Series:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return pd.to_datetime(series, errors="coerce")
