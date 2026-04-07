# Personal Space API

Backend API for the Personal Space dashboard — a personal management app with profile, resume builder, project tracker, reports, and secure vault.

## Tech Stack

- **FastAPI** + **Uvicorn** — async Python web framework
- **PostgreSQL 16** — relational database
- **SQLAlchemy 2.0** (async) — ORM
- **Alembic** — database migrations
- **Firebase Admin SDK** — authentication
- **Pydantic v2** — request/response validation
- **bcrypt** — vault PIN hashing
- **AES-256-GCM** — vault password encryption

## Quick Start

### 1. Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Firebase service account JSON

### 2. Setup

```bash
# Clone
git clone https://github.com/your-username/personal-space-api.git
cd personal-space-api

# Copy env file and fill in values
cp .env.example .env

# Start PostgreSQL
docker compose up db -d

# Install dependencies
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### 3. Or use Docker Compose for everything

```bash
docker compose up
```

The API is available at `http://localhost:8000`.

## API Docs

- **Swagger UI** — http://localhost:8000/docs
- **ReDoc** — http://localhost:8000/redoc

## Running Tests

```bash
# Create test database
createdb personal_space_test

# Run tests
pytest -v
```

## Project Structure

```
app/
├── main.py            # FastAPI app factory
├── config.py          # Settings via pydantic-settings
├── database.py        # Async SQLAlchemy engine
├── dependencies.py    # Shared FastAPI dependencies
├── auth/              # Firebase token verification
├── models/            # SQLAlchemy ORM models
├── schemas/           # Pydantic request/response schemas
├── repositories/      # Data access layer
├── services/          # Business logic layer
├── routers/           # API route handlers
├── enums/             # Python enums (mirrors frontend)
└── utils/             # Encryption, pagination helpers
```

## API Endpoints

### Authenticated (requires Firebase token)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/profile` | Get full profile |
| PUT | `/api/v1/profile/personal` | Update personal details |
| PUT | `/api/v1/profile/about` | Update about & skills |
| POST/PUT/DELETE | `/api/v1/profile/work-experience` | Work experience CRUD |
| POST/PUT/DELETE | `/api/v1/profile/education` | Education CRUD |
| PUT | `/api/v1/profile/social-links` | Update social links |
| GET/POST/PUT/DELETE | `/api/v1/companies` | Companies CRUD |
| POST | `/api/v1/companies/{id}/projects` | Create project |
| PUT/DELETE | `/api/v1/projects/{id}` | Project update/delete |
| POST | `/api/v1/projects/{id}/todos` | Create todo |
| PATCH | `/api/v1/todos/{id}` | Update todo |
| PATCH | `/api/v1/todos/bulk-update` | Kanban bulk update |
| DELETE | `/api/v1/todos/{id}` | Delete todo |
| GET/PUT/DELETE | `/api/v1/resume` | Resume CRUD |
| POST | `/api/v1/resume/generate` | Generate from profile |
| PATCH | `/api/v1/resume/template` | Change template |
| POST | `/api/v1/vault/set-pin` | Set vault PIN |
| POST | `/api/v1/vault/verify-pin` | Verify PIN |
| GET/POST/PUT/DELETE | `/api/v1/vault/categories` | Categories CRUD |
| GET/POST/PUT/DELETE | `/api/v1/vault/entries` | Entries CRUD |
| GET | `/api/v1/reports/summary` | Report summary stats |
| GET | `/api/v1/reports/completed` | Completed tasks grouped |

### Public (no auth — for portfolio site)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/public/profile` | Public profile |
| GET | `/api/v1/public/work-experience` | Work history |
| GET | `/api/v1/public/projects` | Public projects only |
| GET | `/api/v1/public/education` | Education entries |
