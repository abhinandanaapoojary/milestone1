from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.form import PublicFormOut
from app.services import form_service

router = APIRouter(prefix="/public", tags=["Public (no login)"])


@router.get("/forms/{token}", response_model=PublicFormOut)
def get_public_form(token: str, db: Session = Depends(get_db)):
    """What a respondent opens from the shareable link. No authentication needed."""
    return form_service.get_public_form(db, token)
