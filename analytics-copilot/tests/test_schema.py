import pandas as pd

from analytics_copilot.schema import infer_schema


def test_infer_schema_detects_types_and_timestamp_hint():
    df = pd.DataFrame(
        {
            "user_id": ["u1", "u2"],
            "event_time": ["2026-01-01 09:00:00", "2026-01-02 10:00:00"],
            "count": [1, 2],
            "converted": [True, False],
        }
    )

    schema = infer_schema(df)

    columns = {column.name: column for column in schema.columns}
    assert schema.row_count == 2
    assert columns["user_id"].dtype == "text"
    assert columns["event_time"].dtype == "timestamp"
    assert columns["event_time"].is_likely_timestamp is True
    assert columns["count"].dtype == "integer"
    assert columns["converted"].dtype == "boolean"

