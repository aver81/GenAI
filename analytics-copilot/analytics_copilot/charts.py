from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.express as px

from analytics_copilot.models import ChartPlan


@dataclass(frozen=True)
class ChartSpec:
    kind: str
    x: str | None = None
    y: str | None = None
    title: str = ""
    x_axis_label: str | None = None
    y_axis_label: str | None = None
    warning: str | None = None


SUPPORTED_CHARTS = {"bar", "line", "scatter", "table"}


def validate_chart_plan(plan: ChartPlan, df: pd.DataFrame) -> ChartSpec:
    chart_type = plan.chart_type.lower().strip()
    if chart_type not in SUPPORTED_CHARTS:
        return ChartSpec(kind="table", warning=f"Unsupported chart type: {plan.chart_type}.")
    if chart_type == "table":
        return ChartSpec(kind="table", title=plan.title)
    if df.empty:
        return ChartSpec(kind="table", warning="Cannot chart an empty result.")
    if not plan.x or plan.x not in df.columns:
        return ChartSpec(kind="table", warning=f"Chart x column is missing from result: {plan.x}.")
    if not plan.y or plan.y not in df.columns:
        return ChartSpec(kind="table", warning=f"Chart y column is missing from result: {plan.y}.")
    if chart_type in {"bar", "line", "scatter"} and not pd.api.types.is_numeric_dtype(df[plan.y]):
        return ChartSpec(kind="table", warning=f"Chart y column must be numeric: {plan.y}.")
    return ChartSpec(
        kind=chart_type,
        x=plan.x,
        y=plan.y,
        title=plan.title,
        x_axis_label=plan.x_axis_label,
        y_axis_label=plan.y_axis_label,
    )


def build_chart(df: pd.DataFrame, spec: ChartSpec):
    if spec.kind == "line" and spec.x and spec.y:
        chart_df = df.copy()
        chart_df[spec.x] = pd.to_datetime(chart_df[spec.x], errors="coerce")
        return px.line(
            chart_df,
            x=spec.x,
            y=spec.y,
            markers=True,
            title=spec.title or None,
            labels=_labels(spec),
        )
    if spec.kind == "bar" and spec.x and spec.y:
        return px.bar(df, x=spec.x, y=spec.y, title=spec.title or None, labels=_labels(spec))
    if spec.kind == "scatter" and spec.x and spec.y:
        return px.scatter(df, x=spec.x, y=spec.y, title=spec.title or None, labels=_labels(spec))
    return None


def _labels(spec: ChartSpec) -> dict[str, str]:
    labels = {}
    if spec.x and spec.x_axis_label:
        labels[spec.x] = spec.x_axis_label
    if spec.y and spec.y_axis_label:
        labels[spec.y] = spec.y_axis_label
    return labels
