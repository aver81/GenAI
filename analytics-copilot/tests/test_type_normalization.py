import pandas as pd

from analytics_copilot.schema import infer_schema
from analytics_copilot.type_normalization import normalize_dataframe_for_query


def test_normalizes_date_and_numeric_strings_for_query():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-08", "2026-01-15"],
            "engagement_rate": ["10%", "12.5%", "8%"],
            "impressions": ["1,000", "2,500", "3,000"],
            "campaign": ["A", "B", "C"],
        }
    )

    normalized = normalize_dataframe_for_query(df)

    assert str(normalized.query_df["date"].dtype).startswith("datetime64")
    assert normalized.query_df["engagement_rate"].tolist() == [0.10, 0.125, 0.08]
    assert normalized.query_df["impressions"].tolist() == [1000, 2500, 3000]
    assert normalized.query_df["campaign"].tolist() == ["A", "B", "C"]


def test_schema_prompt_mentions_converted_columns():
    df = pd.DataFrame({"date": ["2026-01-01", "2026-01-08"], "value": ["1", "2"]})
    normalized = normalize_dataframe_for_query(df)

    schema = infer_schema(
        normalized.query_df,
        normalization_profiles=normalized.column_profiles,
    )

    prompt = schema.to_prompt_text()
    assert "converted_from=object" in prompt
    assert "parse_success=100%" in prompt


def test_mixed_text_column_is_not_converted():
    df = pd.DataFrame({"label": ["north", "south", "unknown"], "value": ["1", "2", "3"]})

    normalized = normalize_dataframe_for_query(df)

    label_profile = next(profile for profile in normalized.column_profiles if profile.name == "label")
    assert label_profile.conversion_applied is False
    assert label_profile.semantic_type == "text"

