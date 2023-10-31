# UKRDC-FastAPI

[![Test and Publish](https://github.com/renalreg/ukrdc-fastapi/actions/workflows/main.yml/badge.svg)](https://github.com/renalreg/ukrdc-fastapi/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/renalreg/ukrdc-fastapi/branch/main/graph/badge.svg?token=5GYR8M6G1W)](https://codecov.io/gh/renalreg/ukrdc-fastapi)

## Documentation

- [Redoc API Documentation](https://renalreg.github.io/ukrdc-fastapi/redoc/)
- [OpenAPI Specification](https://renalreg.github.io/ukrdc-fastapi/openapi.json)
- [`@ukkidney/ukrdc-axios-ts` Documentation](https://renalreg.github.io/ukrdc-fastapi/typescript-axios-client/)

## Developer Installation

### Prerequisites

- Create a `.env` file with Mirth and database credentials (see `.env.template`):
- Ensure a local Redis instance is running locally on port 6379

### Installation

- Install Poetry
- Run `poetry install`

#### Install pre-commit hooks

- Run `pre-commit install`

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

### Autofix issues before commit

- `poetry run ruff --fix ./ukrdc_fastapi`
- `poetry run ruff format ./ukrdc_fastapi`

### Application and API versioning

The application version will be used as the API version in all documentation and clients. Therefore, the application should follow [semantic versioning](https://semver.org/) for the API functionality, that is:

- Major version changes should be accompanied by a breaking change in the API.
- Minor version changes should be accompanied by a non-breaking change in the API.
- Patch version changes should be accompanied by fixes or updates introducing no new API functionality.

Use `./setversion.sh {version_number}` to set the application version. E.g. `./setversion.sh 4.0.0-rc.1`.

### Github Release Versions

Github releases should use tags that follow the application version. E.g. application version 1.0.1 will be tagged with `v1.0.1`.

This will publish a container image tagged with the version number, and `latest` (except pre-release versions e.g. `1.0.1-beta.1`).


### Build client libraries

Client libraries are automatically built and published on every release.

For development purposes, you can [manually trigger the Build Client Libraries workflow](https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow) to publish a snapshot release.

#### Local `typescript-axios-client` snapshot

`poetry run python clients/generate_spec.py`

`npx @openapitools/openapi-generator-cli generate -c ./clients/typescript-axios-client/config.json -i ./clients/openapi.json -g typescript-axios -o ./typescript-axios-client --additional-properties=snapshot=true`

`npx typedoc ./typescript-axios-client/index.ts --out ./docs/typescript-axios-client`

### Local CORS

On some oeprating systems and environments, it may be difficult to properly set a CORS policy for local development. In these cases, add `allow_origins=["*"]` to your `.env` file.

### Build ARCHITECTURE.md

- Install `pipx`
- `pipx install archmd`
- `archmd . --out "ARCHITECTURE.md" --title="UKRDC-FastAPI Architecture"`
