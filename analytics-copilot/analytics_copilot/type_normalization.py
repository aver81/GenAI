from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from typing import Any

import pandas as pd


PARSE_THRESHOLD = 0.85


@dataclass(frozen=True)
class ColumnTypeProfile:
    name: str
    original_dtype: str
    query_dtype: str
    semantic_type: str
    conversion_applied: bool
    parse_success_rate: float
    examples_failed: list[str]


@dataclass(frozen=True)
class NormalizedDataFrame:
    display_df: pd.DataFrame
    query_df: pd.DataFrame
    column_profiles: list[ColumnTypeProfile]
    warnings: list[str]

    def as_records(self) -> list[dict[str, Any]]:
        return [
            {
                "column": profile.name,
                "original_dtype": profile.original_dtype,
                "query_dtype": profile.query_dtype,
                "semantic_type": profile.semantic_type,
                "conversion_applied": profile.conversion_applied,
                "parse_success_rate": round(profile.parse_success_rate, 3),
                "examples_failed": ", ".join(profile.examples_failed),
            }
            for profile in self.column_profiles
        ]


def normalize_dataframe_for_query(df: pd.DataFrame) -> NormalizedDataFrame:
    query_df = df.copy()
    profiles: list[ColumnTypeProfile] = []
    warnings: list[str] = []

    for column in query_df.columns:
        original = query_df[column]
        converted, profile = _normalize_series(column, original)
        query_df[column] = converted
        profiles.append(profile)
        if profile.conversion_applied and profile.parse_success_rate < 1:
            warnings.append(
                f"{column}: converted to {profile.semantic_type} with "
                f"{profile.parse_success_rate:.0%} parse success."
            )

    return NormalizedDataFrame(
        display_df=df,
        query_df=query_df,
        column_profiles=profiles,
        warnings=warnings,
    )


def _normalize_series(name: str, series: pd.Series) -> tuple[pd.Series, ColumnTypeProfile]:
    original_dtype = str(series.dtype)
    if not pd.api.types.is_object_dtype(series) and not pd.api.types.is_string_dtype(series):
        return series, ColumnTypeProfile(
            name=name,
            original_dtype=original_dtype,
            query_dtype=str(series.dtype),
            semantic_type=_semantic_type_for_native(series),
            conversion_applied=False,
            parse_success_rate=1.0,
            examples_failed=[],
        )

    non_null = series.dropna()
    if non_null.empty:
        return series, _profile(name, original_dtype, str(series.dtype), "text", False, 0.0, [])

    bool_converted, bool_rate, bool_failed = _try_bool(series)
    if bool_rate >= PARSE_THRESHOLD:
        return bool_converted, _profile(name, original_dtype, str(bool_converted.dtype), "boolean", True, bool_rate, bool_failed)

    numeric_converted, numeric_rate, numeric_failed = _try_numeric(series)
    if numeric_rate >= PARSE_THRESHOLD:
        return numeric_converted, _profile(name, original_dtype, str(numeric_converted.dtype), "number", True, numeric_rate, numeric_failed)

    datetime_converted, datetime_rate, datetime_failed = _try_datetime(series)
    if datetime_rate >= PARSE_THRESHOLD:
        return datetime_converted, _profile(
            name,
            original_dtype,
            str(datetime_converted.dtype),
            "timestamp",
            True,
            datetime_rate,
            datetime_failed,
        )

    return series, _profile(name, original_dtype, str(series.dtype), "text", False, 0.0, [])


def _try_bool(series: pd.Series) -> tuple[pd.Series, float, list[str]]:
    mapping = {
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "y": True,
        "n": False,
    }
    text = series.astype("string").str.strip().str.lower()
    parsed = text.map(mapping)
    return parsed.astype("boolean"), _success_rate(series, parsed), _failed_examples(series, parsed)


def _try_numeric(series: pd.Series) -> tuple[pd.Series, float, list[str]]:
    text = series.astype("string").str.strip()
    percent_mask = text.str.endswith("%", na=False)
    cleaned = (
        text.str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .map(_strip_numeric_prefix)
    )
    parsed = pd.to_numeric(cleaned, errors="coerce")
    parsed = parsed.mask(percent_mask, parsed / 100.0)
    return parsed, _success_rate(series, parsed), _failed_examples(series, parsed)


def _strip_numeric_prefix(value: str | object) -> str | object:
    if not isinstance(value, str):
        return value
    return re.sub(r"^[^0-9+\-.]+", "", value)


def _try_datetime(series: pd.Series) -> tuple[pd.Series, float, list[str]]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = pd.to_datetime(series, errors="coerce")
    return parsed, _success_rate(series, parsed), _failed_examples(series, parsed)


def _success_rate(original: pd.Series, parsed: pd.Series) -> float:
    non_null_mask = original.notna()
    total = int(non_null_mask.sum())
    if total == 0:
        return 0.0
    return float(parsed[non_null_mask].notna().sum() / total)


def _failed_examples(original: pd.Series, parsed: pd.Series) -> list[str]:
    failed = original[original.notna() & parsed.isna()].astype(str).head(5).tolist()
    return failed


def _semantic_type_for_native(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "timestamp"
    return "text"


def _profile(
    name: str,
    original_dtype: str,
    query_dtype: str,
    semantic_type: str,
    conversion_applied: bool,
    parse_success_rate: float,
    examples_failed: list[str],
) -> ColumnTypeProfile:
    return ColumnTypeProfile(
        name=name,
        original_dtype=original_dtype,
        query_dtype=query_dtype,
        semantic_type=semantic_type,
        conversion_applied=conversion_applied,
        parse_success_rate=parse_success_rate,
        examples_failed=examples_failed,
    )
