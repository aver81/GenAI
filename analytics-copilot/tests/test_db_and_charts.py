import pandas as pd

from analytics_copilot.charts import validate_chart_plan
from analytics_copilot.db import create_connection, run_query
from analytics_copilot.models import ChartPlan
from analytics_copilot.sql_validation import validate_select_sql


def test_runs_validated_duckdb_query():
    df = pd.DataFrame(
        {
            "user_id": ["u1", "u2", "u1"],
            "event_name": ["signup", "signup", "purchase"],
        }
    )
    connection = create_connection(df)
    sql = validate_select_sql(
        "SELECT event_name, count(*) AS events FROM events GROUP BY event_name"
    )

    result = run_query(connection, sql)

    assert set(result.dataframe["event_name"]) == {"signup", "purchase"}
    assert result.elapsed_seconds >= 0


def test_validate_chart_plan_honors_intended_metric_column():
    df = pd.DataFrame(
        {
            "platform": ["ios", "android"],
            "impressions": [1000, 2000],
            "clicks": [100, 150],
            "ctr": [0.10, 0.075],
        }
    )
    plan = ChartPlan(chart_type="bar", x="platform", y="ctr", title="CTR by platform")

    spec = validate_chart_plan(plan, df)

    assert spec.kind == "bar"
    assert spec.x == "platform"
    assert spec.y == "ctr"


def test_validate_chart_plan_falls_back_for_invalid_y_column():
    df = pd.DataFrame({"platform": ["ios", "android"], "ctr": [0.10, 0.075]})
    plan = ChartPlan(chart_type="bar", x="platform", y="missing_metric")

    spec = validate_chart_plan(plan, df)

    assert spec.kind == "table"
    assert "missing_metric" in spec.warning
