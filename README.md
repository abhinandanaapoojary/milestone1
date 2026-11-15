# FormCraft – Smart Form Builder (Milestone 1)

Backend: FastAPI + PostgreSQL + SQLAlchemy + Alembic. Frontend: React (Vite).
Milestone 1 = project setup, database schema, user sign-up / login, and the dashboard shown after login.

FastAPI + PostgreSQL + SQLAlchemy + Alembic backend for dynamic forms with conditional logic.

## Project structure
```
form_builder/
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── core/config.py     # settings loaded from .env
│   ├── database/          # engine, session, Base
│   ├── models/            # SQLAlchemy models (Task 2 schema)
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # business logic
│   └── routers/           # API routes (health for now)
├── alembic/               # migrations (versions/0001_initial_schema.py)
├── scripts/               # verify_connection.py, seed_sample.py
├── frontend/              # React app (login, signup, dashboard)
├── docs/DATABASE_SCHEMA.md
├── .env / .env.example
├── docker-compose.yml     # optional Postgres
└── requirements.txt
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate            # Windows   (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
```

1. Start PostgreSQL (installed locally, or `docker compose up -d db`).
2. Create the database (skip if using docker):  `CREATE DATABASE form_builder;`
3. Put your real password in `.env` (`DB_PASSWORD=...`).

## Verify database connection
```bash
python -m scripts.verify_connection
```

## Run migrations (creates all tables)
```bash
alembic upgrade head
```
(Optional sample data: `python -m scripts.seed_sample`)

## Run the backend
```bash
uvicorn app.main:app --reload
```
- Swagger UI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- DB health: http://127.0.0.1:8000/health/db  → `{"status":"ok","database":"connected"}`

## Future schema changes
```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Run the frontend (login, sign-up, dashboard)
Open a SECOND terminal (keep the backend running in the first):
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 :
1. Click "Create an account" and sign up (name, email, password).
2. You land on the **Dashboard Overview** page: welcome message + project title.
3. "Log out" returns to the login page; log back in with the same email/password.

## Auth API
- `POST /auth/register` – create user
- `POST /auth/login` – returns JWT token
- `GET /auth/me` – current user (needs token)
- `GET /dashboard/overview` – name + project title (needs token)

## Form APIs (Weeks 1-2)
See `docs/API_GUIDE.md` for a step-by-step Swagger walkthrough.
- `GET /field-types` - field type library
- `POST /forms`, `GET /forms`, `GET /forms/{id}`, `PATCH /forms/{id}`
- `POST /forms/{id}/fields`, `PATCH|DELETE /forms/{id}/fields/{field_key}`, `PUT /forms/{id}/fields/reorder`
- `POST /forms/{id}/publish`, `POST /forms/{id}/archive`, `GET /forms/{id}/versions`
- `GET /public/forms/{token}` - respondent access via shareable link (no login)
