# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A small async FastAPI service for tracking books and reading notes/highlights. It also serves as the
test target for [prai](https://github.com/TODO/prai), a PR review agent — some branches in this repo
are intentional-bug or intentional-anti-pattern test fixtures created for that purpose (e.g. SQL
injection, breaking API changes, pattern deviations). When working on a branch, check whether it looks
like one of these fixtures (an explicit `WARNING: ... intentional ...` comment is the tell) before
assuming odd code is a real bug to fix.

## Commands

```bash
# setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# run the dev server (auto-creates schema on startup)
uvicorn app.main:app --reload

# apply migrations explicitly (alternative to the auto-create-on-startup behavior)
alembic upgrade head

# run the full test suite
pytest

# run a single test file / test
pytest tests/test_books.py
pytest tests/test_books.py::test_get_book_happy_path
```

There is no configured lint/format command in this repo.

## Architecture

- `app/main.py` — creates the `FastAPI` app, registers the CORS middleware, and includes routers. The
  `lifespan` handler calls `Base.metadata.create_all` on startup, so schema exists without running
  migrations first (useful for dev/tests; Alembic is still the source of truth for real schema changes).
- `app/database.py` — single shared async engine/session setup. `DATABASE_URL` env var selects the
  database (defaults to a local `sqlite+aiosqlite` file). `get_db` is the FastAPI dependency every
  endpoint uses to get an `AsyncSession`.
- `app/models.py` — SQLAlchemy 2.0 declarative models (`Book`, `Note`) using `Mapped[...]` typed
  columns. `Book.notes` cascades deletes (`cascade="all, delete-orphan"`).
- `app/schemas.py` — Pydantic v2 request/response models. Read models use
  `ConfigDict(from_attributes=True)` so they can be built directly from ORM instances returned by
  endpoints (`response_model=...`).
- `app/routers/` — one router module per resource (`books.py`, `notes.py`), each with its own
  `APIRouter(prefix=...)`, included in `main.py`. `notes.py`'s router is prefixed
  `/books/{book_id}/notes`, so note endpoints are nested under a book. Both routers repeat a local
  `_get_book_or_404` helper to validate the parent book exists before acting on it.
- `alembic/` — migrations, using an async engine (`run_migrations_online` uses
  `async_engine_from_config` + `connection.run_sync`). `alembic/env.py` imports `app.models` so all
  models are registered on `Base.metadata` before autogeneration.

### Established conventions (deviation from these is the "smell" the PR-review fixtures test for)

- All DB access goes through SQLAlchemy's async ORM (`select()`, `AsyncSession`) — no raw SQL, no
  direct DB-API connections.
- All request/response bodies are typed Pydantic models declared in `app/schemas.py` — no bare
  `dict` payloads.
- Each resource gets its own router module under `app/routers/`, included from `main.py` — endpoints
  aren't added ad hoc into unrelated router files.
- Endpoint handlers are `async def` and take `db: AsyncSession = Depends(get_db)`.

## Tests

`tests/conftest.py` provides a `client` fixture: an in-memory SQLite engine (fresh per test) wired up
via `app.dependency_overrides[get_db]`, wrapped in an `httpx.AsyncClient` against the app through
`ASGITransport`. `pytest.ini` sets `asyncio_mode = auto`, so async test functions need no
`@pytest.mark.asyncio` marker.
