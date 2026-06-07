from __future__ import annotations

import json
import os

from openai import OpenAI

from analytics_copilot.models import AnalysisPlan, ChartPlan
from analytics_copilot.schema import TableSchema
from analytics_copilot.sql_validation import clean_sql


SYSTEM_PROMPT = """You create structured analysis plans for product analytics.
Return JSON only. Do not include markdown.

The plan must include DuckDB-compatible read-only SQL against only the provided table.
Also include the metric intent and visualization intent so the chart matches the user's question.

Rules:
- Use one SQL statement only.
- Prefer clear aliases for output columns.
- The chart x/y fields must refer to columns returned by the SQL.
- If the user asks for a metric that could be an existing column or a calculation, choose the better option from the schema and explain why.
- Do not hardcode assumptions about specific metric names; reason from the user question, schema, types, and samples.
- If the best answer is a table, set chart_type to "table" and x/y to null.

Return this JSON shape:
{
  "sql": "SELECT ... FROM events ...",
  "metric_name": "CTR",
  "metric_source": "calculated|existing_column|aggregate",
  "metric_reason": "Why this column/calculation represents the requested metric.",
  "chart": {
    "chart_type": "bar|line|scatter|table",
    "x": "platform",
    "y": "ctr",
    "title": "CTR by Platform",
    "x_axis_label": "Platform",
    "y_axis_label": "CTR"
  },
  "assumptions": [],
  "warnings": []
}"""


def generate_analysis_plan(question: str, schema: TableSchema, model: str | None = None) -> AnalysisPlan:
    client, model_name = _client_and_model(model)
    response = client.chat.completions.create(
        model=model_name,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{schema.to_prompt_text()}\n\n"
                    f"Question: {question}\n\n"
                    f"Create an analysis plan for table '{schema.table_name}'."
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    return parse_analysis_plan(content)


def parse_analysis_plan(content: str) -> AnalysisPlan:
    raw = json.loads(content)
    chart_raw = raw.get("chart") or {}
    chart = ChartPlan(
        chart_type=str(chart_raw.get("chart_type") or "table"),
        x=chart_raw.get("x"),
        y=chart_raw.get("y"),
        title=str(chart_raw.get("title") or ""),
        x_axis_label=chart_raw.get("x_axis_label"),
        y_axis_label=chart_raw.get("y_axis_label"),
    )
    return AnalysisPlan(
        sql=clean_sql(str(raw.get("sql") or "")),
        metric_name=str(raw.get("metric_name") or ""),
        metric_source=str(raw.get("metric_source") or "aggregate"),
        metric_reason=str(raw.get("metric_reason") or ""),
        chart=chart,
        assumptions=list(raw.get("assumptions") or []),
        warnings=list(raw.get("warnings") or []),
    )


def repair_analysis_plan(
    question: str,
    schema: TableSchema,
    failed_plan: AnalysisPlan,
    error: str,
    model: str | None = None,
) -> AnalysisPlan:
    client, model_name = _client_and_model(model)
    response = client.chat.completions.create(
        model=model_name,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "The previous analysis plan failed in DuckDB. Return a corrected "
                    "analysis plan using the same JSON shape.\n\n"
                    f"{schema.to_prompt_text()}\n\n"
                    f"Question: {question}\n\n"
                    f"Failed SQL:\n{failed_plan.sql}\n\n"
                    f"DuckDB error:\n{error}\n\n"
                    "Fix type casts, column references, aliases, and DuckDB syntax as needed. "
                    "The chart x/y fields must match the corrected SQL result columns."
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    return parse_analysis_plan(content)


def _client_and_model(model: str | None = None) -> tuple[OpenAI, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key), model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
