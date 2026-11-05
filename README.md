# User Management API

A REST API built with FastAPI, SQLAlchemy, SQLite/PostgreSQL, and Slack Incoming Webhooks.

## Features

- Create, list, retrieve, update, and delete users.
- UUID primary keys and database-enforced unique email addresses.
- Pydantic validation for names, emails, and roles (`admin`, `member`, `viewer`).
- `created_at` is preserved on updates; `updated_at` changes on updates.
- Slack notifications for successful create/update/delete operations.
- Notification failures are logged and do not roll back successful database operations.
- Swagger UI at `/docs` and ReDoc at `/redoc`.
- Pytest test suite and Postman collection.

## Requirements

- Python 3.11+
- pip
- PostgreSQL only if you choose PostgreSQL; SQLite works out of the box.

## Setup (SQLite - quickest)

```bash
git clone https://github.com/YOUR_USERNAME/user-management-api.git
cd user-management-api

python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

On Windows Command Prompt, use `copy .env.example .env` instead of `cp`.

The default `.env` uses SQLite and creates `users.db` automatically when the application starts.

## Setup (PostgreSQL)

Create a database, for example:

```sql
CREATE DATABASE user_management;
```

Then set `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/user_management
```

Do not commit `.env`. The `.gitignore` file excludes it.

## Configure Slack notifications

1. In your Slack workspace, create or select an app.
2. Enable **Incoming Webhooks** and add a webhook to the target channel.
3. Copy the webhook URL.
4. Set `SLACK_WEBHOOK_URL` in `.env`.

If no webhook is configured, the API still works and logs that notifications were skipped. If Slack returns an error or times out, the error is logged and the committed database operation remains successful.

## Run the API

```bash
uvicorn app.main:app --reload
```

- API base: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## API examples

### Create

```bash
curl -X POST http://localhost:8000/users \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Alex Johnson","email":"alex@example.com","role":"member"}'
```

### List

```bash
curl http://localhost:8000/users
```

### Get by ID

```bash
curl http://localhost:8000/users/REPLACE_WITH_UUID
```

### Update

```bash
curl -X PATCH http://localhost:8000/users/REPLACE_WITH_UUID \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Alex Updated","role":"admin"}'
```

### Delete

```bash
curl -X DELETE http://localhost:8000/users/REPLACE_WITH_UUID
```

Import `postman_collection.json` into Postman for ready-made requests.

## Run tests

```bash
python -m pytest -v
```

Tests use an isolated in-memory SQLite database and mock the Slack notifier.

## Project structure

```text
user-management-api/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── notifications.py
│   ├── schemas.py
│   └── routers/
│       ├── __init__.py
│       └── users.py
├── tests/
│   ├── conftest.py
│   └── test_users.py
├── .env.example
├── .gitignore
├── postman_collection.json
├── requirements.txt
└── schema.sql
```

## HTTP status behavior

| Scenario | Status |
|---|---:|
| User created | 201 |
| Read/update/delete successful | 200 |
| Invalid body / invalid ID / invalid pagination | 400 or FastAPI 422 |
| User not found | 404 |
| Duplicate email | 409 |
| Unexpected database/application error | 500 |
| Slack unavailable | CRUD response remains successful; error logged |

A custom request-validation handler maps invalid request bodies (including missing fields, invalid email, and invalid role) to `400 Bad Request` to match the assignment.

## Design notes and limitations

- CRUD endpoints are synchronous and use SQLAlchemy's synchronous session.
- Slack delivery is best-effort and synchronous with a five-second timeout. A production system with high throughput should use a background queue (Celery/RQ) and a transactional outbox so notification delivery can be retried reliably.
- `Base.metadata.create_all()` is used to keep this take-home project easy to run. For production schema evolution, use Alembic migrations.
- The API does not include authentication/authorization because it was outside the assignment scope.
- SQLite is the default local database; PostgreSQL is supported by changing `DATABASE_URL`.

## GitHub submission

Create an empty repository on GitHub named `user-management-api`, then run:

```bash
git init
git add .
git commit -m "Build user management API with Slack notifications"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/user-management-api.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. If Git asks for authentication, use GitHub's browser sign-in or a Personal Access Token; do not put credentials in the remote URL.

After pushing, verify the README, source files, and Postman collection are visible on GitHub. Confirm `.env` and `users.db` are not committed.
