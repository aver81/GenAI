from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd
import streamlit as st

from analytics_copilot.charts import build_chart, validate_chart_plan
from analytics_copilot.db import create_connection, run_query
from analytics_copilot.llm import generate_analysis_plan, repair_analysis_plan
from analytics_copilot.models import AnalysisPlan
from analytics_copilot.schema import infer_schema
from analytics_copilot.sql_validation import SQLValidationError, validate_select_sql
from analytics_copilot.tracing import TraceLog
from analytics_copilot.type_normalization import normalize_dataframe_for_query


TABLE_NAME = "events"


@dataclass(frozen=True)
class ExecutionResult:
    query_result: object
    plan: AnalysisPlan
    sql: str


def _store_trace(trace: TraceLog) -> None:
    if "traces" not in st.session_state:
        st.session_state["traces"] = []
    st.session_state["traces"].insert(0, trace)
    st.session_state["traces"] = st.session_state["traces"][:10]


def _render_trace(trace: TraceLog) -> None:
    with st.expander(f"Trace {trace.trace_id}", expanded=False):
        st.dataframe(pd.DataFrame(trace.as_records()), use_container_width=True)
        st.json(trace.as_records())


def _run_analysis(question: str, df: pd.DataFrame, table_schema) -> None:
    trace = TraceLog()
    try:
        with st.spinner("Planning analysis..."):
            with trace.step("analysis.plan_llm", question=question) as event:
                plan = generate_analysis_plan(question, table_schema)
                event.outputs = {
                    "sql": plan.sql,
                    "metric_name": plan.metric_name,
                    "metric_source": plan.metric_source,
                    "metric_reason": plan.metric_reason,
                    "chart": asdict(plan.chart),
                    "assumptions": plan.assumptions,
                    "warnings": plan.warnings,
                }
            with trace.step("sql.validate", sql=plan.sql) as event:
                validated_sql = validate_select_sql(plan.sql, table_name=TABLE_NAME)
                event.outputs = {"validated_sql": validated_sql}

        with st.spinner("Running query..."):
            result = _execute_with_one_repair(
                question=question,
                df=df,
                table_schema=table_schema,
                plan=plan,
                validated_sql=validated_sql,
                trace=trace,
            )

        active_plan = result.plan
        query_result = result.query_result

        with trace.step("chart.validate", chart=asdict(active_plan.chart)) as event:
            chart_spec = validate_chart_plan(active_plan.chart, query_result.dataframe)
            event.outputs = asdict(chart_spec)

        if active_plan.assumptions:
            st.info("Assumptions: " + " ".join(active_plan.assumptions))
        if active_plan.warnings:
            st.warning(" ".join(active_plan.warnings))
        if chart_spec.warning:
            st.warning(f"Chart fallback: {chart_spec.warning}")

        st.subheader("Generated SQL")
        st.code(result.sql, language="sql")

        st.caption(f"{len(query_result.dataframe):,} rows returned in {query_result.elapsed_seconds:.2f} seconds.")
        if query_result.dataframe.empty:
            st.info("The query ran successfully but returned no rows.")
            return

        chart = build_chart(query_result.dataframe, chart_spec)
        if chart is not None:
            st.subheader("Chart")
            st.plotly_chart(chart, use_container_width=True)

        st.subheader("Results")
        st.dataframe(query_result.dataframe, use_container_width=True)
    finally:
        _store_trace(trace)


def _execute_with_one_repair(
    question: str,
    df: pd.DataFrame,
    table_schema,
    plan,
    validated_sql: str,
    trace: TraceLog,
) -> ExecutionResult:
    try:
        with trace.step("sql.duckdb_execute", sql=validated_sql, input_rows=len(df)) as event:
            connection = create_connection(df, table_name=TABLE_NAME)
            query_result = run_query(connection, validated_sql)
            event.outputs = {
                "rows": len(query_result.dataframe),
                "columns": list(query_result.dataframe.columns),
                "duckdb_elapsed_seconds": query_result.elapsed_seconds,
                "repaired": False,
            }
        return ExecutionResult(query_result=query_result, plan=plan, sql=validated_sql)
    except Exception as exc:
        error = str(exc)
        trace.add_event(
            "sql.repair_triggered",
            status="ok",
            inputs={"failed_sql": validated_sql},
            outputs={"error": error},
        )

    with trace.step("analysis.repair_llm", question=question, failed_sql=validated_sql) as event:
        repaired_plan = repair_analysis_plan(question, table_schema, plan, error)
        event.outputs = {
            "sql": repaired_plan.sql,
            "metric_name": repaired_plan.metric_name,
            "chart": asdict(repaired_plan.chart),
        }
    with trace.step("sql.validate_repaired", sql=repaired_plan.sql) as event:
        repaired_sql = validate_select_sql(repaired_plan.sql, table_name=TABLE_NAME)
        event.outputs = {"validated_sql": repaired_sql}
    with trace.step("sql.duckdb_execute_repaired", sql=repaired_sql, input_rows=len(df)) as event:
        connection = create_connection(df, table_name=TABLE_NAME)
        query_result = run_query(connection, repaired_sql)
        event.outputs = {
            "rows": len(query_result.dataframe),
            "columns": list(query_result.dataframe.columns),
            "duckdb_elapsed_seconds": query_result.elapsed_seconds,
            "repaired": True,
        }
    return ExecutionResult(query_result=query_result, plan=repaired_plan, sql=repaired_sql)


st.set_page_config(page_title="AI Product Analytics Copilot", layout="wide")
st.title("AI Product Analytics Copilot")

uploaded_file = st.file_uploader("Upload event CSV", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV to start asking product analytics questions.")
    st.stop()

try:
    dataframe = pd.read_csv(uploaded_file)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}")
    st.stop()

if dataframe.empty:
    st.warning("The uploaded CSV has no rows.")
    st.stop()

normalized = normalize_dataframe_for_query(dataframe)
query_dataframe = normalized.query_df
schema = infer_schema(query_dataframe, table_name=TABLE_NAME, normalization_profiles=normalized.column_profiles)

analysis_tab, trace_tab = st.tabs(["Analysis", "Traces"])

with analysis_tab:
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Dataset preview")
        st.dataframe(dataframe.head(50), use_container_width=True)
    with right:
        st.subheader("Schema")
        st.dataframe(pd.DataFrame(schema.as_records()), use_container_width=True)

    question = st.text_input(
        "Ask a question",
        placeholder="Example: Analyze CTR platform-wise",
    )

    if st.button("Run analysis", type="primary", disabled=not question):
        try:
            _run_analysis(question, query_dataframe, schema)
        except SQLValidationError as exc:
            st.error(f"Generated SQL was rejected: {exc}")
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")

with trace_tab:
    st.subheader("Type normalization")
    st.caption(
        "The app keeps your uploaded CSV unchanged for preview, but queries run against "
        "a normalized copy where obvious dates, numbers, percents, and booleans are parsed."
    )
    st.dataframe(pd.DataFrame(normalized.as_records()), use_container_width=True)
    if normalized.warnings:
        st.warning(" ".join(normalized.warnings))

    st.subheader("Recent traces")
    traces = st.session_state.get("traces", [])
    if not traces:
        st.info("Run an analysis to collect traces.")
    for trace in traces:
        _render_trace(trace)
