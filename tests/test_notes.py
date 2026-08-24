async def _create_book(client):
    response = await client.post("/books", json={"title": "Some Book", "author": "Some Author"})
    return response.json()["id"]


async def test_create_note_happy_path(client):
    book_id = await _create_book(client)
    response = await client.post(
        f"/books/{book_id}/notes",
        json={"text": "The limits of my language mean the limits of my world.", "page": 42},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["text"] == "The limits of my language mean the limits of my world."
    assert body["page"] == 42
    assert "id" in body
    assert "created_at" in body


async def test_create_note_optional_page(client):
    book_id = await _create_book(client)
    response = await client.post(f"/books/{book_id}/notes", json={"text": "No page here"})
    assert response.status_code == 201
    assert response.json()["page"] is None


async def test_create_note_book_not_found(client):
    response = await client.post("/books/999/notes", json={"text": "Orphan note"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


async def test_create_note_validation_error(client):
    book_id = await _create_book(client)
    response = await client.post(f"/books/{book_id}/notes", json={"page": 1})
    assert response.status_code == 422


async def test_list_notes_happy_path(client):
    book_id = await _create_book(client)
    await client.post(f"/books/{book_id}/notes", json={"text": "Note 1"})
    await client.post(f"/books/{book_id}/notes", json={"text": "Note 2"})

    response = await client.get(f"/books/{book_id}/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 2
    assert [n["text"] for n in notes] == ["Note 1", "Note 2"]


async def test_list_notes_book_not_found(client):
    response = await client.get("/books/999/notes")
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}
