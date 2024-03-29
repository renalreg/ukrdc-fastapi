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

## Run the API server

`poetry run uvicorn ukrdc_fastapi.main:app` or `./run.sh`

## Run the utility scripts

This application includes a small number of utility scripts which make use of the internal API functionality to simplify some tasks.

These scripts require an activate database connection and a corresponding `.env` file in the project root, just like the API server.

### Create the local user-preferences `sqlite` database

See "Create local databases" section above

### Automatically resolve type-9 JTRACE work items

`poetry run python scripts/type_9_resolver/process.py {work item ID}`

Type-9 work items, in essence, are raised when a data file is received which simultaneously changes a local hospital ID as well as demographics. In order to close the work item, two things need to happen:

1. The work item attributes must be manually checked to ensure they do indeed correspond to the claimed patient.
2. Data files blocked by the work item must be reprocessed in two parts. First, we modify the incoming file to use the _current_ local hospital number, but include the new demographics. Then, we reprocess the original incoming file with both the new local hospital number and new demographics.

This script automates step 2.

### Find all records with multiple UKRDC IDs

`poetry run python scripts/ukrdc_dupes/find.py`

Results will be saved to a file `dupes.json`

### Query and analyse PKB membership creation events

We include scripts to query and analyse who created PKB memberships, and when they were created.
This is useful for identifying which hospitals are engaging with the process.

#### Query events

`poetry run python scripts/analytics/query_memberships.py`

This will create two output files used in analysis, `scripts/analytics/output/events.json` and `scripts/analytics/output/uids.json`

#### Analyse events

`scripts/analytics/analyse_memberships.py`

This will create timeline plots for each user in `scripts/analytics/output/plot/`

### Testing scripts

Scripts in `scripts/testing` are one-off scripts used to check or verify functionality before being included in the API. Things like performance benchmarks used to justify API code changes live here.

## Developer notes

### Autofix issues before commit

- `poetry run ruff --fix ./ukrdc_fastapi`
- `poetry run ruff format ./ukrdc_fastapi`

### Versioning, releases, and deployments

See our [internal Confluence documentation](https://renalregistry.atlassian.net/wiki/spaces/UDF/pages/2516680711/Releases+and+Deployment) for up-to-date guidelines on versioning, releases, and deployment.


### Build client libraries

Client libraries are automatically built and published on every release.

For development purposes, you can [manually trigger the Build Client Libraries workflow](https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow) to publish a snapshot release.

#### Local `typescript-axios-client` snapshot

`poetry run python clients/generate_spec.py`

`npx @openapitools/openapi-generator-cli generate -c ./clients/typescript-axios-client/config.json -i ./clients/openapi.json -g typescript-axios -o ./typescript-axios-client --additional-properties=snapshot=true`

`npx typedoc ./typescript-axios-client/index.ts --out ./docs/typescript-axios-client`

### Local CORS

On some oeprating systems and environments, it may be difficult to properly set a CORS policy for local development. In these cases, add `allow_origins=["*"]` to your `.env` file.
