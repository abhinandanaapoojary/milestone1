"""Quick check that the app can reach PostgreSQL.  Run:  python -m scripts.verify_connection"""
from sqlalchemy import text

from app.core.config import settings
from app.database.session import engine

try:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
    print("Database connection SUCCESSFUL")
    print(version)
except Exception as exc:  # noqa: BLE001
    print("Database connection FAILED:", exc)
    print("Check .env values (DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME) and that PostgreSQL is running.")
    print("URL used (password hidden):", settings.DATABASE_URL.replace(settings.DB_PASSWORD, "****") if settings.DB_PASSWORD else settings.DATABASE_URL)
