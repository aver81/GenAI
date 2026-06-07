from __future__ import annotations

import re


FORBIDDEN_KEYWORDS = {
    "alter",
    "attach",
    "copy",
    "create",
    "delete",
    "detach",
    "drop",
    "insert",
    "install",
    "load",
    "pragma",
    "replace",
    "set",
    "truncate",
    "update",
}


class SQLValidationError(ValueError):
    pass


def clean_sql(sql: str) -> str:
    cleaned = sql.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned.rstrip(";").strip()


def validate_select_sql(sql: str, table_name: str = "events") -> str:
    cleaned = clean_sql(sql)
    if not cleaned:
        raise SQLValidationError("Generated SQL is empty.")
    if ";" in cleaned:
        raise SQLValidationError("Only one SQL statement is allowed.")
    if not re.match(r"^\s*(select|with)\b", cleaned, flags=re.IGNORECASE):
        raise SQLValidationError("Only read-only SELECT queries are allowed.")

    tokens = {token.lower() for token in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", cleaned)}
    blocked = sorted(tokens.intersection(FORBIDDEN_KEYWORDS))
    if blocked:
        raise SQLValidationError(f"Forbidden SQL keyword used: {', '.join(blocked)}.")

    referenced_tables = _referenced_tables(cleaned)
    invalid_tables = sorted(table for table in referenced_tables if table.lower() != table_name.lower())
    if invalid_tables:
        raise SQLValidationError(f"Query can only reference table '{table_name}'.")
    if table_name.lower() not in {table.lower() for table in referenced_tables}:
        raise SQLValidationError(f"Query must reference table '{table_name}'.")
    return cleaned


def _referenced_tables(sql: str) -> set[str]:
    matches = re.findall(
        r"\b(?:from|join)\s+([\"`]?)([a-zA-Z_][a-zA-Z0-9_]*)\1",
        sql,
        flags=re.IGNORECASE,
    )
    return {match[1] for match in matches}

