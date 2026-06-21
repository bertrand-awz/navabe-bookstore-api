
from dataclasses import asdict, dataclass
from decimal import Decimal
from math import ceil


@dataclass(frozen=True, slots=True)
class Book:
    isbn: str
    title: str
    author: str
    editor: str = ""
    category: str = ""
    synopsis: str = ""
    publication_year: int | None = None
    price: Decimal = Decimal("0")
    image_url: str = ""
    quantity: int | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["price"] = float(self.price)
        return data


@dataclass(frozen=True, slots=True)
class BookPage:
    items: tuple[Book, ...]
    page: int
    page_size: int
    total: int
    sort: str
    direction: str

    def to_dict(self) -> dict:
        total_pages = ceil(self.total / self.page_size) if self.total else 0
        return {
            "items": [book.to_dict() for book in self.items],
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total": self.total,
                "total_pages": total_pages,
                "has_next": self.page < total_pages,
                "has_previous": self.page > 1 and total_pages > 0,
            },
            "sort": {"field": self.sort, "direction": self.direction},
        }


@dataclass(frozen=True, slots=True)
class User:
    identifier: str
    name: str
    first_name: str
    address: str
    email: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Admin:
    identifier: str
    name: str
    first_name: str
    email: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OrderLine:
    isbn: str
    quantity: int


@dataclass(frozen=True, slots=True)
class Order:
    identifier: str
    user_id: str
    transaction_id: str
    amount: Decimal
    lines: tuple[OrderLine, ...]

    def to_dict(self) -> dict:
        return {
            "identifier": self.identifier,
            "user_id": self.user_id,
            "transaction_id": self.transaction_id,
            "amount": float(self.amount),
            "lines": [asdict(line) for line in self.lines],
        }
