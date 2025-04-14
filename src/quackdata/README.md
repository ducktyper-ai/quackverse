# 🧮 QuackData

**QuackData** is the QuackVerse module for working with databases, analytics warehouses, and structured data APIs. It provides high-level, developer-friendly functions to automate workflows across services like SQLite, BigQuery, and Supabase.

---

## 📌 Purpose

QuackData is designed to:
- Help developers automate data ingestion, extraction, and transformation
- Provide a clean interface for building data-powered QuackTools
- Abstract low-level service calls into simple, testable utilities

---

## 📦 Folder Structure

```
src/quackdata/
├── __init__.py
├── jupytext.py           # Convert Notebooks to plain code and viceversa
├── sqlite.py             # Lightweight local DB support
├── bigquery.py           # Google BigQuery read/write tools
├── supabase.py           # Supabase database and API sync
└── plugins.py            # Integration plugin registration
```

---

## 🔌 Plugin Registration

QuackData registers integrations via the `quackcore` plugin interface:

```python
from quackcore.integrations.core import register_plugin

@register_plugin("sqlite")
def register_sqlite():
    return SQLiteIntegration()
```

---

## 💡 Example Use

```python
from quackdata.sqlite import execute_query

rows = execute_query("SELECT * FROM users WHERE active = 1")
for row in rows:
    print(row["name"])
```

Or upload a Pandas DataFrame to BigQuery:

```python
from quackdata.bigquery import upload_dataframe

upload_dataframe(df, dataset="quack", table="logs")
```

---

## 🔄 Integration Sources

Each service uses internal logic from `integrations/` to manage:
- Credentials
- HTTP/SDK operations
- Query formatting and result handling

All low-level adapters live outside this folder and are wrapped here.

---

## 🧪 Tests

Unit tests live in `tests/quackdata/`. Use mocks for service access (e.g., `mock_bigquery()`, `mock_sqlite()`).

---

## ✅ When to Use

Use `quackdata` if you're building:
- A data-heavy QuackTool
- An analytics or ETL pipeline
- A productivity automation tool involving structured storage or logs

---

## 🧭 Design Principles

QuackData functions should:
- Be minimal, focused, and callable without boilerplate
- Return typed results or standard dict/list structures
- Avoid direct CLI logic or interactive prompts

---

## 🛠 Future Extensions

Potential expansions:
- Support for DuckDB
- Integration with Postgres via Supabase
- Data catalog querying (e.g. dbt, metadata APIs)

---

Let QuackData turn your data into ducks — fast, clean, and easy. 🦆📊