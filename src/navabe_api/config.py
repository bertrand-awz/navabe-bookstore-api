import os


def settings() -> dict:
    return {
        "APP_ENV": os.getenv("APP_ENV", "development").lower(),
        "SECRET_KEY": os.getenv("SECRET_KEY", "development-only-change-me"),
        "FRONTEND_ORIGIN": os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
        "COOKIE_SECURE": os.getenv("COOKIE_SECURE", "false").lower() == "true",
        "DATABASE_BACKEND": os.getenv("DATABASE_BACKEND", "mysql"),
        "MYSQL": {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "database": os.getenv("MYSQL_DATABASE", "NAVABE"),
            "user": os.getenv("MYSQL_USER", "Navabe_Project"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
        },
        "MAIL_ENABLED": os.getenv("MAIL_ENABLED", "false").lower() == "true",
        "SMTP_HOST": os.getenv("SMTP_HOST", "smtp.resend.com"),
        "SMTP_PORT": int(os.getenv("SMTP_PORT", "465")),
        "SMTP_USER": os.getenv("SMTP_USER", "resend"),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD") or os.getenv("RESEND_API_KEY", ""),
        "SMTP_SENDER": os.getenv(
            "SMTP_SENDER", "Navabe Bookstore <no-reply@mail.navabe.bertawz.dev>"
        ),
        "SMTP_SECURITY": os.getenv("SMTP_SECURITY", "ssl").lower(),
        "SMTP_TIMEOUT": float(os.getenv("SMTP_TIMEOUT", "10")),
    }


def validate_settings(config: dict) -> None:
    if config["APP_ENV"] != "production":
        return

    unsafe_secrets = {
        "development-only-change-me",
        "docker-development-secret-change-me",
        "replace-with-a-long-random-secret",
    }
    if (
        config["SECRET_KEY"] in unsafe_secrets
        or config["SECRET_KEY"].startswith("replace-with-")
        or len(config["SECRET_KEY"]) < 32
    ):
        raise RuntimeError("Production SECRET_KEY must be a random value of at least 32 characters")
    if not config["COOKIE_SECURE"]:
        raise RuntimeError("COOKIE_SECURE must be true in production")
    if not config["FRONTEND_ORIGIN"].startswith("https://"):
        raise RuntimeError("FRONTEND_ORIGIN must use HTTPS in production")
    if config["DATABASE_BACKEND"] == "mysql":
        password = config["MYSQL"]["password"]
        if not password or password.startswith("replace-"):
            raise RuntimeError("MYSQL_PASSWORD must be set to a non-placeholder value in production")
