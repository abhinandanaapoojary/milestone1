import enum


class FormStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class FieldType(str, enum.Enum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"      # multi-checkbox
    DATE = "date"
    FILE = "file"
    RATING = "rating"


class ConditionOperator(str, enum.Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    GREATER_THAN = "greater_than"
    IS_EMPTY = "is_empty"


class RuleAction(str, enum.Enum):
    SHOW = "show"
    HIDE = "hide"
    REQUIRE = "require"


class SubmissionStatus(str, enum.Enum):
    STARTED = "started"
    SUBMITTED = "submitted"
