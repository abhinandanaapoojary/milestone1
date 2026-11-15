# Database Schema (Task 2)

## ERD (Mermaid – renders on GitHub / VS Code Mermaid preview)

```mermaid
erDiagram
    FORMS ||--o{ FORM_VERSIONS : "has versions"
    FORM_VERSIONS ||--o{ FIELDS : "contains"
    FORM_VERSIONS ||--o{ CONDITIONAL_RULES : "defines"
    FORM_VERSIONS ||--o{ SUBMISSIONS : "receives"
    FIELDS ||--o{ FIELD_OPTIONS : "has choices"
    FIELDS ||--o{ CONDITIONAL_RULES : "trigger / target"
    SUBMISSIONS ||--o{ RESPONSE_VALUES : "holds answers"
    FIELDS ||--o{ RESPONSE_VALUES : "answered by"

    FORMS { uuid id PK
            string title
            text description
            string owner_id
            enum status
            timestamptz created_at
            timestamptz updated_at }
    FORM_VERSIONS { uuid id PK
            uuid form_id FK
            int version_number
            enum status
            string share_token UK
            jsonb schema_snapshot
            timestamptz published_at }
    FIELDS { uuid id PK
            uuid form_version_id FK
            string field_key
            string label
            enum field_type
            bool is_required
            int position
            jsonb config }
    FIELD_OPTIONS { uuid id PK
            uuid field_id FK
            string label
            string value
            int position }
    CONDITIONAL_RULES { uuid id PK
            uuid form_version_id FK
            uuid trigger_field_id FK
            enum operator
            string comparison_value
            uuid target_field_id FK
            enum action }
    SUBMISSIONS { uuid id PK
            uuid form_version_id FK
            enum status
            timestamptz started_at
            timestamptz submitted_at
            int duration_seconds }
    RESPONSE_VALUES { uuid id PK
            uuid submission_id FK
            uuid field_id FK
            text value_text
            numeric value_number
            date value_date
            jsonb value_json
            string file_path }
```

## Tables

| Table | Purpose |
|---|---|
| `forms` | Top-level form (title, owner, status draft/published/archived). |
| `form_versions` | Versioned snapshot of a form. Publishing freezes it (`schema_snapshot`, `published_at`); editing a published form creates version N+1. `share_token` = unique shareable link per version. |
| `fields` | Questions of a version. `field_type` = text, number, email, dropdown, checkbox, date, file, rating. `config` (JSONB) holds per-type constraints (min/max length, number range, date range, file type/size, rating scale). |
| `field_options` | Choices for dropdown / multi-checkbox fields. |
| `conditional_rules` | "If trigger_field `operator` value then `action` target_field". Operators: equals, not_equals, contains, greater_than, is_empty. Actions: show, hide, require. |
| `submissions` | One respondent attempt, linked to the exact version. `started_at`, `submitted_at`, `status`, `duration_seconds` give completion rate and average time. |
| `response_values` | One answer per field per submission, stored in typed columns (text / number / date / json / file info). |

## Key design decisions
- **Versioning**: fields and rules belong to a *version*, so old submissions always match the schema they were answered against.
- **Typed response columns** make filtering and analytics (counts, averages, distributions) fast without parsing JSON.
- **Integrity**: unique `(form_id, version_number)`, unique `(form_version_id, field_key)`, unique `(submission_id, field_id)`, CHECK that a rule's trigger and target fields differ, `ON DELETE CASCADE` everywhere.
- **Indexes** on all foreign keys, `status`, `submitted_at`, `share_token`.
