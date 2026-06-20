def test_searches_catalog_and_exposes_stock(client):
    response = client.get("/api/v1/books?q=tycoon")
    category_response = client.get("/api/v1/books?q=Essays")

    assert response.status_code == 200
    assert response.json["items"][0]["isbn"] == "9780020199854"
    assert response.json["items"][0]["quantity"] == 4
    assert [book["title"] for book in category_response.json["items"]] == ["Zeta"]


def test_paginates_catalog_with_navigation_metadata(client):
    first_page = client.get("/api/v1/books?page=1&page_size=2")
    second_page = client.get("/api/v1/books?page=2&page_size=2")

    assert [book["title"] for book in first_page.json["items"]] == ["Alpha", "The Love of the Last Tycoon"]
    assert first_page.json["pagination"] == {
        "page": 1,
        "page_size": 2,
        "total": 3,
        "total_pages": 2,
        "has_next": True,
        "has_previous": False,
    }
    assert [book["title"] for book in second_page.json["items"]] == ["Zeta"]
    assert second_page.json["pagination"]["has_next"] is False
    assert second_page.json["pagination"]["has_previous"] is True


def test_sorts_catalog_by_price_and_publication_year(client):
    price_desc = client.get("/api/v1/books?sort=price&direction=desc")
    year_asc = client.get("/api/v1/books?sort=publication_year&direction=asc")

    assert [book["price"] for book in price_desc.json["items"]] == [40.0, 25.0, 10.0]
    assert [book["publication_year"] for book in year_asc.json["items"]] == [1980, 1994, 2020]


def test_rejects_unknown_catalog_sort(client):
    response = client.get("/api/v1/books?sort=author")

    assert response.status_code == 422
    assert response.json["code"] == "invalid_sort"


def test_checks_requested_stock(client):
    assert client.get("/api/v1/books/9780020199854/availability?quantity=4").json["available"] is True
    assert client.get("/api/v1/books/9780020199854/availability?quantity=5").json["available"] is False


def test_returns_structured_error_for_unknown_book(client):
    response = client.get("/api/v1/books/0000000000000")

    assert response.status_code == 404
    assert response.json == {"code": "book_not_found", "message": "Book not found"}
