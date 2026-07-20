FROM python:3.12

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
    apt install -y --no-install-recommends build-essential libpq-dev libpq-dev postgresql postgresql-contrib git && \
    useradd -m appuser && mkdir -p /tmp/pgdata && chown appuser:appuser /tmp/pgdata && \
    rm -rf /var/lib/apt/lists/*

# Force poetry to use system git instead of dulwich for VCS deps
ENV POETRY_EXPERIMENTAL_SYSTEM_GIT_CLIENT=true

WORKDIR /app

RUN python -m pip install -U pip wheel && pip install poetry

COPY . ./

# Configure HTTPS token auth, run poetry install, then remove the token from
# git config -- all within one RUN so the token never lands in a committed
# image layer. --mount=type=secret only keeps it out of build cache/history;
# it does NOT stop it from persisting if we wrote it to a file in an earlier,
# separate RUN step.
RUN --mount=type=secret,id=GIT_AUTH_TOKEN,uid=1000 \
    set -eu; \
    TOKEN="$(cat /run/secrets/GIT_AUTH_TOKEN)"; \
    test -n "$TOKEN"; \
    git config --system url."https://x-access-token:${TOKEN}@github.com/".insteadOf "git@github.com:"; \
    git config --system url."https://x-access-token:${TOKEN}@github.com/".insteadOf "ssh://git@github.com/"; \
    git config --system url."https://x-access-token:${TOKEN}@github.com/".insteadOf "https://github.com/"; \
    poetry install --with dev --no-interaction; \
    git config --system --unset-all url."https://x-access-token:${TOKEN}@github.com/".insteadOf; \
    git config --system --remove-section "url.https://x-access-token:${TOKEN}@github.com/" 2>/dev/null || true

RUN chown -R appuser:appuser /app

USER appuser
ENV HOME=/home/appuser

CMD ["poetry", "run", "uvicorn", "ukrdc_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]