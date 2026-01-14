# Meet Assist (MVP)

## Run locally (Docker)

```bash
cd meet-assist

docker build -t meet-assist .
docker run --rm -p 5001:5000 \
  -e DATABASE_URL="postgresql+psycopg2://meet:meetpass@host.docker.internal:5432/meetassist" \
  meet-assist

```

Open: http://localhost:5001/athletes

## What you get
- Athletes page (table)
- Add athlete form (only first/last name are freeform; all other fields are dropdowns)
- Inline editing in the table (dropdowns + text/date fields)
- Soft delete via `Active` dropdown

## DB
Defaults to SQLite (`backend/meet_assist.db`).
Set `DATABASE_URL` to point to Postgres later.

## Schema change workflow

Whenever you modify SQLAlchemy models:

Edit models (backend/app.py)

Generate a migration

docker run --rm -it \
  -v "$PWD/backend:/app/backend" \
  -w /app/backend \
  -e PYTHONPATH=/app \
  -e DATABASE_URL="postgresql+psycopg2://meet:meetpass@host.docker.internal:5432/meetassist" \
  meet-assist \
  alembic revision --autogenerate -m "describe change"


Review the generated migration file

Ensure it matches the intended schema change

Apply migrations

docker run --rm -it \
  -v "$PWD/backend:/app/backend" \
  -w /app/backend \
  -e PYTHONPATH=/app \
  -e DATABASE_URL="postgresql+psycopg2://meet:meetpass@host.docker.internal:5432/meetassist" \
  meet-assist \
  alembic upgrade head


Each database only needs to apply each migration once.

Checking migration state
docker run --rm -it \
  -v "$PWD/backend:/app/backend" \
  -w /app/backend \
  -e PYTHONPATH=/app \
  -e DATABASE_URL="postgresql+psycopg2://meet:meetpass@host.docker.internal:5432/meetassist" \
  meet-assist \
  alembic current

Database Seeding

Seeding inserts reference or demo data into an already-migrated database.

⚠️ Always run migrations before seeding.

docker run --rm -it \
  -v "$PWD/backend:/app/backend" \
  -w /app/backend \
  -e PYTHONPATH=/app \
  -e DATABASE_URL="postgresql+psycopg2://meet:meetpass@host.docker.internal:5432/meetassist" \
  -e SEED_DEMO_DATA=1 \
  -e SEED_EVENTS=1 \
  meet-assist \
  python seed.py
