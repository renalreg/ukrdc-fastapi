# UKRDC-FastAPI

[![codecov](https://codecov.io/gh/renalreg/ukrdc-fastapi/branch/main/graph/badge.svg?token=5GYR8M6G1W)](https://codecov.io/gh/renalreg/ukrdc-fastapi)

## Developer Installation

### Prerequisites

- Create a `.env` file with Mirth and database credentials (see `.env.template`):
- Ensure a local Redis instance is running locally on port 6379

### Installation

- Install Poetry
- Run `poetry install`

## Create local databases

### Users Database

If it doesn't already exist, we need to create an sqlite database used to store user information like preferences.

#### Automatic

```bash
poetry run scripts/sqlite/create_databases.py
```

#### Manual

```bash
mkdir data
sqlite3 data/users.sqlite
```

```sql
CREATE TABLE user_preference (uid VARCHAR NOT NULL, "key" VARCHAR NOT NULL, val JSON, PRIMARY KEY (uid, "key"));
```

## Run the server

- `poetry run uvicorn ukrdc_fastapi.main:app`


## Developer notes

### Setting package versions

This repository includes both the Python API application and code to generate client libraries.
Version numbers of the application and all client libraries should remain synchronized.

The version number will effectively become the API version,
so should remain 1.x.x unless breaking API changes are introduced (i.e. API v2).

To quickly set the version of the application and all libraries, call `./version.sh ${version}`.

E.g.

- `./version.sh 1.1.0` to set the version to v1.1.0
- `./version.sh patch` to iterate the version by a patch bump (or `minor` or `major`)

### Build client libraries

Client libraries are automatically built and published on every release.

For development purposes, you can manually trigger the Build Client Libraries workflow to publish a snapshot release.

#### Local `typescript-axios-client` snapshot

`openapi-generator-cli generate -c ./clients/config.json -i ./clients/openapi.json -g typescript-axios -o ./clients/typescript-axios-client --additional-properties=snapshot=true`

### Pre-commit hooks

Included in the repo is a pre-commit config to run Black and isort before committing.

To install/enable the hooks, run

```
poetry run pre-commit install
```

### Local CORS

On some oeprating systems and environments, it may be difficult to properly set a CORS policy for local development. In these cases, add `allow_origins=["*"]` to your `.env` file.

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

### Build ARCHITECTURE.md

- Install `pipx`
- `pipx install archmd`
- `archmd . --out "ARCHITECTURE.md" --title="UKRDC-FastAPI Architecture"`
