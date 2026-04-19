# F1 Expert Chatbot

This project is a V1 notebook-based Formula 1 question-answering prototype. It uses a LangGraph pipeline to turn a natural-language F1 question into a SQL query, execute that query against a local SQLite database, and summarize the result with an LLM.

The main workflow lives in `main.ipynb`.

## What It Does

The notebook builds a simple multi-step pipeline:

```text
User question
-> Generate SQL query
-> Execute SQL against local SQLite database
-> Summarize SQL result
-> Return final answer
```

Example question:

```text
tell me who won the 2023 italian GP
```

Example output:

```text
Based on the race data, Max Verstappen won the 2023 Italian GP.
```

## Project Files

- `main.ipynb`: Main LangGraph chatbot notebook.
- `data_cleaning.ipynb`: Supporting notebook for data preparation.
- `f1_data.db`: Local SQLite database generated from the CSV files.
- `requirements.txt`: Python package requirements.
- `*.csv`: Formula 1 source tables used to populate SQLite.

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
2. Run the cells from top to bottom.
3. The notebook loads the CSV files into `f1_data.db`.
4. It builds schema context from the SQLite tables.
5. It compiles the LangGraph pipeline.
6. It invokes the graph with a sample F1 question.

The sample invocation is:

```python
result = graph.invoke({"user_query": "tell me who won the 2023 italian GP"})
```

The final response is available in:

```python
result["summary"]
```

## Pipeline Design

The graph state is defined as:

```python
class State(TypedDict):
    user_query: str
    sql_code: str
    sql_code_answer: str
    summary: str
```

The pipeline has three LangGraph nodes:

- `query_generator`: Converts the user's natural-language question into SQL.
- `run_sqlite_query`: Executes the generated SQL against `f1_data.db`.
- `summarizer`: Converts the SQL query and SQL result into a natural-language answer.

The graph wiring is:

```text
query generator -> sqlite3 generator -> summarization -> END
```

## Notes On The V1 Design

This V1 uses plain LangGraph node functions. It does not use LangChain `@tool` wrappers for the graph nodes.

The SQL generator receives table schema information from the local SQLite database and asks the LLM to produce SQL only. The SQL result is then passed to the summarizer, which is instructed to answer using only the data returned by SQLite.

## Current Limitations

- SQL generation depends on the LLM producing valid SQLite syntax.
- The generated SQL is executed directly against the local database.
- The notebook is a prototype, not a packaged application.
- The state type marks `sql_code_answer` as a string, but successful SQL results are returned as Python row tuples.
- The CSV-to-SQLite loading step runs in the notebook and may overwrite existing SQLite tables.

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

