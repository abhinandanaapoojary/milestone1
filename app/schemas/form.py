import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import FieldType, FormStatus
from app.schemas.field_types import OPTION_TYPES, validate_field_config

FIELD_KEY_PATTERN = r"^[a-z][a-z0-9_]{0,99}$"


# ---------------------------------------------------------------- input
class OptionIn(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    value: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _default_value(self):
        if not self.value:
            self.value = self.label.strip().lower().replace(" ", "_")
        return self


def check_options(field_type: FieldType, options: List[OptionIn]) -> None:
    """Dropdown / checkbox need options; other types must not have any. Raises ValueError."""
    if field_type in OPTION_TYPES:
        if not options:
            raise ValueError(f"'{field_type.value}' fields need at least one option")
    elif options:
        raise ValueError(f"'{field_type.value}' fields cannot have options")
    values = [o.value for o in options]
    if len(values) != len(set(values)):
        raise ValueError("Option values must be unique within a field")


class FieldIn(BaseModel):
    field_key: str = Field(pattern=FIELD_KEY_PATTERN, description="Stable machine name, e.g. full_name")
    label: str = Field(min_length=1, max_length=255)
    field_type: FieldType
    placeholder: Optional[str] = Field(default=None, max_length=255)
    help_text: Optional[str] = None
    is_required: bool = False
    config: Dict[str, Any] = Field(default_factory=dict)
    options: List[OptionIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_type_rules(self):
        self.config = validate_field_config(self.field_type, self.config)
        check_options(self.field_type, self.options)
        return self


class FieldUpdate(BaseModel):
    """Field type and field_key cannot be changed; remove and re-add the field instead."""
    label: Optional[str] = Field(default=None, min_length=1, max_length=255)
    placeholder: Optional[str] = Field(default=None, max_length=255)
    help_text: Optional[str] = None
    is_required: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    options: Optional[List[OptionIn]] = None


class FormCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    fields: List[FieldIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_keys(self):
        keys = [f.field_key for f in self.fields]
        if len(keys) != len(set(keys)):
            raise ValueError("field_key values must be unique within a form")
        return self


class FormUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None


class ReorderRequest(BaseModel):
    field_keys: List[str] = Field(min_length=1, description="Every field_key, in the new order")


# ---------------------------------------------------------------- output
class OptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    label: str
    value: str
    position: int


class FieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    field_key: str
    label: str
    field_type: FieldType
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    is_required: bool
    position: int
    config: Dict[str, Any] = Field(default_factory=dict)
    options: List[OptionOut] = Field(default_factory=list)


class VersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    version_number: int
    status: FormStatus
    share_token: Optional[str] = None
    share_url: Optional[str] = None
    published_at: Optional[datetime] = None
    fields: List[FieldOut] = Field(default_factory=list)


class FormOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: FormStatus
    created_at: datetime
    updated_at: datetime
    current_version: Optional[VersionOut] = None


class FormSummary(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: FormStatus
    latest_version_number: int
    share_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- public (no login)
class PublicOptionOut(BaseModel):
    label: str
    value: str
    position: int


class PublicFieldOut(BaseModel):
    field_key: str
    label: str
    field_type: FieldType
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    is_required: bool
    position: int
    config: Dict[str, Any] = Field(default_factory=dict)
    options: List[PublicOptionOut] = Field(default_factory=list)


class PublicRuleOut(BaseModel):
    trigger_field_key: str
    operator: str
    comparison_value: Optional[str] = None
    target_field_key: str
    action: str


class PublicFormOut(BaseModel):
    title: str
    description: Optional[str] = None
    version_number: int
    fields: List[PublicFieldOut]
    conditional_rules: List[PublicRuleOut] = Field(default_factory=list)
