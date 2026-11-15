# Weeks 1-2 API Guide (Form Schema Engine, Field Types, CRUD, Versioning, Share Link)

Open http://127.0.0.1:8000/docs. Sign up in the React app first (or use POST /auth/register).

## 0. Log in inside Swagger
1. `POST /auth/login` -> copy the `access_token` value.
2. Click **Authorize** (top right) -> paste the token -> Authorize -> Close.

## 1. Field type library
`GET /field-types` lists the 8 field types (text, number, email, dropdown, checkbox, date, file, rating)
with the configuration each accepts.

| Type | config options |
|---|---|
| text | min_length, max_length, multiline |
| number | number_type (integer / decimal), min_value, max_value, decimal_places |
| email | allowed_domains |
| dropdown | choices go in `options` |
| checkbox | min_selected, max_selected; choices go in `options` |
| date | min_date, max_date |
| file | allowed_types, max_size_mb |
| rating | scale (3-10) |

## 2. Create a form with fields  (`POST /forms`)
```json
{
  "title": "Employee Feedback",
  "description": "Quarterly feedback form",
  "fields": [
    {"field_key": "full_name", "label": "Full name", "field_type": "text",
     "is_required": true, "config": {"min_length": 2, "max_length": 100}},
    {"field_key": "age", "label": "Age", "field_type": "number",
     "config": {"number_type": "integer", "min_value": 18, "max_value": 65}},
    {"field_key": "department", "label": "Department", "field_type": "dropdown",
     "options": [{"label": "Engineering"}, {"label": "HR"}, {"label": "Sales"}]},
    {"field_key": "joined_on", "label": "Joining date", "field_type": "date",
     "config": {"min_date": "2020-01-01", "max_date": "2030-12-31"}},
    {"field_key": "satisfaction", "label": "Satisfaction", "field_type": "rating",
     "config": {"scale": 5}}
  ]
}
```
Copy the `id` from the response (this is `form_id`).

## 3. Edit the draft
- `POST /forms/{form_id}/fields` add a field
- `PATCH /forms/{form_id}/fields/{field_key}` change label / required / config / options
- `DELETE /forms/{form_id}/fields/{field_key}` remove a field
- `PUT /forms/{form_id}/fields/reorder` body: `{"field_keys": ["age", "full_name", ...]}` (every key once)

## 4. Publish  (`POST /forms/{form_id}/publish`)
Freezes the draft into a versioned snapshot and returns `share_token` + `share_url` for that version.

## 5. Shareable link (no login)
Open the `share_url`, or call `GET /public/forms/{token}` without authorizing. It returns the frozen form.

## 6. Versioning
Add / edit / remove a field on a published form -> a NEW version (v2) is created as a draft; v1 stays frozen.
Publish again -> v2 gets its own link and v1's link stops accepting respondents (HTTP 410).
`GET /forms/{form_id}/versions` shows all versions.

## 7. Archive  (`POST /forms/{form_id}/archive`)
Closes all links for the form (HTTP 410) and blocks further edits.
