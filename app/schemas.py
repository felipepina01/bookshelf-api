from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    text: str = Field(min_length=1)
    page: int | None = None


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    page: int | None
    created_at: datetime


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    author: str = Field(min_length=1, max_length=200)


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    created_at: datetime


class BookListItem(BookRead):
    note_count: int


class BookDetail(BookRead):
    notes: list[NoteRead]


class BookImportError(BaseModel):
    row: int
    reason: str


class BookImportResult(BaseModel):
    imported: list[BookRead]
    errors: list[BookImportError]
