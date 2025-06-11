FROM python:3.11-slim-buster

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
# Install system dependencies (including PostgreSQL dev headers)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        postgresql \
        postgresql-client \
        pkg-config \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -ms /bin/bash appuser

WORKDIR /app

RUN python -m pip install -U pip wheel && pip install poetry

COPY . ./
RUN chown -R appuser:appuser /app
RUN poetry install

USER appuser
#CMD ["poetry", "run", "uvicorn", "ukrdc_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
