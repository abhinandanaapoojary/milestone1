import secrets
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ConditionalRule, Field, FieldOption, Form, FormStatus, FormVersion, User
from app.schemas.field_types import validate_field_config
from app.schemas.form import (
    FieldIn, FieldUpdate, FormCreate, FormOut, FormSummary, FormUpdate, OptionIn,
    PublicFormOut, ReorderRequest, VersionOut, check_options,
)


# ------------------------------------------------------------------ helpers
def _error(code: int, message: str) -> HTTPException:
    return HTTPException(status_code=code, detail=message)


def get_owned_form(db: Session, user: User, form_id: uuid.UUID) -> Form:
    form = db.get(Form, form_id)
    if form is None or form.owner_id != str(user.id):
        raise _error(status.HTTP_404_NOT_FOUND, "Form not found")
    return form


def _build_options(options: List[OptionIn]) -> List[FieldOption]:
    return [
        FieldOption(label=o.label.strip(), value=o.value, position=index)
        for index, o in enumerate(options, start=1)
    ]


def _build_field(version: FormVersion, data: FieldIn, position: int) -> Field:
    field = Field(
        field_key=data.field_key,
        label=data.label.strip(),
        field_type=data.field_type,
        placeholder=data.placeholder,
        help_text=data.help_text,
        is_required=data.is_required,
        position=position,
        config=data.config,
    )
    field.options = _build_options(data.options)
    # Appending to the parent's collection is what registers the new field with the DB session.
    version.fields.append(field)
    return field


def _find_field(version: FormVersion, field_key: str) -> Field:
    for field in version.fields:
        if field.field_key == field_key:
            return field
    raise _error(status.HTTP_404_NOT_FOUND, f"Field '{field_key}' not found")


def _clone_version(form: Form, source: FormVersion) -> FormVersion:
    """Copy a (published) version into a new draft version: fields, options and rules."""
    new_version = FormVersion(version_number=source.version_number + 1, status=FormStatus.DRAFT)
    form.versions.append(new_version)  # registers the new version with the DB session
    field_map = {}
    for old in source.fields:
        new_field = Field(
            field_key=old.field_key,
            label=old.label,
            field_type=old.field_type,
            placeholder=old.placeholder,
            help_text=old.help_text,
            is_required=old.is_required,
            position=old.position,
            config=dict(old.config or {}),
        )
        new_field.options = [
            FieldOption(label=o.label, value=o.value, position=o.position) for o in old.options
        ]
        new_version.fields.append(new_field)
        field_map[old.id] = new_field
    for rule in source.rules:
        new_version.rules.append(
            ConditionalRule(
                trigger_field=field_map[rule.trigger_field_id],
                operator=rule.operator,
                comparison_value=rule.comparison_value,
                target_field=field_map[rule.target_field_id],
                action=rule.action,
            )
        )
    return new_version


def _editable_draft(form: Form) -> FormVersion:
    """
    Returns the draft version to edit. If the latest version is already published, a NEW version
    is created (versioning): the published schema stays frozen, submissions keep pointing at it.
    """
    if form.status == FormStatus.ARCHIVED:
        raise _error(status.HTTP_409_CONFLICT, "Archived forms cannot be edited")
    latest = form.versions[-1]
    if latest.status == FormStatus.DRAFT:
        return latest
    return _clone_version(form, latest)


def build_snapshot(form: Form, version: FormVersion) -> dict:
    """Frozen copy of the form structure, stored when a version is published."""
    return {
        "form_id": str(form.id),
        "title": form.title,
        "description": form.description,
        "version_number": version.version_number,
        "fields": [
            {
                "field_key": f.field_key,
                "label": f.label,
                "field_type": f.field_type.value,
                "placeholder": f.placeholder,
                "help_text": f.help_text,
                "is_required": f.is_required,
                "position": f.position,
                "config": dict(f.config or {}),
                "options": [{"label": o.label, "value": o.value, "position": o.position} for o in f.options],
            }
            for f in version.fields
        ],
        "conditional_rules": [
            {
                "trigger_field_key": r.trigger_field.field_key,
                "operator": r.operator.value,
                "comparison_value": r.comparison_value,
                "target_field_key": r.target_field.field_key,
                "action": r.action.value,
            }
            for r in version.rules
        ],
    }


