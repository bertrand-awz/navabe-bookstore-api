
from decimal import Decimal, InvalidOperation

from navabe_api.application.security import hash_password, password_matches, temporary_password
from navabe_api.domain.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from navabe_api.domain.models import Admin, Book, BookPage, Order, OrderLine, User
from navabe_api.domain.ports import Mailer, NavabeRepository


class CatalogService:
    SORTS = {"title", "price", "publication_year"}
    DIRECTIONS = {"asc", "desc"}

    def __init__(self, repository: NavabeRepository):
        self.repository = repository

    def list_books(
        self,
        query: str = "",
        page: int = 1,
        page_size: int = 24,
        sort: str = "title",
        direction: str = "asc",
    ) -> BookPage:
        if page < 1:
            raise ValidationError("Page must be greater than or equal to 1", "invalid_page")
        if page_size < 1 or page_size > 200:
            raise ValidationError("Page size must be between 1 and 200", "invalid_page_size")
        if sort not in self.SORTS:
            raise ValidationError("Sort must be title, price or publication_year", "invalid_sort")
        if direction not in self.DIRECTIONS:
            raise ValidationError("Direction must be asc or desc", "invalid_direction")

        query = query.strip()
        items = self.repository.list_books(query, page_size, (page - 1) * page_size, sort, direction)
        return BookPage(tuple(items), page, page_size, self.repository.count_books(query), sort, direction)

    def get_book(self, isbn: str) -> Book:
        book = self.repository.get_book(isbn)
        if not book:
            raise NotFoundError("Book not found", "book_not_found")
        return book

    def check_stock(self, isbn: str, quantity: int) -> bool:
        if quantity < 1:
            raise ValidationError("Quantity must be positive", "invalid_quantity")
        return self.repository.stock_available(isbn, quantity)


class IdentityService:
    def __init__(self, repository: NavabeRepository, mailer: Mailer):
        self.repository = repository
        self.mailer = mailer

    def register(self, payload: dict) -> User:
        required = ("name", "first_name", "address", "email", "password")
        if any(not str(payload.get(field, "")).strip() for field in required):
            raise ValidationError("All fields are required", "missing_fields")
        if len(payload["password"]) < 6:
            raise ValidationError("Password must contain at least 6 characters", "weak_password")
        try:
            user = self.repository.create_user(
                payload["name"].strip(),
                payload["first_name"].strip(),
                payload["address"].strip(),
                payload["email"].strip().lower(),
                hash_password(payload["password"]),
            )
        except ConflictError:
            raise
        self.mailer.send(
            user.email,
            "Welcome to Navabe",
            f"Hello {user.first_name},\n\nYour Navabe identifier is {user.identifier}.",
        )
        return user

    def login(self, email: str, password: str) -> User:
        result = self.repository.get_user_by_email(email.strip().lower())
        if not result or not password_matches(result[1], password):
            raise AuthenticationError("Incorrect email or password", "invalid_credentials")
        return result[0]

    def get_user(self, identifier: str) -> User:
        result = self.repository.get_user_by_id(identifier)
        if not result:
            raise NotFoundError("User not found", "user_not_found")
        return result[0]

    def change_password(self, identifier: str, new_password: str) -> None:
        if len(new_password) < 6:
            raise ValidationError("Password must contain at least 6 characters", "weak_password")
        user = self.get_user(identifier)
        if not self.repository.update_user_password(identifier, hash_password(new_password)):
            raise NotFoundError("User not found", "user_not_found")
        self.mailer.send(user.email, "Navabe password changed", f"Hello {user.first_name},\n\nYour password was changed.")

    def recover(self, identifier: str) -> None:
        user = self.get_user(identifier)
        password = temporary_password()
        self.repository.update_user_password(identifier, hash_password(password))
        self.mailer.send(
            user.email,
            "Navabe account recovery",
            f"Hello {user.first_name},\n\nYour temporary password is: {password}",
        )


