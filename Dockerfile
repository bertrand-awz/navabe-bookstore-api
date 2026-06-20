FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir "poetry==2.3.2"

COPY pyproject.toml poetry.lock README.md ./
COPY src ./src

FROM base AS development

RUN poetry install --with dev --no-interaction --no-ansi

EXPOSE 5000

CMD ["poetry", "run", "flask", "--app", "navabe_api:create_app", "run", "--debug", "--host=0.0.0.0", "--port=5000"]

FROM base AS runtime

RUN poetry install --only main --no-interaction --no-ansi

RUN useradd --create-home --uid 10001 navabe \
    && chown -R navabe:navabe /app

USER navabe

EXPOSE 5000

CMD ["python", "-m", "navabe_api"]