# ------------------------------------------------------------------ serializers
def _share_url(version: Optional[FormVersion], base_url: str) -> Optional[str]:
    if version is not None and version.share_token:
        return f"{base_url}/public/forms/{version.share_token}"
    return None


def serialize_version(version: FormVersion, base_url: str) -> VersionOut:
    out = VersionOut.model_validate(version)
    out.share_url = _share_url(version, base_url)
    return out


def serialize_form(form: Form, base_url: str) -> FormOut:
    latest = form.versions[-1] if form.versions else None
    return FormOut(
        id=form.id,
        title=form.title,
        description=form.description,
        status=form.status,
        created_at=form.created_at,
        updated_at=form.updated_at,
        current_version=serialize_version(latest, base_url) if latest else None,
    )


def serialize_summary(form: Form, base_url: str) -> FormSummary:
    latest = form.versions[-1]
    live = next((v for v in reversed(form.versions) if v.status == FormStatus.PUBLISHED), None)
    return FormSummary(
        id=form.id,
        title=form.title,
        description=form.description,
        status=form.status,
        latest_version_number=latest.version_number,
        share_url=_share_url(live, base_url),
        created_at=form.created_at,
        updated_at=form.updated_at,
    )


# ------------------------------------------------------------------ form CRUD
def create_form(db: Session, user: User, data: FormCreate) -> Form:
    form = Form(
        title=data.title.strip(),
        description=data.description,
        owner_id=str(user.id),
        status=FormStatus.DRAFT,
    )
    version = FormVersion(form=form, version_number=1, status=FormStatus.DRAFT)
    for index, field_data in enumerate(data.fields, start=1):
        _build_field(version, field_data, index)
    db.add(form)
    db.commit()
    db.refresh(form)
    return form


def list_forms(db: Session, user: User, status_filter: Optional[FormStatus] = None) -> List[Form]:
    query = select(Form).where(Form.owner_id == str(user.id)).order_by(Form.created_at.desc())
    if status_filter is not None:
        query = query.where(Form.status == status_filter)
    return list(db.scalars(query))


def update_form_meta(db: Session, user: User, form_id: uuid.UUID, data: FormUpdate) -> Form:
    form = get_owned_form(db, user, form_id)
    if form.status == FormStatus.ARCHIVED:
        raise _error(status.HTTP_409_CONFLICT, "Archived forms cannot be edited")
    if data.title is not None:
        form.title = data.title.strip()
    if data.description is not None:
        form.description = data.description
    db.commit()
    db.refresh(form)
    return form


# ------------------------------------------------------------------ field operations
def add_field(db: Session, user: User, form_id: uuid.UUID, data: FieldIn) -> Form:
    form = get_owned_form(db, user, form_id)
    draft = _editable_draft(form)
    if any(f.field_key == data.field_key for f in draft.fields):
        raise _error(status.HTTP_409_CONFLICT, f"A field with key '{data.field_key}' already exists")
    position = max((f.position for f in draft.fields), default=0) + 1
    _build_field(draft, data, position)
    db.commit()
    db.refresh(form)
    return form


