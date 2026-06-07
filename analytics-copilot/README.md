# AI Product Analytics Copilot

Local MVP for PMs and growth teams to upload event data, ask questions without
writing SQL, and inspect SQL-backed answers with tables and charts.

## Tech

- Streamlit
- DuckDB
- Direct LLM API call
- Plotly

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OPENAI_API_KEY="your_api_key_here"
streamlit run app.py
```

Optional:

```powershell
$env:OPENAI_MODEL="gpt-4o-mini"
```

## MVP Flow

1. Upload one CSV.
2. Review the detected schema and sample rows.
3. Ask a product analytics question.
4. The app normalizes obvious query types while keeping the raw preview unchanged.
5. The LLM returns a structured analysis plan: SQL, metric intent, and chart intent.
6. DuckDB executes the validated SQL against the normalized query table.
7. The app validates the chart plan against the query result.
8. View the metric explanation, generated SQL, chart, table, warnings, and trace.

## Type Normalization

The uploaded CSV is shown as-is, but queries run against a normalized copy. The
normalizer conservatively converts columns when at least 85% of non-null values
parse as a stronger type:

- text dates -> timestamps
- numeric strings -> numbers
- percent strings -> decimal rates
- comma/currency formatted numbers -> numbers
- true/false style strings -> booleans

The schema prompt includes conversion details so the LLM reasons over the actual
DuckDB query types. The app also shows a `Type normalization` expander with parse
success rates and examples that failed conversion.

## Structured Analysis Plans

The app no longer guesses chart columns from the first numeric result column. The
LLM must specify which result column represents the requested metric and which
columns to visualize.

```json
{
  "sql": "SELECT platform, SUM(clicks) * 1.0 / NULLIF(SUM(impressions), 0) AS ctr FROM events GROUP BY platform",
  "metric_name": "CTR",
  "metric_source": "calculated",
  "metric_reason": "Computed at platform grain from available columns.",
  "chart": {
    "chart_type": "bar",
    "x": "platform",
    "y": "ctr",
    "title": "CTR by Platform"
  },
  "assumptions": [],
  "warnings": []
}
```

Python validates the SQL and chart plan. If DuckDB execution fails, the app asks
the LLM for one repaired analysis plan using the error message and schema, then
validates and executes that repaired SQL once. If the chart plan is invalid, the
app falls back safely and records the reason in the trace.

## Tracing

The app keeps lightweight in-memory traces for recent runs. Each trace records
major steps, timing, compact inputs/outputs, generated SQL, DuckDB row counts,
chart validation, and errors.

## Evaluation Seed

Use `benchmarks/events_sample.csv` and `benchmarks/questions.json` as the first
benchmark seed for tracking SQL execution, answer quality, chart quality, and
response time against the PRD goals of 80% benchmark accuracy and under 10
seconds.
