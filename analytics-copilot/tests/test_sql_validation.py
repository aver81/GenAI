import pytest

from analytics_copilot.sql_validation import SQLValidationError, validate_select_sql


def test_validates_select_query_against_events_table():
    sql = validate_select_sql("SELECT event_name, count(*) FROM events GROUP BY event_name;")

    assert sql == "SELECT event_name, count(*) FROM events GROUP BY event_name"


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM events",
        "SELECT * FROM events; DROP TABLE events",
        "UPDATE events SET event_name = 'x'",
        "SELECT * FROM users",
        "SELECT 1",
    ],
)
def test_rejects_unsafe_or_out_of_scope_sql(sql):
    with pytest.raises(SQLValidationError):
        validate_select_sql(sql)

