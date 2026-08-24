from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
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
