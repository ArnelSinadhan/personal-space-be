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

- `APP_PORT_LOCAL`
- `DATABASE_URL`
- `FIREBASE_SERVICE_ACCOUNT_KEY` or `FIREBASE_SERVICE_ACCOUNT_PATH`
- `VAULT_ENCRYPTION_SECRET`
- `JWT_SECRET`
- `ALLOWED_ORIGINS`
- `PUBLIC_TESTIMONIAL_CAPTCHA_SECRET`

Notes:

- `APP_PORT_LOCAL` controls the local API port when you run with Docker Compose.
- `DATABASE_URL` should point to your local Postgres database.
- You can either paste the Firebase service account JSON into `FIREBASE_SERVICE_ACCOUNT_KEY` as one line, or use `FIREBASE_SERVICE_ACCOUNT_PATH`.
- `VAULT_ENCRYPTION_SECRET` should be a stable secret, not a placeholder.
- In Railway, the container should bind to the platform-provided `PORT` variable.
- `PUBLIC_TESTIMONIAL_CAPTCHA_SECRET` is the Cloudflare Turnstile secret key used to validate public testimonial submissions.

## Cloudflare Turnstile Setup

The public testimonial endpoint supports Cloudflare Turnstile protection.

This backend expects:

- `PUBLIC_TESTIMONIAL_CAPTCHA_SECRET` in `personal-space-be`

The portfolio frontend expects:

- `NEXT_PUBLIC_TURNSTILE_SITE_KEY` in `personal-portfolio-v2`

To create the keys:

1. Open the Cloudflare dashboard and go to Turnstile.
2. Select `Add widget`.
3. Give it a name like `portfolio-testimonials`.
4. Add the hostnames where the portfolio runs, for example:
   - `localhost`
   - your production portfolio domain
5. Choose a widget mode. `Managed` is a good default.
6. Create the widget and copy both values:
   - `sitekey` for the frontend
   - `secret key` for the backend

Example env values:

```env
# personal-portfolio-v2
NEXT_PUBLIC_TURNSTILE_SITE_KEY=your-cloudflare-turnstile-sitekey

# personal-space-be
PUBLIC_TESTIMONIAL_CAPTCHA_SECRET=your-cloudflare-turnstile-secret
```

References:

- [Cloudflare Turnstile: Get started](https://developers.cloudflare.com/turnstile/get-started/)
- [Cloudflare Turnstile: Dashboard widget management](https://developers.cloudflare.com/turnstile/get-started/widget-management/dashboard/)

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

The API will be available at [http://localhost:8000](http://localhost:8000) by default, or whatever value you set for `APP_PORT_LOCAL`.

### Option 2: Docker Compose for API + DB

```bash
docker compose up --build
```

This starts:

- API on port `APP_PORT_LOCAL` (default `8000`)
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

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs) by default
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc) by default

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
- `DELETE /api/v1/todos/{todo_id}`

Resume:

- `GET /api/v1/resume`
- `PUT /api/v1/resume`

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
