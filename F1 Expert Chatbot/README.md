# F1 Expert Chatbot

This project is a notebook-based Formula 1 question-answering prototype. It uses a local SQLite database, LangGraph, and an LLM to convert natural-language F1 questions into SQL queries, execute those queries, and summarize the results.

The main workflow lives in `main.ipynb`.

## What It Does

The notebook currently contains two versions of the pipeline:

- **Version 1**: A simple linear SQL question-answering pipeline.
- **Version 2**: An intent-routed pipeline with separate paths for factual lookup, deeper analysis, and hybrid questions.

At a high level, both versions follow this pattern:

```text
User question
-> Generate SQL query
-> Execute SQL against local SQLite database
-> Summarize SQL result
-> Return final answer
```

Version 2 adds an intent-classification step before SQL generation:

```text
User question
-> Classify intent
-> Route to factual lookup, deep analysis, or hybrid SQL generation
-> Execute SQL
-> Produce polished summary
-> Return final answer
```

## Project Files

- `main.ipynb`: Main notebook containing data loading, schema extraction, V1 pipeline, and V2 pipeline.
- `f1_data.db`: Local SQLite database generated from the CSV files.
- `requirements.txt`: Python package requirements.
- `data/*.csv`: Formula 1 source data used to populate SQLite.

Key CSV files include:

- `races.csv`
- `results.csv`
- `drivers.csv`
- `constructors.csv`
- `circuits.csv`
- `lap_times.csv`
- `pit_stops.csv`
- `qualifying.csv`
- `driver_standings.csv`
- `constructor_standings.csv`
- `status.csv`

## Requirements

Install dependencies from:

```powershell
pip install -r requirements.txt
```

The notebook expects a Groq API key. Add it to a `.env` file:

```text
GROQ_API_KEY=your_groq_api_key_here
```

If the environment variable is not present, the notebook prompts for it interactively.

## How To Run

1. Open `main.ipynb` in Jupyter or VS Code.
2. Run the setup cells from the top of the notebook.
3. The notebook loads CSV data from `data/` into `f1_data.db`.
4. It builds schema context from the SQLite tables.
5. Run either the Version 1 or Version 2 graph cells.
6. Invoke the graph with a natural-language F1 question.

Example:

```python
result = graph.invoke({"user_query": "analyze norris's performance in 2024 season"})
```

To view the final answer cleanly, print only the summary:

```python
print(result["summary"])
```

Displaying the whole `result` dictionary may show escaped characters and raw Python tuple output.

## Version 1: Linear SQL QA Pipeline

Version 1 is the original multi-table SQLite LangGraph pipeline.

### State

```python
class State(TypedDict):
    user_query: str
    sql_code: str
    sql_code_answer: str
    summary: str
```

### Nodes

- `query_generator`: Converts the user's natural-language question into SQL.
- `run_sqlite_query`: Executes the generated SQL against `f1_data.db`.
- `summarizer`: Converts the SQL query and SQL result into a natural-language answer.

### Graph

```text
query generator -> sqlite3 generator -> summarization -> END
```

Version 1 is useful as a simple baseline because it has one SQL-generation path and one summarization path.

## Version 2: Intent-Routed SQL QA Pipeline

Version 2 expands the original design by adding intent classification, multiple SQL-generation paths, structured output schemas, and a more controlled final-response prompt.

### Main Updates

- Added an **intent classifier** before SQL generation.
- Added three intent categories:
  - `Factual Lookup`
  - `Deep Analysis`
  - `Hybrid`
- Added separate graph nodes for factual, deep-analysis, and hybrid SQL generation.
- Added Pydantic `BaseModel` schemas for structured LLM responses.
- Updated the graph state to include `intent` and `sql_code_answer`.
- Updated the final summary prompt to include the actual SQL result.
- Added readability rules for summaries:
  - use only the SQL result as the source of truth
  - avoid inventing race names, team names, teammate names, causes, or comparisons
  - do not reproduce large SQL result tables in full
  - summarize SQL results with more than 8 rows
  - keep Markdown tables to at most 6 rows
  - use plain ASCII spacing and punctuation where possible

### State

```python
class State(TypedDict):
    user_query: str
    intent: str
    sql_code: str
    sql_code_answer: str
    summary: str
```

### Intent Classification

The `intent_classifier` node classifies the user question into one of three categories:

- **Factual Lookup**: A single verifiable answer, such as "Who won the 2023 Italian GP?"
- **Deep Analysis**: A trend, comparison, or performance analysis, such as "Analyze Norris's 2024 season."
- **Hybrid**: A factual lookup plus some analysis in the same question.

The classifier uses a Pydantic schema:

```python
class intent_classification(BaseModel):
    user_query: str
    intent: Literal["Factual Lookup", "Deep Analysis", "Hybrid"]
```

### SQL Generation Nodes

Version 2 has three SQL-generation nodes:

- `factual_lookup`: Generates SQL for direct factual questions.
- `deep_analysis`: Generates SQL for analytical or comparative questions.
- `hybrid_response`: Generates SQL for questions that combine lookup and analysis.

The factual and deep-analysis paths use structured output with a schema containing `sql_code`.

### SQL Execution

The shared `run_sqlite_query` node executes the generated SQL:

```text
Generated SQL -> SQLite cursor -> fetched rows -> sql_code_answer
```

Successful results are returned as Python row tuples. SQL errors are returned as an error string in `sql_code_answer`.

### Polished Response

The `polished_response` node receives:

- user question
- classified intent
- generated SQL query
- SQL query answer

The summary prompt is designed to keep the output readable and grounded. For deep analysis, the requested structure is:

```text
## Summary
One direct paragraph of 2-3 sentences.

## Key Metrics
A compact Markdown table with at most 6 rows.

## Highlights
3-5 bullets summarizing the most important patterns.

## Caveat
One sentence explaining what the SQL result does not cover.
```

This avoids dumping long race-by-race tables into the final summary while still preserving the important metrics and patterns.

### Graph

```text
intent classifier
-> factual lookup OR deep analysis OR hybrid
-> sqlite3 generator
-> summarization
-> END
```

The conditional routing is:

```python
builder.add_conditional_edges(
    "intent classifier",
    routing_decision,
    {
        0: "factual lookup",
        1: "deep analysis",
        2: "hybrid",
    },
)
```

## Example V2 Question

```python
result = graph.invoke({"user_query": "analyze norris's performance in 2024 season"})
print(result["summary"])
```

The graph classifies the query as `Deep Analysis`, generates SQL for Norris's 2024 race results, executes it against SQLite, and returns a compact analytical summary instead of a full 24-row race table.

## Current Limitations

- SQL generation depends on the LLM producing valid SQLite syntax.
- Generated SQL is executed directly against the local database.
- The notebook is a prototype, not a packaged application.
- The CSV-to-SQLite loading step runs inside the notebook and may overwrite existing SQLite tables.
- Successful SQL results are Python tuples, so the summarizer must infer column meaning from the SQL query and row order.
- Long raw `result` dictionaries can be hard to read in notebook output; prefer `print(result["summary"])`.
- The model may still make arithmetic or labeling mistakes if the SQL result is ambiguous.
- For race statistics, fields such as `positionorder` are often safer than casting the text `position` column.

## Dependencies

The project currently lists:

```text
numpy
pandas
seaborn
langchain
langchain-community
langgraph
ipykernel
langchain-groq
langchain-openai
```
