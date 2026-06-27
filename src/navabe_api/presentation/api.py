from functools import wraps

from flask import current_app, request, session
from flask_restx import Api, Namespace, Resource, fields

from navabe_api.domain.exceptions import AuthorizationError, DomainError


def configure_api(app) -> Api:
    api = Api(
        app,
        version="2.0",
        title="Navabe Bookstore API",
        description="REST API for Navabe's catalog, customer accounts, orders and administration.",
        prefix="/api/v1",
        doc="/docs",
        contact="Navabe Team",
        license="Educational project",
        security="sessionCookie",
        authorizations={"sessionCookie": {"type": "apiKey", "in": "cookie", "name": "session"}},
    )
    _register_models_and_namespaces(api)

    @api.errorhandler(DomainError)
    def handle_domain_error(error):
        return {"code": error.code, "message": error.message}, error.status_code

    return api


def services():
    return current_app.extensions["navabe_services"]


def payload():
    return request.get_json(silent=True) or {}


def user_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            raise AuthorizationError("Customer session required", "user_session_required")
        return function(*args, **kwargs)
    return wrapper


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            raise AuthorizationError("Management session required", "admin_session_required")
        if session.get("admin_must_change_password"):
            raise AuthorizationError(
                "Management password change required",
                "admin_password_change_required",
            )
        return function(*args, **kwargs)
    return wrapper


def admin_session_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            raise AuthorizationError("Management session required", "admin_session_required")
        return function(*args, **kwargs)
    return wrapper


