async def test_create_book_happy_path(client):
    response = await client.post(
        "/books", json={"title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Designing Data-Intensive Applications"
    assert body["author"] == "Martin Kleppmann"
    assert "created_at" in body


async def test_create_book_validation_error(client):
    response = await client.post("/books", json={"title": "Missing Author"})
    assert response.status_code == 422


async def test_list_books_includes_note_count(client):
    create_resp = await client.post("/books", json={"title": "Book A", "author": "Author A"})
    book_id = create_resp.json()["id"]
    await client.post(f"/books/{book_id}/notes", json={"text": "A note", "page": 1})

    response = await client.get("/books")
    assert response.status_code == 200
    books = response.json()
    assert len(books) == 1
    assert books[0]["note_count"] == 1


async def test_list_books_empty(client):
    response = await client.get("/books")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_book_happy_path(client):
    create_resp = await client.post("/books", json={"title": "Book B", "author": "Author B"})
    book_id = create_resp.json()["id"]
    await client.post(f"/books/{book_id}/notes", json={"text": "Highlight", "page": 5})

    response = await client.get(f"/books/{book_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == book_id
    assert len(body["notes"]) == 1
    assert body["notes"][0]["text"] == "Highlight"


async def test_get_book_not_found(client):
    response = await client.get("/books/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}
