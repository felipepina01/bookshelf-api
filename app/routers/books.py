import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Book, Note
from app.schemas import (
    BookCreate,
    BookDetail,
    BookImportError,
    BookImportResult,
    BookListItem,
    BookRead,
)

router = APIRouter(prefix="/books", tags=["books"])

REQUIRED_IMPORT_COLUMNS = {"title", "author"}


async def _get_book_or_404(book_id: int, db: AsyncSession) -> Book:
    book = await db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("", response_model=BookRead, status_code=201)
async def create_book(payload: BookCreate, db: AsyncSession = Depends(get_db)):
    book = Book(title=payload.title, author=payload.author)
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


@router.post("/import", response_model=BookImportResult, status_code=201)
async def import_books(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv file")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = {name.strip().lower() for name in (reader.fieldnames or [])}
    if not REQUIRED_IMPORT_COLUMNS.issubset(fieldnames):
        raise HTTPException(
            status_code=400, detail="CSV must have 'title' and 'author' columns"
        )

    imported: list[Book] = []
    errors: list[BookImportError] = []

    for row_number, row in enumerate(reader, start=2):  # row 1 is the header
        title = (row.get("title") or "").strip()
        author = (row.get("author") or "").strip()
        if not title or not author:
            errors.append(
                BookImportError(row=row_number, reason="Missing title or author")
            )
            continue
        book = Book(title=title, author=author)
        db.add(book)
        imported.append(book)

    await db.commit()
    for book in imported:
        await db.refresh(book)

    return BookImportResult(imported=imported, errors=errors)


@router.get("", response_model=list[BookListItem])
async def list_books(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book, func.count(Note.id).label("note_count"))
        .outerjoin(Note, Note.book_id == Book.id)
        .group_by(Book.id)
        .order_by(Book.id)
    )
    items = [
        BookListItem(
            id=book.id,
            title=book.title,
            author=book.author,
            created_at=book.created_at,
            note_count=note_count,
        )
        for book, note_count in result.all()
    ]
    return items


@router.get("/{book_id}", response_model=BookDetail)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book).where(Book.id == book_id).options(selectinload(Book.notes))
    )
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
