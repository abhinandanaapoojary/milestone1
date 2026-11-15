from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.schemas.health import DBHealthResponse, HealthResponse
from app.services.health_service import check_database

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", app=settings.APP_NAME, version=settings.APP_VERSION)


@router.get("/health/db", response_model=DBHealthResponse)
def health_db(db: Session = Depends(get_db)):
    try:
        check_database(db)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "disconnected", "detail": str(exc)[:200]},
        )
    return DBHealthResponse(status="ok", database="connected")
