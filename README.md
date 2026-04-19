# Personal Space API

Backend API for the Personal Space dashboard.

## Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2 async ORM
- Alembic
- Firebase Admin
- Pydantic v2

## Requirements

- Python 3.12+
- PostgreSQL 16+ or Docker

## Environment

Copy the example file first:

```bash
cp .env.example .env
```

Important values:

- `DATABASE_URL`
- `APP_PORT_LOCAL`
- `VAULT_ENCRYPTION_SECRET`
- `JWT_SECRET`
- `ALLOWED_ORIGINS`
- `FIREBASE_SERVICE_ACCOUNT_KEY` or `FIREBASE_SERVICE_ACCOUNT_PATH`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `PUBLIC_TESTIMONIAL_CAPTCHA_SECRET`
- `PUBLIC_PORTFOLIO_GEO_LOOKUP_ENABLED`
- `PUBLIC_PORTFOLIO_GEO_LOOKUP_URL`

## Local Setup

### Option 1: Local API + Docker Postgres

Start Postgres:

```bash
docker compose up db -d
```

Install dependencies:

```bash
pip install -e ".[dev]"
```

Run migrations:

```bash
./scripts/check_alembic_heads.sh
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Default local URLs:

- API: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Option 2: Docker Compose for API + DB

```bash
docker compose up --build
```

This starts:

- API on `APP_PORT_LOCAL` (default `8000`)
- Postgres on `5432`

## Production Setup

This service is container-friendly and can be deployed to Railway, Render, Fly.io, or any platform that can run a Python container.

### 1. Set production environment variables

At minimum:

- `DATABASE_URL`
- `PORT`
- `VAULT_ENCRYPTION_SECRET`
- `JWT_SECRET`
- `ALLOWED_ORIGINS`
- `ENVIRONMENT=production`
- `DEBUG=false`
- `FIREBASE_SERVICE_ACCOUNT_KEY` or `FIREBASE_SERVICE_ACCOUNT_PATH`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Recommended:

- `PUBLIC_TESTIMONIAL_CAPTCHA_SECRET`
- `PUBLIC_PORTFOLIO_GEO_LOOKUP_ENABLED=true`
- `PUBLIC_PORTFOLIO_GEO_LOOKUP_URL=https://ipapi.co/{ip}/json/`
- explicit bucket names if they differ from defaults

### 2. Build the container

```bash
docker build -t personal-space-api .
```

### 3. Run database migrations

Run this before serving traffic:

```bash
./scripts/check_alembic_heads.sh
alembic upgrade head
```

### 4. Start the app

The included `Dockerfile` already runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

If you run it without Docker:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Database

Default local database from `docker-compose.yml`:

- `personal_space`

If you use a local PostgreSQL install instead of Docker, create the database first:

```bash
createdb personal_space
```

Then run:

```bash
alembic upgrade head
```

## Migrations

Check the migration graph before creating, merging, or applying migrations:

```bash
./scripts/check_alembic_heads.sh
```

If this fails, resolve the migration graph before running `alembic upgrade head`.

Useful commands:

```bash
alembic current
alembic heads
alembic history --verbose
alembic upgrade head
```

## Tests

Tests expect a separate database:

- `personal_space_test`

Create it first:

```bash
createdb personal_space_test
```

Run tests:

```bash
pytest -v
```

## Common Commands

Install dependencies:

```bash
pip install -e ".[dev]"
```

Run the API:

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

Run lint:

```bash
ruff check .
```

## Project Structure

```text
app/
├── auth/
├── enums/
├── models/
├── repositories/
├── routers/
├── schemas/
├── services/
├── utils/
├── config.py
├── database.py
├── dependencies.py
└── main.py
```
