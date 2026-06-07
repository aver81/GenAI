from __future__ import annotations

import time
from dataclasses import dataclass

import duckdb
import pandas as pd


@dataclass(frozen=True)
class QueryResult:
    dataframe: pd.DataFrame
    elapsed_seconds: float


def create_connection(df: pd.DataFrame, table_name: str = "events") -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(database=":memory:")
    connection.register(table_name, df)
    return connection


def run_query(connection: duckdb.DuckDBPyConnection, sql: str) -> QueryResult:
    started = time.perf_counter()
    result = connection.execute(sql).fetchdf()
    elapsed = time.perf_counter() - started
    return QueryResult(dataframe=result, elapsed_seconds=elapsed)

