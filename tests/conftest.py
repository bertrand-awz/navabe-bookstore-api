from decimal import Decimal

import pytest

from navabe_api import create_app
from navabe_api.application.security import hash_password
from navabe_api.domain.models import Admin, Book, User
from navabe_api.infrastructure.memory_repository import MemoryRepository


class SpyMailer:
    def __init__(self):
        self.messages = []

    def send(self, recipient: str, subject: str, body: str, html: str | None = None) -> None:
        self.messages.append((recipient, subject, body, html))


@pytest.fixture
def repository():
    repo = MemoryRepository()
    repo.books["9780020199854"] = Book(
        isbn="9780020199854",
        title="The Love of the Last Tycoon",
        author="F. Scott Fitzgerald",
        category="Fiction",
        publication_year=1994,
        price=Decimal("25.00"),
        quantity=4,
    )
    repo.books["9780000000001"] = Book(
        isbn="9780000000001",
        title="Alpha",
        author="Alice Author",
        category="Fiction",
        publication_year=2020,
        price=Decimal("40.00"),
        quantity=2,
    )
    repo.books["9789999999999"] = Book(
        isbn="9789999999999",
        title="Zeta",
        author="Zed Author",
        category="Essays",
        publication_year=1980,
        price=Decimal("10.00"),
        quantity=3,
    )
    user = User("JODO0001", "Doe", "John", "1 Main Street", "john@example.com")
    repo.users[user.identifier] = (user, hash_password("secret12"))
    admin = Admin("AD0001", "Admin", "Jane", "admin@example.com")
    repo.admins[admin.identifier] = (admin, hash_password("admin123"))
    return repo


@pytest.fixture
def mailer():
    return SpyMailer()


@pytest.fixture
def app(repository, mailer):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_BACKEND": "memory",
            "FRONTEND_ORIGIN": "http://localhost:5173",
        },
        repository=repository,
        mailer=mailer,
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_client(client):
    response = client.post("/api/v1/auth/login", json={"email": "john@example.com", "password": "secret12"})
    assert response.status_code == 200
    return client


@pytest.fixture
def admin_client(client):
    response = client.post("/api/v1/admin/auth/login", json={"identifier": "AD0001", "password": "admin123"})
    assert response.status_code == 200
    return client
