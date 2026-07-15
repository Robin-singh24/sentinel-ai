# 06_API_SPEC.md

# Sentinel AI
## API Specification

**Version:** 1.0  
**Status:** Draft  
**API Style:** RESTful  
**Authentication:** JWT Bearer Token

---

# 1. Overview

The Sentinel AI API exposes REST endpoints for authentication, workspace management, document ingestion, conversations, and AI-powered investigations.

Base URL (Development)

```text
http://localhost:8000/api/v1
```

---

# 2. Authentication

Protected endpoints require:

```http
Authorization: Bearer <JWT_TOKEN>
```

---

# 3. Standard Response Format

## Success

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

## Error

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Requested resource not found"
  }
}
```

---

# 4. Authentication APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register a user |
| POST | /auth/login | Login |
| POST | /auth/refresh | Refresh access token |
| POST | /auth/logout | Logout |

---

# 5. Workspace APIs

| Method | Endpoint |
|--------|----------|
| POST | /workspaces |
| GET | /workspaces |
| GET | /workspaces/{workspaceId} |
| PUT | /workspaces/{workspaceId} |
| DELETE | /workspaces/{workspaceId} |

---

# 6. Document APIs

| Method | Endpoint |
|--------|----------|
| POST | /workspaces/{workspaceId}/documents |
| GET | /workspaces/{workspaceId}/documents |
| DELETE | /documents/{documentId} |
| GET | /documents/{documentId}/status |

Supported formats:
- PDF
- Markdown
- TXT

---

# 7. Conversation APIs

| Method | Endpoint |
|--------|----------|
| POST | /conversations |
| GET | /conversations |
| GET | /conversations/{conversationId} |
| DELETE | /conversations/{conversationId} |

---

# 8. Chat APIs

| Method | Endpoint |
|--------|----------|
| POST | /conversations/{conversationId}/messages |
| POST | /conversations/{conversationId}/messages/stream |

Streaming uses **Server-Sent Events (text/event-stream)**.

Example Response

```json
{
  "success": true,
  "message": "Response generated",
  "data": {
    "response": "...",
    "citations": [],
    "confidence": 0.94
  }
}
```

---

# 9. Health APIs

- GET /health
- GET /health/live
- GET /health/ready

---

# 10. HTTP Status Codes

200, 201, 204, 400, 401, 403, 404, 409, 422, 429, 500

---

# 11. API Versioning

Current:

```text
/api/v1
```

Future:

```text
/api/v2
```

---

# 12. Requirement Traceability

| Requirement | API |
|------------|-----|
| FR-001 | Authentication |
| FR-002 | Workspace |
| FR-003 | Documents |
| FR-007 | Messages |
| FR-008 | Conversations |
| FR-009 | Chat Responses |
