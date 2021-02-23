# UKRDC-FastAPI

[![codecov](https://codecov.io/gh/renalreg/ukrdc-fastapi/branch/main/graph/badge.svg?token=5GYR8M6G1W)](https://codecov.io/gh/renalreg/ukrdc-fastapi)

## Developer Installation

- Install Poetry
- Run `poetry install`

## Basic Installation

- `pip install .`

## Run the server

- `poetry run uvicorn ukrdc_fastapi.main:app`

## Developer notes

### VSCode config for auto-formatting

```json
{
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### Why the duplicated models?

Currently, the SQLAlchemy models we use are part of a large `services` library. Because of this, using the models involves installing all dependencies of everything in the `services` library. Additionally, that library exists only on a private repository, complicating Docker image generation and dependency resolution.

It is my hope that the models will eventually be split into a separate, public repository to eliminate this issue, however in the meantime I am creating a minimal, inline copy of the models.

A log of the dependencies removed after removing `services` is included below:

```
• Removing bcrypt (3.2.0)
• Removing beautifulsoup4 (4.9.3)
• Removing certifi (2020.12.5)
• Removing cffi (1.14.4)
• Removing chardet (4.0.0)
• Removing cryptography (3.4.4)
• Removing dicttoxml (1.7.4)
• Removing dynaconf (3.1.2)
• Removing faker (5.8.0)
• Removing fpdf (1.7.2)
• Removing future-fstrings (1.2.0)
• Removing hl7apy (1.3.4)
• Removing idna (2.10)
• Removing insignia (0.0.4)
• Removing lxml (4.4.1)
• Removing paramiko (2.7.2)
• Removing pillow (8.1.0)
• Removing psycopg2-binary (2.8.6)
• Removing pycparser (2.20)
• Removing pynacl (1.4.0)
• Removing python-dateutil (2.8.0)
• Removing pyxb (1.2.6)
• Removing redis (3.5.3)
• Removing reportlab (3.5.59)
• Removing requests (2.25.1)
• Removing rr-common (1.1.17)
• Removing soupsieve (2.2)
• Removing sqlalchemy (1.3.5)
• Removing sshtunnel (0.3.1)
• Removing text-unidecode (1.3)
• Removing tpckd-pdfgen (0.0.1)
• Removing ukrdc-schema (2.3.0)
• Removing ukrdc-services (0.1.88 c52332f)
• Removing ukrdc.database (1.1.5)
• Removing urllib3 (1.26.3)
• Removing xlrd (2.0.1)
• Removing xlutils (2.0.0)
• Removing xlwt (1.3.0)
```