def _register_models_and_namespaces(api: Api) -> None:
    book_model = api.model(
        "Book",
        {
            "isbn": fields.String(required=True, example="9780020199854"),
            "title": fields.String(required=True),
            "author": fields.String(required=True),
            "editor": fields.String,
            "category": fields.String,
            "synopsis": fields.String,
            "publication_year": fields.Integer,
            "price": fields.Float(required=True),
            "image_url": fields.String,
            "quantity": fields.Integer,
        },
    )
    book_write = api.inherit("BookWrite", book_model, {"quantity": fields.Integer(default=0)})
    pagination_model = api.model(
        "Pagination",
        {
            "page": fields.Integer,
            "page_size": fields.Integer,
            "total": fields.Integer,
            "total_pages": fields.Integer,
            "has_next": fields.Boolean,
            "has_previous": fields.Boolean,
        },
    )
    sort_model = api.model("CatalogSort", {"field": fields.String, "direction": fields.String})
    book_page_model = api.model(
        "BookPage",
        {
            "items": fields.List(fields.Nested(book_model)),
            "pagination": fields.Nested(pagination_model),
            "sort": fields.Nested(sort_model),
        },
    )
    user_model = api.model(
        "User",
        {
            "identifier": fields.String,
            "name": fields.String,
            "first_name": fields.String,
            "address": fields.String,
            "email": fields.String,
        },
    )
    register_model = api.model(
        "RegisterCustomer",
        {
            "name": fields.String(required=True),
            "first_name": fields.String(required=True),
            "address": fields.String(required=True),
            "email": fields.String(required=True),
            "password": fields.String(required=True, min_length=6),
        },
    )
    login_model = api.model(
        "Login",
        {"email": fields.String(required=True), "password": fields.String(required=True)},
    )
    admin_login_model = api.model(
        "AdminLogin",
        {"identifier": fields.String(required=True), "password": fields.String(required=True)},
    )
    order_line_model = api.model(
        "OrderLine",
        {"isbn": fields.String(required=True), "quantity": fields.Integer(required=True, min=1)},
    )
    order_model = api.model(
        "CreateOrder",
        {
            "transaction_id": fields.String(required=True),
            "amount": fields.Float(required=True, min=0.01),
            "lines": fields.List(fields.Nested(order_line_model), required=True),
        },
    )
    admin_create_model = api.model(
        "CreateAdministrator",
        {
            "name": fields.String(required=True),
            "first_name": fields.String(required=True),
            "email": fields.String(required=True),
        },
    )
    password_model = api.model("ChangePassword", {"password": fields.String(required=True, min_length=6)})
    recovery_model = api.model("Recovery", {"identifier": fields.String(required=True)})

    health = Namespace("health", description="Service health")
    books = Namespace("books", description="Public catalog and stock")
    auth = Namespace("auth", description="Customer identity and sessions")
    orders = Namespace("orders", description="Customer orders")
    admin = Namespace("admin", description="Protected administration operations")

    @health.route("")
    class Health(Resource):
        def get(self):
            """Check whether the API process is healthy."""
            return {"status": "ok", "version": "2.0.0"}

    @books.route("")
    class Books(Resource):
        @books.doc(
            params={
                "q": "ISBN, title, author or category",
                "page": "Page number, starting at 1",
                "page_size": "Books per page, between 1 and 200",
                "sort": "title, price or publication_year",
                "direction": "asc or desc",
            }
        )
        @books.marshal_with(book_page_model)
        def get(self):
            """List or search a sorted page of books."""
            from flask import request
            return services()["catalog"].list_books(
                request.args.get("q", ""),
                request.args.get("page", default=1, type=int),
                request.args.get("page_size", default=24, type=int),
                request.args.get("sort", "title"),
                request.args.get("direction", "asc"),
            ).to_dict()

    @books.route("/<string:isbn>")
    class BookItem(Resource):
        @books.marshal_with(book_model)
        def get(self, isbn):
            """Get one book by ISBN."""
            return services()["catalog"].get_book(isbn).to_dict()

    @books.route("/<string:isbn>/availability")
    class Availability(Resource):
        @books.doc(params={"quantity": "Requested quantity"})
        def get(self, isbn):
            """Check whether the requested quantity is in stock."""
            from flask import request
            quantity = request.args.get("quantity", default=1, type=int)
            return {"isbn": isbn, "quantity": quantity, "available": services()["catalog"].check_stock(isbn, quantity)}

    @auth.route("/register")
    class Register(Resource):
        @auth.expect(register_model, validate=True)
        @auth.marshal_with(user_model, code=201)
        def post(self):
            """Create a customer account and open its session."""
            user = services()["identity"].register(payload())
            session.clear()
            session["user_id"] = user.identifier
            return user.to_dict(), 201

    @auth.route("/login")
    class Login(Resource):
        @auth.expect(login_model, validate=True)
        @auth.marshal_with(user_model)
        def post(self):
            """Authenticate a customer and open a secure server-side session."""
            user = services()["identity"].login(payload()["email"], payload()["password"])
            session.clear()
            session["user_id"] = user.identifier
            return user.to_dict()

    @auth.route("/me")
    class Me(Resource):
        @user_required
        @auth.marshal_with(user_model)
        def get(self):
            """Return the currently authenticated customer."""
            return services()["identity"].get_user(session["user_id"]).to_dict()

    @auth.route("/logout")
    class Logout(Resource):
        @user_required
        def post(self):
            """Close the current customer session."""
            session.clear()
            return "", 204

    @auth.route("/password")
    class Password(Resource):
        @user_required
        @auth.expect(password_model, validate=True)
        def patch(self):
            """Change the current customer's password and close the session."""
            services()["identity"].change_password(session["user_id"], payload()["password"])
            session.clear()
            return "", 204

    @auth.route("/recovery")
    class Recovery(Resource):
        @auth.expect(recovery_model, validate=True)
        def post(self):
            """Generate and email a temporary customer password."""
            services()["identity"].recover(payload()["identifier"])
            return "", 204

    @orders.route("")
    class Orders(Resource):
        @user_required
        @orders.expect(order_model, validate=True)
        def post(self):
            """Record a paid order and atomically update stock."""
            return services()["orders"].create(session["user_id"], payload()).to_dict(), 201

    @admin.route("/auth/login")
    class AdminLogin(Resource):
        @admin.expect(admin_login_model, validate=True)
        def post(self):
            """Authenticate an administrator."""
            administrator = services()["admin"].login(payload()["identifier"], payload()["password"])
            session.clear()
            session["admin_id"] = administrator.identifier
            session["admin_must_change_password"] = administrator.must_change_password
            return administrator.to_dict()

    @admin.route("/auth/session")
    class AdminSession(Resource):
        def get(self):
            """Report the active administrator session."""
            return {
                "authenticated": bool(session.get("admin_id")),
                "identifier": session.get("admin_id"),
                "must_change_password": bool(session.get("admin_must_change_password")),
            }

    @admin.route("/auth/logout")
    class AdminLogout(Resource):
        @admin_session_required
        def post(self):
            """Close the current administrator session."""
            session.clear()
            return "", 204

    @admin.route("/auth/password")
    class AdminPassword(Resource):
        @admin_session_required
        @admin.expect(password_model, validate=True)
        def patch(self):
            """Change the current manager password."""
            services()["admin"].change_password(session["admin_id"], payload()["password"])
            session["admin_must_change_password"] = False
            return "", 204

    @admin.route("/auth/recovery")
    class AdminRecovery(Resource):
        @admin.expect(recovery_model, validate=True)
        def post(self):
            """Generate and email an administrator temporary password."""
            services()["admin"].recover(payload()["identifier"])
            return "", 204

    @admin.route("/administrators")
    class Administrators(Resource):
        @admin_required
        @admin.expect(admin_create_model, validate=True)
        def post(self):
            """Create a new administrator."""
            return services()["admin"].create_admin(payload()).to_dict(), 201

    @admin.route("/books")
    class AdminBooks(Resource):
        @admin_required
        @admin.doc(params={"q": "ISBN, title, author or category"})
        @admin.marshal_list_with(book_model)
        def get(self):
            """Search books from the administration area."""
            from flask import request
            page = services()["catalog"].list_books(request.args.get("q", ""), 1, 200)
            return [book.to_dict() for book in page.items]

        @admin_required
        @admin.expect(book_write, validate=True)
        @admin.marshal_with(book_model, code=201)
        def post(self):
            """Create or update a book and add the supplied stock quantity."""
            return services()["admin"].upsert_book(payload()).to_dict(), 201

    @admin.route("/books/<string:isbn>")
    class AdminBook(Resource):
        @admin_required
        def delete(self, isbn):
            """Remove a book and its inventory record."""
            services()["admin"].delete_book(isbn)
            return "", 204

    @admin.route("/orders/<string:identifier>")
    class AdminOrder(Resource):
        @admin_required
        def get(self, identifier):
            """Find an order by its 16-character identifier."""
            return services()["admin"].get_order(identifier)

    @admin.route("/statistics/<string:metric>")
    class Statistics(Resource):
        @admin_required
        @admin.doc(params={"group_by": "category or year where applicable"})
        def get(self, metric):
            """Return labeled values for stock, sales, order or average-price charts."""
            from flask import request
            return services()["admin"].statistics(metric, request.args.get("group_by", ""))

    for namespace in (health, books, auth, orders, admin):
        api.add_namespace(namespace)