class OrderService:
    def __init__(self, repository: NavabeRepository):
        self.repository = repository

    def create(self, user_id: str, payload: dict) -> Order:
        transaction_id = str(payload.get("transaction_id", "")).strip()
        raw_lines = payload.get("lines") or []
        if not transaction_id or not raw_lines:
            raise ValidationError("A transaction and at least one line are required", "invalid_order")
        lines = tuple(OrderLine(str(line.get("isbn", "")), int(line.get("quantity", 0))) for line in raw_lines)
        if any(not line.isbn or line.quantity < 1 for line in lines):
            raise ValidationError("Every order line needs an ISBN and positive quantity", "invalid_order_line")
        for line in lines:
            if not self.repository.stock_available(line.isbn, line.quantity):
                raise ConflictError(f"Insufficient stock for {line.isbn}", "insufficient_stock")
        try:
            amount = Decimal(str(payload.get("amount", ""))).quantize(Decimal("0.01"))
        except InvalidOperation as error:
            raise ValidationError("Invalid order amount", "invalid_amount") from error
        if amount <= 0:
            raise ValidationError("Order amount must be positive", "invalid_amount")
        expected = sum(
            (self.repository.get_book(line.isbn).price * line.quantity for line in lines),
            start=Decimal("0"),
        ).quantize(Decimal("0.01"))
        if amount != expected:
            raise ValidationError("Order amount does not match current catalog prices", "invalid_amount")
        return self.repository.create_order(user_id, transaction_id, lines, amount)


class AdminService:
    METRICS = {"stock", "sales", "orders", "average-price"}

    def __init__(self, repository: NavabeRepository, mailer: Mailer):
        self.repository = repository
        self.mailer = mailer

    def login(self, identifier: str, password: str) -> Admin:
        result = self.repository.get_admin_by_id(identifier.strip())
        if not result or not password_matches(result[1], password):
            raise AuthenticationError("Incorrect manager ID or password", "invalid_credentials")
        return result[0]

    def create_admin(self, payload: dict) -> Admin:
        if any(not str(payload.get(field, "")).strip() for field in ("name", "first_name", "email")):
            raise ValidationError("Name, first name and email are required", "missing_fields")
        password = temporary_password()
        admin = self.repository.create_admin(
            payload["name"].strip(),
            payload["first_name"].strip(),
            payload["email"].strip().lower(),
            hash_password(password),
        )
        self.mailer.send(
            admin.email,
            "Welcome to the Navabe Management Portal",
            f"Your manager ID is {admin.identifier} and your temporary password is {password}.",
        )
        return admin

    def recover(self, identifier: str) -> None:
        result = self.repository.get_admin_by_id(identifier)
        if not result:
            raise NotFoundError("Management account not found", "admin_not_found")
        admin = result[0]
        password = temporary_password()
        self.repository.update_admin_password(identifier, hash_password(password))
        self.mailer.send(admin.email, "Navabe management account recovery", f"Your temporary password is {password}.")

    def upsert_book(self, payload: dict) -> Book:
        required = ("isbn", "title", "author", "price")
        if any(not str(payload.get(field, "")).strip() for field in required):
            raise ValidationError("ISBN, title, author and price are required", "missing_fields")
        isbn = str(payload["isbn"]).strip()
        if len(isbn) != 13 or not isbn.isdigit():
            raise ValidationError("ISBN must contain exactly 13 digits", "invalid_isbn")
        try:
            book = Book(
                isbn=isbn,
                title=str(payload["title"]).strip(),
                author=str(payload["author"]).strip(),
                editor=str(payload.get("editor", "")).strip(),
                category=str(payload.get("category", "")).strip(),
                synopsis=str(payload.get("synopsis", "")).strip(),
                publication_year=int(payload["publication_year"]) if payload.get("publication_year") else None,
                price=Decimal(str(payload["price"])).quantize(Decimal("0.01")),
                image_url=str(payload.get("image_url", "")).strip(),
            )
            quantity = int(payload.get("quantity", 0))
        except (InvalidOperation, TypeError, ValueError) as error:
            raise ValidationError("Invalid book data", "invalid_book") from error
        if book.price <= 0 or quantity < 0:
            raise ValidationError("Price must be positive and quantity cannot be negative", "invalid_book")
        return self.repository.upsert_book(book, quantity)

    def delete_book(self, isbn: str) -> None:
        if not self.repository.delete_book(isbn):
            raise NotFoundError("Book not found", "book_not_found")

    def get_order(self, identifier: str) -> dict:
        order = self.repository.get_order(identifier)
        if not order:
            raise NotFoundError("Order not found", "order_not_found")
        return order

    def statistics(self, metric: str, group_by: str = "") -> dict:
        if metric not in self.METRICS:
            raise ValidationError("Unknown statistic metric", "invalid_metric")
        if metric in {"stock", "average-price"} and group_by not in {"", "category", "year"}:
            raise ValidationError("This metric can only be grouped by category or year", "invalid_grouping")
        return self.repository.statistics(metric, group_by)
