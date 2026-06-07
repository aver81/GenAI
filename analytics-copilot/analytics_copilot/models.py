from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChartPlan:
    chart_type: str
    x: str | None = None
    y: str | None = None
    title: str = ""
    x_axis_label: str | None = None
    y_axis_label: str | None = None


@dataclass(frozen=True)
class AnalysisPlan:
    sql: str
    metric_name: str
    metric_source: str
    metric_reason: str
    chart: ChartPlan
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
