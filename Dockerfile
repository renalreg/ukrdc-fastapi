FROM python:3.8-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

WORKDIR /app

RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

COPY . ./

RUN poetry install --no-dev --no-interaction

CMD ["poetry", "run", "uvicorn", "ukrdc_fastapi.main:app"]
