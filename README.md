# Navabe API

Flask-RESTX REST API organized around domain services and repository/mailer ports.

## Run

With the complete Docker environment from the repository root:

```bash
./run.sh
```

The Compose stack waits for MySQL's health check and executes
`data/migration_v2.sql` through the one-shot `db-migrate` service before this
API starts. A fresh MySQL volume is initialized from `data/schema.sql`, imports
`data/NVB.csv`, and creates inventory records. Applied migrations are tracked in
the `schema_migrations` table. The root `run.sh up` command recreates the
one-shot migration task on every scripted start. Compose builds the
`development` Docker stage and mounts `src` into the container; Flask's debug
reloader automatically restarts the API after a source-code change.

For a local process using an already-running MySQL server:

```bash
cp .env.example .env
poetry install
poetry run navabe-api
```

The API listens on `http://localhost:5000`. Interactive Swagger documentation is
available at `http://localhost:5000/docs`.

Set `DATABASE_BACKEND=memory` to explore the API without MySQL. Production
data access uses the MySQL adapter configured by the `MYSQL_*` variables.
Use `data/schema.sql` for a new database or `data/migration_v2.sql` before
connecting an existing Navabe database.
Email delivery is disabled by default; enable it only after configuring `SMTP_*`.

The backend image is defined in `Dockerfile`; its application process only
starts after Compose reports the database migration as successful. Build the
`runtime` stage for a production image:

```bash
docker build --target runtime -t navabe-backend .
```

Changes to `pyproject.toml` or `poetry.lock` require rebuilding the development
image with `./run.sh up`.

## Catalog pagination

`GET /api/v1/books` returns a paginated envelope. Supported parameters:

- `q`: ISBN, title, author or category search
- `page`: page number starting at `1`
- `page_size`: between `1` and `200`
- `sort`: `title`, `price` or `publication_year`
- `direction`: `asc` or `desc`

Example:

```text
GET /api/v1/books?page=2&page_size=24&sort=price&direction=desc
```

The response contains `items`, `pagination.total`, `pagination.total_pages`,
`pagination.has_next`, and the effective sort.

## Quality

```bash
poetry run pytest
poetry run ruff check src tests
```

The layers are:

- `domain`: entities, errors and outbound ports
- `application`: use cases and password policy
- `infrastructure`: MySQL/memory repositories and mail adapters
- `presentation`: versioned Flask-RESTX resources and Swagger contracts
