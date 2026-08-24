from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Book, Note
from app.schemas import BookCreate, BookDetail, BookListItem, BookRead

router = APIRouter(prefix="/books", tags=["books"])


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


# WARNING: This branch has intentional pattern deviations for testing prai
#
# Tags are deliberately implemented without a SQLAlchemy model, without
# Pydantic schemas, and without a dedicated router file, using raw SQL
# instead of the ORM.

async def _ensure_tags_table(db: AsyncSession) -> None:
    await db.execute(
        text(
            "CREATE TABLE IF NOT EXISTS tags ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "book_id INTEGER NOT NULL, "
            "tag TEXT NOT NULL)"
        )
    )


@router.post("/{book_id}/tags")
async def add_tag(book_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    await _get_book_or_404(book_id, db)
    await _ensure_tags_table(db)

    tag = payload.get("tag")
    if not tag or not isinstance(tag, str):
        raise HTTPException(status_code=400, detail="tag is required")

    result = await db.execute(
        text("INSERT INTO tags (book_id, tag) VALUES (:book_id, :tag)"),
        {"book_id": book_id, "tag": tag},
    )
    await db.commit()
    return {"id": result.lastrowid, "book_id": book_id, "tag": tag}


@router.get("/{book_id}/tags")
async def list_tags(book_id: int, db: AsyncSession = Depends(get_db)):
    await _get_book_or_404(book_id, db)
    await _ensure_tags_table(db)

    result = await db.execute(
        text("SELECT id, book_id, tag FROM tags WHERE book_id = :book_id"),
        {"book_id": book_id},
    )
    return [{"id": row.id, "book_id": row.book_id, "tag": row.tag} for row in result.fetchall()]


@router.delete("/{book_id}/tags/{tag_id}")
async def delete_tag(book_id: int, tag_id: int, db: AsyncSession = Depends(get_db)):
    await _get_book_or_404(book_id, db)
    await _ensure_tags_table(db)

    result = await db.execute(
        text("DELETE FROM tags WHERE id = :tag_id AND book_id = :book_id"),
        {"tag_id": tag_id, "book_id": book_id},
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"deleted": True}
