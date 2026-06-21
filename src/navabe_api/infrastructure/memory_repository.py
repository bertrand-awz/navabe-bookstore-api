
import secrets
import string
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from navabe_api.domain.exceptions import ConflictError
from navabe_api.domain.models import Admin, Book, Order, OrderLine, User


class MemoryRepository:
    def __init__(self):
        self.books: dict[str, Book] = {}
        self.users: dict[str, tuple[User, str]] = {}
        self.admins: dict[str, tuple[Admin, str]] = {}
        self.orders: dict[str, dict] = {}

    def _matching_books(self, query: str) -> list[Book]:
        query = query.lower()
        return [
            book
            for book in self.books.values()
            if not query or query in " ".join((book.isbn, book.title, book.author, book.category)).lower()
        ]

    def list_books(self, query: str, limit: int, offset: int, sort: str, direction: str) -> list[Book]:
        books = self._matching_books(query)
        books.sort(key=lambda book: (book.title.casefold(), book.isbn))
        if sort == "publication_year":
            published = [book for book in books if book.publication_year is not None]
            unpublished = [book for book in books if book.publication_year is None]
            published.sort(key=lambda book: book.publication_year, reverse=direction == "desc")
            books = published + unpublished
        else:
            key = (lambda book: book.title.casefold()) if sort == "title" else (lambda book: book.price)
            books.sort(key=key, reverse=direction == "desc")
        return books[offset : offset + limit]

    def count_books(self, query: str) -> int:
        return len(self._matching_books(query))

    def get_book(self, isbn: str) -> Book | None:
        return self.books.get(isbn)

    def stock_available(self, isbn: str, quantity: int) -> bool:
        book = self.books.get(isbn)
        return bool(book and book.quantity is not None and book.quantity >= quantity)

    def create_user(self, name: str, first_name: str, address: str, email: str, password_hash: str) -> User:
        if any(user.email == email for user, _ in self.users.values()):
            raise ConflictError("Email already registered", "email_exists")
        identifier = f"{first_name[:2]}{name[:2]}{len(self.users) + 1:04d}".upper()
        user = User(identifier, name, first_name, address, email)
        self.users[identifier] = (user, password_hash)
        return user

    def get_user_by_email(self, email: str) -> tuple[User, str] | None:
        return next((record for record in self.users.values() if record[0].email == email), None)

    def get_user_by_id(self, identifier: str) -> tuple[User, str] | None:
        return self.users.get(identifier)

    def update_user_password(self, identifier: str, password_hash: str) -> bool:
        record = self.users.get(identifier)
        if not record:
            return False
        self.users[identifier] = (record[0], password_hash)
        return True

    def create_order(self, user_id: str, transaction_id: str, lines: tuple[OrderLine, ...], amount: Decimal) -> Order:
        identifier = datetime.now().strftime("%Y%m%d") + secrets.token_hex(4).upper()
        order = Order(identifier, user_id, transaction_id, amount, lines)
        details = order.to_dict() | {"status": "In process", "created_at": datetime.now().isoformat()}
        details["items"] = []
        for line in lines:
            book = self.books[line.isbn]
            self.books[line.isbn] = Book(**(book.to_dict() | {"price": book.price, "quantity": book.quantity - line.quantity}))
            details["items"].append({"title_by_author": f"{book.title} by {book.author}", "book_price": float(book.price), "quantity": line.quantity})
        self.orders[identifier] = details
        return order

    def get_admin_by_id(self, identifier: str) -> tuple[Admin, str] | None:
        return self.admins.get(identifier)

    def create_admin(self, name: str, first_name: str, email: str, password_hash: str) -> Admin:
        if any(admin.email == email for admin, _ in self.admins.values()):
            raise ConflictError("Email already registered", "email_exists")
        suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        admin = Admin(f"{name[0]}{first_name[0]}{suffix}".upper(), name, first_name, email)
        self.admins[admin.identifier] = (admin, password_hash)
        return admin

    def update_admin_password(self, identifier: str, password_hash: str) -> bool:
        record = self.admins.get(identifier)
        if not record:
            return False
        self.admins[identifier] = (record[0], password_hash)
        return True

    def upsert_book(self, book: Book, quantity: int) -> Book:
        current = self.books.get(book.isbn)
        total = quantity + (current.quantity or 0 if current else 0)
        saved = Book(**(book.to_dict() | {"price": book.price, "quantity": total}))
        self.books[book.isbn] = saved
        return saved

    def delete_book(self, isbn: str) -> bool:
        return self.books.pop(isbn, None) is not None

    def get_order(self, identifier: str) -> dict | None:
        return self.orders.get(identifier)

    def statistics(self, metric: str, group_by: str) -> dict:
        values: dict[str, float] = defaultdict(float)
        counts: dict[str, int] = defaultdict(int)
        if metric in {"stock", "average-price"}:
            key_name = "publication_year" if group_by == "year" else "category"
            for book in self.books.values():
                label = str(getattr(book, key_name) or "Unknown")
                values[label] += float(book.quantity or 0) if metric == "stock" else float(book.price)
                counts[label] += 1
        elif metric == "orders":
            for order in self.orders.values():
                values[order["status"]] += 1
        elif metric == "sales":
            for order in self.orders.values():
                values[order["created_at"][5:7]] += order["amount"]
        if metric == "average-price":
            values = {label: round(total / counts[label], 2) for label, total in values.items()}
        return {"labels": list(values), "values": list(values.values())}
