FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.1.5

WORKDIR /app

RUN python -m pip install -U pip==21.0.1 && pip install poetry

COPY . ./

RUN poetry install --no-dev --no-interaction

CMD ["poetry", "run", "uvicorn", "ukrdc_fastapi.main:app"]
