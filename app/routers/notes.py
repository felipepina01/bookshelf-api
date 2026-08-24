from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Book, Note
from app.schemas import NoteCreate, NoteRead

router = APIRouter(prefix="/books/{book_id}/notes", tags=["notes"])


async def _get_book_or_404(book_id: int, db: AsyncSession) -> Book:
    book = await db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("", response_model=NoteRead, status_code=201)
async def create_note(book_id: int, payload: NoteCreate, db: AsyncSession = Depends(get_db)):
    await _get_book_or_404(book_id, db)
    note = Note(book_id=book_id, text=payload.text, page=payload.page)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("", response_model=list[NoteRead])
async def list_notes(book_id: int, db: AsyncSession = Depends(get_db)):
    await _get_book_or_404(book_id, db)
    result = await db.execute(
        select(Note).where(Note.book_id == book_id).order_by(Note.id)
    )
    return result.scalars().all()
