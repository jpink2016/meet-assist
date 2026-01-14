# Meet Assist (MVP)

## Run locally (Docker)

```bash
cd meet-assist

docker build -t meet-assist .
docker run --rm -p 5001:5000 \
  -e DB_PATH=/data/meet_assist.db \
  -v meet_assist_data:/data \
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

## Seeding
```bash
docker run --rm -it \
  -v "$PWD/backend:/app/backend" \
  -v "$PWD/backend/data:/data" \
  -w /app/backend \
  -e PYTHONPATH=/app \
  -e DATABASE_URL="sqlite:////data/meet_assist.db" \
  -e SEED_DEMO_DATA=1 \
  -e SEED_EVENTS=1 \
  meet-assist \
  python seed.py
```

## Migrations 
add column to table

generate migrations
 ```bash
docker run --rm -it \
  -v "$PWD/backend:/app/backend" \
  -v "$PWD/backend/data:/data" \
  -w /app/backend \
  -e PYTHONPATH=/app \
  -e DATABASE_URL="sqlite:////data/meet_assist.db" \
  meet-assist \
  alembic revision --autogenerate -m "describe change"
```

apply migrations
```bash
docker run --rm -it \
  -v "$PWD/backend:/app/backend" \
  -v "$PWD/backend/data:/data" \
  -w /app/backend \
  -e PYTHONPATH=/app \
  -e DATABASE_URL="sqlite:////data/meet_assist.db" \
  meet-assist \
  alembic upgrade head
```
