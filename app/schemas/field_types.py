"""
Field type library.

Each field type has a configuration model describing its constraints.
`validate_field_config()` checks a config dict against the right model and returns a clean dict
that is stored in the `fields.config` JSONB column.
"""
from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.models.enums import FieldType


class _BaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TextConfig(_BaseConfig):
    """text: min / max length."""
    min_length: Optional[int] = Field(default=None, ge=0)
    max_length: Optional[int] = Field(default=None, ge=1)
    multiline: bool = False

    @model_validator(mode="after")
    def _check_range(self):
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            raise ValueError("min_length cannot be greater than max_length")
        return self


class NumberConfig(_BaseConfig):
    """number: min / max, integer or decimal."""
    number_type: Literal["integer", "decimal"] = "decimal"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    decimal_places: Optional[int] = Field(default=None, ge=0, le=6)

    @model_validator(mode="after")
    def _check(self):
        if self.min_value is not None and self.max_value is not None and self.min_value > self.max_value:
            raise ValueError("min_value cannot be greater than max_value")
        if self.number_type == "integer" and self.decimal_places not in (None, 0):
            raise ValueError("decimal_places can only be used with number_type 'decimal'")
        return self


class EmailConfig(_BaseConfig):
    """email: optionally restrict to certain domains."""
    allowed_domains: Optional[List[str]] = None

    @field_validator("allowed_domains")
    @classmethod
    def _normalise(cls, value):
        if value is None:
            return value
        return [d.strip().lower().lstrip("@") for d in value if d.strip()]


class DropdownConfig(_BaseConfig):
    """dropdown: the choices themselves are stored in `field_options`."""


class CheckboxConfig(_BaseConfig):
    """multi-checkbox: how many choices may be ticked."""
    min_selected: Optional[int] = Field(default=None, ge=0)
    max_selected: Optional[int] = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _check_range(self):
        if self.min_selected is not None and self.max_selected is not None and self.min_selected > self.max_selected:
            raise ValueError("min_selected cannot be greater than max_selected")
        return self


class DateConfig(_BaseConfig):
    """date: allowed date range."""
    min_date: Optional[date] = None
    max_date: Optional[date] = None

    @model_validator(mode="after")
    def _check_range(self):
        if self.min_date is not None and self.max_date is not None and self.min_date > self.max_date:
            raise ValueError("min_date cannot be after max_date")
        return self


class FileConfig(_BaseConfig):
    """file upload: allowed extensions and size limit."""
    allowed_types: List[str] = Field(default_factory=lambda: ["pdf", "png", "jpg", "jpeg"])
    max_size_mb: float = Field(default=5, gt=0, le=25)

    @field_validator("allowed_types")
    @classmethod
    def _normalise(cls, value):
        cleaned = [t.strip().lower().lstrip(".") for t in value if t.strip()]
        if not cleaned:
            raise ValueError("allowed_types must contain at least one file type")
        return cleaned


class RatingConfig(_BaseConfig):
    """rating: scale, e.g. 5 means 1-5 stars."""
    scale: int = Field(default=5, ge=3, le=10)


CONFIG_MODELS: Dict[FieldType, type] = {
    FieldType.TEXT: TextConfig,
    FieldType.NUMBER: NumberConfig,
    FieldType.EMAIL: EmailConfig,
    FieldType.DROPDOWN: DropdownConfig,
    FieldType.CHECKBOX: CheckboxConfig,
    FieldType.DATE: DateConfig,
    FieldType.FILE: FileConfig,
    FieldType.RATING: RatingConfig,
}

# Field types whose choices live in the field_options table
OPTION_TYPES = {FieldType.DROPDOWN, FieldType.CHECKBOX}


def validate_field_config(field_type: FieldType, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate `config` for the given field type. Raises ValueError with a readable message."""
    model = CONFIG_MODELS[field_type]
    try:
        parsed = model.model_validate(config or {})
    except ValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first["loc"])
        where = f" ({location})" if location else ""
        raise ValueError(f"Invalid config for '{field_type.value}' field{where}: {first['msg']}") from None
    return parsed.model_dump(mode="json", exclude_none=True)


def describe_field_types() -> List[Dict[str, Any]]:
    """Used by GET /field-types so a frontend can build its form-designer UI."""
    return [
        {
            "field_type": field_type.value,
            "requires_options": field_type in OPTION_TYPES,
            "config_schema": model.model_json_schema(),
        }
        for field_type, model in CONFIG_MODELS.items()
    ]
