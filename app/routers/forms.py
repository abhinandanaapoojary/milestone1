import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import FormStatus, User
from app.schemas.field_types import describe_field_types
from app.schemas.form import (
    FieldIn, FieldUpdate, FormCreate, FormOut, FormSummary, FormUpdate, ReorderRequest, VersionOut,
)
from app.services import form_service

router = APIRouter(prefix="/forms", tags=["Forms"])
field_types_router = APIRouter(tags=["Field Types"])


def _base(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@field_types_router.get("/field-types")
def field_types():
    """The field type library: every supported type and the config it accepts."""
    return describe_field_types()


@router.post("", response_model=FormOut, status_code=status.HTTP_201_CREATED)
def create_form(
    data: FormCreate, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    form = form_service.create_form(db, user, data)
    return form_service.serialize_form(form, _base(request))


@router.get("", response_model=List[FormSummary])
def list_forms(
    request: Request,
    status_filter: Optional[FormStatus] = Query(default=None, alias="status"),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    forms = form_service.list_forms(db, user, status_filter)
    return [form_service.serialize_summary(f, _base(request)) for f in forms]


@router.get("/{form_id}", response_model=FormOut)
def get_form(
    form_id: uuid.UUID, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    form = form_service.get_owned_form(db, user, form_id)
    return form_service.serialize_form(form, _base(request))


@router.patch("/{form_id}", response_model=FormOut)
def update_form(
    form_id: uuid.UUID, data: FormUpdate, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    form = form_service.update_form_meta(db, user, form_id, data)
    return form_service.serialize_form(form, _base(request))


@router.post("/{form_id}/fields", response_model=FormOut, status_code=status.HTTP_201_CREATED)
def add_field(
    form_id: uuid.UUID, data: FieldIn, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    form = form_service.add_field(db, user, form_id, data)
    return form_service.serialize_form(form, _base(request))


@router.put("/{form_id}/fields/reorder", response_model=FormOut)
def reorder_fields(
    form_id: uuid.UUID, data: ReorderRequest, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    form = form_service.reorder_fields(db, user, form_id, data)
    return form_service.serialize_form(form, _base(request))


@router.patch("/{form_id}/fields/{field_key}", response_model=FormOut)
def update_field(
    form_id: uuid.UUID, field_key: str, data: FieldUpdate, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    form = form_service.update_field(db, user, form_id, field_key, data)
    return form_service.serialize_form(form, _base(request))


@router.delete("/{form_id}/fields/{field_key}", response_model=FormOut)
def remove_field(
    form_id: uuid.UUID, field_key: str, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    form = form_service.remove_field(db, user, form_id, field_key)
    return form_service.serialize_form(form, _base(request))


@router.post("/{form_id}/publish", response_model=FormOut)
def publish_form(
    form_id: uuid.UUID, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    """Freezes the current draft into a versioned snapshot and generates the shareable link."""
    form = form_service.publish_form(db, user, form_id)
    return form_service.serialize_form(form, _base(request))


@router.post("/{form_id}/archive", response_model=FormOut)
def archive_form(
    form_id: uuid.UUID, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    form = form_service.archive_form(db, user, form_id)
    return form_service.serialize_form(form, _base(request))


@router.get("/{form_id}/versions", response_model=List[VersionOut])
def list_versions(
    form_id: uuid.UUID, request: Request,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    versions = form_service.list_versions(db, user, form_id)
    return [form_service.serialize_version(v, _base(request)) for v in versions]
