FROM python:3.12-slim-bookworm

ARG GITHUB_SHA
ARG GITHUB_REF
ARG SENTRY_DSN

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.1.11 \
    GITHUB_SHA=$GITHUB_SHA \
    GITHUB_REF=$GITHUB_REF \
    SENTRY_DSN=$SENTRY_DSN

# Required to build some wheels on newer Python versions
RUN apt update && \
    apt install -y --no-install-recommends build-essential libpq-dev libpq-dev postgresql postgresql-contrib && \
    useradd -m appuser && mkdir -p /tmp/pgdata && chown appuser:appuser /tmp/pgdata && \
    rm -rf /var/lib/apt/lists/* 

WORKDIR /app

RUN python -m pip install -U pip wheel && pip install poetry

COPY . ./

RUN chown -R appuser:appuser /app

USER appuser

RUN poetry install --with dev --no-interaction

CMD ["poetry", "run", "uvicorn", "ukrdc_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
