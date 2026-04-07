# Personal Space API

Backend API for the Personal Space dashboard and portfolio site.

It currently supports:

- profile management
- work experience workspaces
- projects and todos
- resume builder
- reports
- secure vault

## Current Domain Shape

The backend has been refactored so project tracking now hangs off `work_experiences` instead of a separate `companies` table.

The main relationships are:

- `users -> profile`
- `profile -> work_experiences`
- `work_experiences -> projects`
- `projects -> todos`
- `profile -> education_entries`
- `profile -> social_links`
- `profile -> skills`
- `users -> resume`
- `users -> vault_*`

This means a current work experience can be treated as the active project workspace in the frontend.

## Tech Stack

- FastAPI + Uvicorn
- PostgreSQL 16
- SQLAlchemy 2.0 async ORM
- Alembic
- Firebase Admin SDK
- Pydantic v2
- bcrypt
- cryptography / AES-based password encryption

## Prerequisites

- Python 3.12+
- PostgreSQL 16+ or Docker
- Firebase service account JSON

## Environment Setup

Copy the env template:

```bash
cp .env.example .env
```

Important values:

- `DATABASE_URL`
- `FIREBASE_SERVICE_ACCOUNT_KEY` or `FIREBASE_SERVICE_ACCOUNT_PATH`
- `VAULT_ENCRYPTION_SECRET`
- `JWT_SECRET`
- `ALLOWED_ORIGINS`

Notes:

- `DATABASE_URL` should point to your local Postgres database.
- You can either paste the Firebase service account JSON into `FIREBASE_SERVICE_ACCOUNT_KEY` as one line, or use `FIREBASE_SERVICE_ACCOUNT_PATH`.
- `VAULT_ENCRYPTION_SECRET` should be a stable secret, not a placeholder.

## Local Development

### Option 1: Local Python + Docker Postgres

Start the database:

```bash
docker compose up db -d
```

Install dependencies:

```bash
pip install -e ".[dev]"
```

Run migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).

### Option 2: Docker Compose for API + DB

```bash
docker compose up --build
```

This starts:

- API on port `8000`
- Postgres on port `5432`

## Database Setup

The default local database name in `docker-compose.yml` is:

- `personal_space`

If you are using a local Postgres install instead of Docker, create the database manually first:

```bash
createdb personal_space
```

Then run:

```bash
alembic upgrade head
```

## Test Setup

The tests expect a separate database:

- `personal_space_test`

Create it before running tests:

```bash
createdb personal_space_test
```

Then run:

```bash
pytest -v
```

If you skip this step, tests will fail during setup because the test database does not exist.

## API Docs

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Common Commands

Install dependencies:

```bash
pip install -e ".[dev]"
```

Run the app:

```bash
uvicorn app.main:app --reload
```

Run migrations:

```bash
alembic upgrade head
```

Run tests:

```bash
pytest -v
```

Lint:

```bash
ruff check .
```

## Project Structure

```text
app/
├── main.py
├── config.py
├── database.py
├── dependencies.py
├── auth/
├── models/
├── repositories/
├── routers/
├── schemas/
├── services/
├── enums/
└── utils/
```

## API Overview

### Authenticated endpoints

Profile:

- `GET /api/v1/profile`
- `PUT /api/v1/profile/personal`
- `PUT /api/v1/profile/about`
- `POST /api/v1/profile/work-experience`
- `PUT /api/v1/profile/work-experience/{entry_id}`
- `DELETE /api/v1/profile/work-experience/{entry_id}`
- `POST /api/v1/profile/education`
- `PUT /api/v1/profile/education/{entry_id}`
- `DELETE /api/v1/profile/education/{entry_id}`
- `PUT /api/v1/profile/social-links`

Workspaces and projects:

- `GET /api/v1/work-experiences`
- `GET /api/v1/work-experiences?current_only=true`
- `POST /api/v1/work-experiences/{work_experience_id}/projects`
- `PUT /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/todos`
- `PATCH /api/v1/todos/{todo_id}`
- `PATCH /api/v1/todos/bulk-update`
- `DELETE /api/v1/todos/{todo_id}`

Resume:

- `GET /api/v1/resume`
- `PUT /api/v1/resume`
- `DELETE /api/v1/resume`
- `POST /api/v1/resume/generate`
- `PATCH /api/v1/resume/template`

Vault:

- `POST /api/v1/vault/set-pin`
- `POST /api/v1/vault/verify-pin`
- `GET /api/v1/vault/categories`
- `POST /api/v1/vault/categories`
- `PUT /api/v1/vault/categories/{category_id}`
- `DELETE /api/v1/vault/categories/{category_id}`
- `GET /api/v1/vault/entries`
- `POST /api/v1/vault/entries`
- `PUT /api/v1/vault/entries/{entry_id}`
- `DELETE /api/v1/vault/entries/{entry_id}`

Reports:

- `GET /api/v1/reports/summary`
- `GET /api/v1/reports/completed`

### Public endpoints

- `GET /api/v1/public/profile`
- `GET /api/v1/public/work-experience`
- `GET /api/v1/public/projects`
- `GET /api/v1/public/education`

## Notes For Existing Databases

The repository was refactored from `companies -> projects` to `work_experiences -> projects`.

If you already have an existing database with company data, do not rely on the edited initial migration alone. You should create a new Alembic migration that:

- adds `projects.work_experience_id`
- backfills it from existing company/work-experience mappings
- removes `projects.company_id`
- drops the `companies` table

The current `alembic/versions/94fca1a390c3_initial.py` is now aligned for fresh setups.
