export WOTD='["Running on internal debug server. Not for deployment."]'
poetry run uvicorn ukrdc_fastapi.main:app --host 0.0.0.0
