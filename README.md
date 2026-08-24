# Bookshelf API

Personal bookshelf API for storing books and reading notes.

## Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

The database schema is created automatically on startup. To manage schema changes explicitly, use Alembic:

```bash
alembic upgrade head
```

## Test

```bash
pytest
```

## Endpoints

| Method | Path                      | Description                          |
|--------|---------------------------|---------------------------------------|
| POST   | `/books`                  | Create a book                         |
| GET    | `/books`                  | List all books (with note counts)     |
| GET    | `/books/{book_id}`        | Get a book with all its notes         |
| POST   | `/books/{book_id}/notes`  | Add a note/highlight to a book        |
| GET    | `/books/{book_id}/notes`  | List all notes for a book             |

## About

This repo also serves as the test target for [prai](https://github.com/TODO/prai) — a PR review agent.
