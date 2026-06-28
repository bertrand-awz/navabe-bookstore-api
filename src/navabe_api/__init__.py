from flask import Flask, redirect
from flask_cors import CORS

from navabe_api.application.services import (
    AdminService,
    CatalogService,
    IdentityService,
    OrderService,
)
from navabe_api.config import settings, validate_settings
from navabe_api.infrastructure.mailers import LoggingMailer, SmtpMailer
from navabe_api.infrastructure.memory_repository import MemoryRepository
from navabe_api.infrastructure.mysql_repository import MySqlRepository
from navabe_api.presentation.api import configure_api


def create_app(config: dict | None = None, repository=None, mailer=None) -> Flask:
    app = Flask(__name__)
    app.config.update(settings())
    if config:
        app.config.update(config)
    validate_settings(app.config)
    app.config.update(
        RESTX_ERROR_404_HELP=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=app.config["COOKIE_SECURE"],
    )
    CORS(app, origins=[app.config["FRONTEND_ORIGIN"]], supports_credentials=True)

    repository = repository or _repository(app.config)
    mailer = mailer or _mailer(app.config)
    app.extensions["navabe_services"] = {
        "catalog": CatalogService(repository),
        "identity": IdentityService(repository, mailer),
        "orders": OrderService(repository),
        "admin": AdminService(repository, mailer),
    }
    configure_api(app)

    @app.get("/")
    def api_documentation():
        return redirect("/docs", code=302)

    @app.get("/swagger")
    def legacy_api_documentation():
        return redirect("/docs", code=302)

    return app


def _repository(config: dict):
    return (
        MemoryRepository()
        if config["DATABASE_BACKEND"] == "memory"
        else MySqlRepository(config["MYSQL"])
    )


def _mailer(config: dict):
    if not config["MAIL_ENABLED"]:
        return LoggingMailer()
    if bool(config["SMTP_USER"]) != bool(config["SMTP_PASSWORD"]):
        raise RuntimeError("SMTP_USER and SMTP_PASSWORD must both be set or both be empty")
    return SmtpMailer(
        config["SMTP_HOST"],
        config["SMTP_PORT"],
        config["SMTP_USER"],
        config["SMTP_PASSWORD"],
        config["SMTP_SENDER"],
        config["SMTP_TIMEOUT"],
        config["SMTP_SECURITY"],
    )
