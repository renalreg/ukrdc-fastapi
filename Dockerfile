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

# SSH setup for private Git deps
RUN mkdir -p /home/appuser/.ssh && \
    ssh-keyscan github.com >> /home/appuser/.ssh/known_hosts && \
    chown -R appuser:appuser /home/appuser/.ssh

RUN --mount=type=secret,id=ssh_private_key,uid=1000 \
    cp /run/secrets/ssh_private_key /home/appuser/.ssh/id_rsa && \
    chmod 600 /home/appuser/.ssh/id_rsa && \
    chown appuser:appuser /home/appuser/.ssh/id_rsa

# System-level config applies regardless of which user runs git later
RUN git config --system url."git@github.com:".insteadOf "https://github.com/"

# Force poetry to use system git instead of dulwich for VCS deps
ENV POETRY_EXPERIMENTAL_SYSTEM_GIT_CLIENT=true

WORKDIR /app

RUN python -m pip install -U pip wheel && pip install poetry

COPY . ./

RUN chown -R appuser:appuser /app

USER appuser
ENV HOME=/home/appuser

RUN poetry install --with dev --no-interaction

CMD ["poetry", "run", "uvicorn", "ukrdc_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]