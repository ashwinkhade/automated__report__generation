# API Documentation

The backend serves an OpenAPI/Swagger UI at **`/docs`** and ReDoc at **`/redoc`** while running.

Base URL: `http://<host>:8000/api/v1`

## Authentication

All endpoints (except `/auth/register`, `/auth/login`, `/health`) require a Bearer token.

```
Authorization: Bearer <access_token>
```

### POST `/auth/register`

```json
{
  "email": "user@example.com",
  "username": "user",
  "password": "secret123",
  "full_name": "Demo User"
}
```
**Returns:** `{ access_token, token_type, user }`

### POST `/auth/login` (form-encoded)
- `username` — username **or** email
- `password`

**Returns:** `{ access_token, token_type, user }`

### GET `/auth/me`
Returns the current user.

---

## Datasets

### POST `/datasets/upload`  (multipart/form-data)
- `file` — CSV / XLS / XLSX, max 50 MB

Runs ETL, stores cleaned metadata, returns `DatasetOut`.

### GET `/datasets`
List your datasets.

### GET `/datasets/{id}/preview`
Returns first 20 rows + column list.

### DELETE `/datasets/{id}`
Removes dataset and underlying file.

---

## Reports

### POST `/reports`
```json
{ "dataset_id": 1, "title": "Q1 Sales Report" }
```
Starts generation in the background. Poll `GET /reports/{id}` until `status == "completed"`.

### GET `/reports`
List your reports.

### GET `/reports/{id}`
Full report including KPIs, charts, insights, recommendations.

### GET `/reports/{id}/download/{fmt}`
`fmt` ∈ `html | pdf | docx` — downloads the rendered report.

### DELETE `/reports/{id}`
Removes report and exported files.

### POST `/reports/chat`
```json
{ "report_id": 1, "question": "What drove revenue growth this week?" }
```
Returns: `{ "answer": "…" }`

---

## Health

### GET `/health`
Returns service health and feature toggles (`llm_enabled`, `s3_enabled`).
