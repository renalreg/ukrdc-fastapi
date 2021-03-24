export MOTD="Running on debug test server"
poetry run uvicorn ukrdc_fastapi.main:app --reload
