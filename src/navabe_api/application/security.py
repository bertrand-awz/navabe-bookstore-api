from __future__ import annotations

import secrets
import string

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def password_matches(stored_hash: str, candidate: str) -> bool:
    return check_password_hash(stored_hash, candidate)


def temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