def update_field(db: Session, user: User, form_id: uuid.UUID, field_key: str, data: FieldUpdate) -> Form:
    form = get_owned_form(db, user, form_id)
    draft = _editable_draft(form)
    field = _find_field(draft, field_key)

    if data.label is not None:
        field.label = data.label.strip()
    if data.placeholder is not None:
        field.placeholder = data.placeholder
    if data.help_text is not None:
        field.help_text = data.help_text
    if data.is_required is not None:
        field.is_required = data.is_required
    try:
        if data.config is not None:
            field.config = validate_field_config(field.field_type, data.config)
        if data.options is not None:
            check_options(field.field_type, data.options)
    except ValueError as exc:
        db.rollback()
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    if data.options is not None:
        field.options.clear()
        db.flush()  # delete old options first so reused option values don't clash
        field.options.extend(_build_options(data.options))

    db.commit()
    db.refresh(form)
    return form


def remove_field(db: Session, user: User, form_id: uuid.UUID, field_key: str) -> Form:
    form = get_owned_form(db, user, form_id)
    draft = _editable_draft(form)
    field = _find_field(draft, field_key)
    draft.fields.remove(field)  # delete-orphan removes the row (and its options / rules via cascade)
    for index, remaining in enumerate(sorted(draft.fields, key=lambda f: f.position), start=1):
        remaining.position = index
    db.commit()
    db.refresh(form)
    return form


def reorder_fields(db: Session, user: User, form_id: uuid.UUID, data: ReorderRequest) -> Form:
    form = get_owned_form(db, user, form_id)
    draft = _editable_draft(form)
    current = {f.field_key: f for f in draft.fields}
    if sorted(data.field_keys) != sorted(current):
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "field_keys must list every existing field exactly once",
        )
    for index, key in enumerate(data.field_keys, start=1):
        current[key].position = index
    db.commit()
    db.refresh(form)
    return form


# ------------------------------------------------------------------ publish / archive
def publish_form(db: Session, user: User, form_id: uuid.UUID) -> Form:
    form = get_owned_form(db, user, form_id)
    if form.status == FormStatus.ARCHIVED:
        raise _error(status.HTTP_409_CONFLICT, "Archived forms cannot be published")
    version = form.versions[-1]
    if version.status != FormStatus.DRAFT:
        raise _error(
            status.HTTP_409_CONFLICT,
            "Nothing to publish. Edit the form first; editing a published form creates a new version.",
        )
    if not version.fields:
        raise _error(status.HTTP_422_UNPROCESSABLE_ENTITY, "Add at least one field before publishing")

    for other in form.versions:
        if other is not version and other.status == FormStatus.PUBLISHED:
            other.status = FormStatus.ARCHIVED  # only the newest version accepts new respondents

    version.status = FormStatus.PUBLISHED
    version.share_token = secrets.token_urlsafe(16)
    version.published_at = datetime.now(timezone.utc)
    version.schema_snapshot = build_snapshot(form, version)
    form.status = FormStatus.PUBLISHED
    db.commit()
    db.refresh(form)
    return form


def archive_form(db: Session, user: User, form_id: uuid.UUID) -> Form:
    form = get_owned_form(db, user, form_id)
    if form.status == FormStatus.ARCHIVED:
        raise _error(status.HTTP_409_CONFLICT, "Form is already archived")
    for version in form.versions:
        if version.status == FormStatus.PUBLISHED:
            version.status = FormStatus.ARCHIVED
    form.status = FormStatus.ARCHIVED
    db.commit()
    db.refresh(form)
    return form


def list_versions(db: Session, user: User, form_id: uuid.UUID) -> List[FormVersion]:
    return list(get_owned_form(db, user, form_id).versions)


# ------------------------------------------------------------------ public access
def get_public_form(db: Session, token: str) -> PublicFormOut:
    version = db.scalar(select(FormVersion).where(FormVersion.share_token == token))
    if version is None or version.schema_snapshot is None:
        raise _error(status.HTTP_404_NOT_FOUND, "Form link not found")
    if version.status != FormStatus.PUBLISHED or version.form.status == FormStatus.ARCHIVED:
        raise _error(status.HTTP_410_GONE, "This form is no longer accepting responses")
    return PublicFormOut.model_validate(version.schema_snapshot)
