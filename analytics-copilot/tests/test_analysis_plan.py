from analytics_copilot.llm import parse_analysis_plan


def test_parse_analysis_plan_from_llm_json():
    plan = parse_analysis_plan(
        """
        {
          "sql": "SELECT platform, SUM(clicks) * 1.0 / NULLIF(SUM(impressions), 0) AS ctr FROM events GROUP BY platform",
          "metric_name": "CTR",
          "metric_source": "calculated",
          "metric_reason": "Computed at platform grain from available columns.",
          "chart": {
            "chart_type": "bar",
            "x": "platform",
            "y": "ctr",
            "title": "CTR by Platform",
            "x_axis_label": "Platform",
            "y_axis_label": "CTR"
          },
          "assumptions": ["Aggregated numerator and denominator before division."],
          "warnings": []
        }
        """
    )

    assert plan.metric_name == "CTR"
    assert plan.metric_source == "calculated"
    assert plan.chart.chart_type == "bar"
    assert plan.chart.x == "platform"
    assert plan.chart.y == "ctr"
    assert plan.assumptions == ["Aggregated numerator and denominator before division."]
