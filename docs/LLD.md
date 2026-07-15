# 05_LLD.md

# Sentinel AI

### Low Level Design (LLD)

**Document Version:** 1.0

**Status:** Draft

**Architecture:** Modular Monolith

**Last Updated:** July 2026

---

# 1. Purpose

This document defines the internal implementation design of Sentinel AI.

It describes:

* Module responsibilities
* Folder structure
* Layered architecture
* Internal request flow
* Service boundaries
* Design patterns
* Dependency relationships

Implementation details such as business logic and algorithms are intentionally omitted.

---

# 2. Architecture Style

Sentinel AI follows a **Modular Monolith** architecture with clear domain boundaries.

Each domain owns:

* API endpoints
* Business logic
* Data access
* Validation
* Models

Cross-domain communication happens only through public service interfaces.

---

# 3. Backend Folder Structure

```text
backend/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── modules/
│   │   ├── auth/
│   │   ├── workspace/
│   │   ├── documents/
│   │   ├── conversations/
│   │   ├── orchestration/
│   │   ├── retrieval/
│   │   ├── memory/
│   │   └── ingestion/
│   │
│   ├── llm/
│   ├── vector/
│   ├── database/
│   ├── schemas/
│   ├── models/
│   ├── middleware/
│   ├── services/
│   ├── utils/
│   └── config/
│
├── tests/
├── docker/
└── requirements.txt
```

---

# 4. Layered Architecture

```text
Presentation Layer
        │
        ▼
API Layer
        │
        ▼
Application Services
        │
        ▼
Domain Logic
        │
        ▼
Repository Layer
        │
        ▼
Infrastructure
```

Each layer communicates only with the layer directly below it.

---

# 5. Module Responsibilities

## Authentication

Responsible for:

* Registration
* Login
* JWT handling
* Refresh tokens
* User identity

---

## Workspace

Responsible for:

* Workspace CRUD
* Ownership
* Isolation
* Access validation

---

## Documents

Responsible for:

* Upload
* Delete
* Metadata
* Listing

---

## Ingestion

Responsible for:

* Parsing
* Cleaning
* Chunking
* Embedding generation
* Vector indexing

---

## Retrieval

Responsible for:

* Semantic search
* Metadata filtering
* Context assembly

---

## Orchestration

Responsible for:

* Agent execution
* Workflow coordination
* Provider selection
* State management

---

## Conversations

Responsible for:

* Chat history
* Session persistence
* Context retrieval

---

## Memory

Responsible for:

* Conversation memory
* Context compression
* Future long-term memory

---

# 6. LLM Provider Abstraction

```text
LLMProvider
     │
 ┌───┼──────────────┐
 ▼   ▼              ▼
Groq DeepSeek   OpenAI
```

Every provider implements the same interface.

The orchestration layer never directly depends on a provider SDK.

---

# 7. AI Workflow

```text
User Request
      │
      ▼
Supervisor
      │
      ▼
Retriever
      │
      ▼
Vector Database
      │
      ▼
Responder
      │
      ▼
Persist Conversation
      │
      ▼
Return Response
```

---

# 8. Document Ingestion Flow

```text
Upload

↓

Validate

↓

Extract Text

↓

Normalize

↓

Chunk

↓

Generate Embeddings

↓

Store Metadata

↓

Index Vectors

↓

Ready
```

---

# 9. Request Lifecycle

### Chat Request

1. Authenticate user
2. Validate workspace
3. Load conversation context
4. Execute Supervisor
5. Retrieve knowledge
6. Generate response
7. Save conversation
8. Stream response

---

# 10. Design Patterns

The project adopts the following patterns:

* Repository Pattern
* Service Layer
* Factory Pattern
* Strategy Pattern
* Dependency Injection
* Adapter Pattern
* Provider Abstraction

---

# 11. Error Handling Strategy

Every module returns standardized application errors.

Categories:

* Validation Errors
* Authentication Errors
* Authorization Errors
* Resource Not Found
* External Provider Failure
* Vector Search Failure
* AI Provider Failure
* Internal Server Error

All errors are logged with correlation IDs.

---

# 12. Logging Strategy

Every request includes:

* Request ID
* User ID
* Workspace ID
* Execution time
* Module name
* Log level

AI execution additionally records:

* Provider
* Model
* Token usage
* Latency
* Retrieval duration

---

# 13. Dependency Rules

Modules must not directly access each other's database logic.

Allowed communication:

```text
API
↓

Service

↓

Repository

↓

Database
```

Disallowed:

* Repository → Repository
* API → Database
* API → External Provider
* Module → Module Database

---

# 14. Configuration Strategy

All configuration is environment-driven.

Examples:

* Database URL
* Redis URL
* Qdrant URL
* LLM Provider
* Model Name
* JWT Secret
* Token Expiry
* Embedding Model

No secrets may be hardcoded.

---

# 15. Future Extensibility

The modular boundaries allow future extraction into independent services:

* Orchestration Service
* Retrieval Service
* Ingestion Service
* Integration Service
* Notification Service

No domain redesign should be required during this transition.

---

# 16. Coding Standards

Implementation must follow:

* SOLID principles
* DRY
* Single Responsibility Principle
* Type-safe APIs
* Reusable services
* Small, cohesive modules
* Dependency injection
* No duplicated business logic
* Configuration over hardcoding
* Consistent error handling

---

# 17. Traceability

This implementation maps directly to the requirements defined in **01_PRD.md**.

Examples:

| Requirement                      | Implemented By                |
| -------------------------------- | ----------------------------- |
| FR-001 Authentication            | Authentication Module         |
| FR-002 Workspace Management      | Workspace Module              |
| FR-003 Document Upload           | Documents + Ingestion Modules |
| FR-005 Embedding Generation      | Ingestion Module              |
| FR-007 Multi-Agent Workflow      | Orchestration Module          |
| FR-009 Citation-backed Responses | Retrieval + Responder         |
| NFR-006 Modular Architecture     | Layered Modular Monolith      |

Every future implementation should be traceable back to a functional or non-functional requirement.
