# 04_DATABASE.md

# Sentinel AI

### Database Design Document

**Document Version:** 1.0

**Status:** Draft

**Database:** PostgreSQL + Qdrant + Redis

**Last Updated:** July 2026

---

# 1. Purpose

This document defines the persistence layer of Sentinel AI.

The platform uses a polyglot persistence approach:

| Database   | Purpose                               |
| ---------- | ------------------------------------- |
| PostgreSQL | Relational application data           |
| Qdrant     | Vector embeddings & semantic search   |
| Redis      | Caching, sessions and temporary state |

---

# 2. Database Architecture

```text
                     Sentinel AI

                            │

        ┌───────────────────┼────────────────────┐

        ▼                   ▼                    ▼

 PostgreSQL             Qdrant               Redis

 Relational Data      Vector Search      Cache / Sessions
```

Each datastore has a single responsibility.

---

# 3. PostgreSQL Schema

## User

Represents registered users.

Fields

* id (UUID)
* email
* password_hash
* first_name
* last_name
* avatar_url
* is_active
* created_at
* updated_at

Relationships

* One User → Many Workspaces
* One User → Many Conversations

---

## Workspace

Represents an isolated knowledge environment.

Fields

* id
* owner_id
* name
* description
* created_at
* updated_at

Relationships

* One Workspace → Many Documents
* One Workspace → Many Conversations

---

## Document

Represents uploaded knowledge.

Fields

* id
* workspace_id
* filename
* original_filename
* mime_type
* file_size
* storage_path
* status
* checksum
* uploaded_by
* uploaded_at

Status

* Uploaded
* Processing
* Indexed
* Failed

---

## DocumentChunk

Metadata for each chunk.

Actual vectors live in Qdrant.

Fields

* id
* document_id
* chunk_index
* content
* token_count
* vector_id
* metadata
* created_at

---

## Conversation

Represents a chat session.

Fields

* id
* workspace_id
* user_id
* title
* created_at
* updated_at

---

## Message

Stores conversation messages.

Fields

* id
* conversation_id
* role
* content
* citations
* confidence
* token_usage
* latency
* created_at

Role

* User
* Assistant
* System

---

## AuditLog

Stores security events.

Fields

* id
* user_id
* action
* resource
* ip_address
* timestamp

Future use

* Compliance
* Security
* Monitoring

---

# 4. Entity Relationships

```text
User
 │
 ├──────────────┐
 ▼              ▼
Workspace    Conversation
 │              │
 ▼              ▼
Document     Message
 │
 ▼
DocumentChunk
```

---

# 5. Qdrant Collections

Collection

workspace_documents

Each vector represents one document chunk.

Metadata

* workspace_id
* document_id
* chunk_id
* filename
* page_number
* source
* created_at

Embedding Model

Configurable.

Initially:

BAAI BGE-M3

Future:

Provider independent.

---

# 6. Redis Usage

Redis stores temporary application state.

Keys

Authentication

* Refresh Tokens

Caching

* Conversation Context
* Frequent Retrieval Results

Future

* Pub/Sub
* Rate Limiting
* Distributed Locks

---

# 7. Indexing Strategy

PostgreSQL

Indexes

User

* email

Workspace

* owner_id

Document

* workspace_id
* status

Conversation

* workspace_id
* user_id

Message

* conversation_id

---

Qdrant

Indexes

* workspace_id
* document_id
* filename

---

# 8. Data Lifecycle

Document

```text
Upload

↓

Processing

↓

Chunking

↓

Embedding

↓

Vector Indexing

↓

Available

↓

Archived

↓

Deleted
```

Conversation

```text
Question

↓

Retrieve

↓

Generate

↓

Store

↓

Future Context
```

---

# 9. Constraints

Workspace Isolation

Documents cannot be accessed across workspaces.

Cascade Rules

Deleting a workspace deletes:

* Documents
* Chunks
* Conversations
* Messages

Deleting a document removes:

* PostgreSQL metadata
* Qdrant vectors

---

# 10. Storage Strategy

Files

MVP

Local Storage

Production

AWS S3

Only metadata is stored inside PostgreSQL.

---

# 11. Migration Strategy

Migration Tool

Alembic

Versioned schema migrations.

Backward-compatible changes preferred.

---

# 12. Backup Strategy

PostgreSQL

* Daily backups

Qdrant

* Snapshot backups

Redis

* Ephemeral
* Persistence optional

---

# 13. Future Database Enhancements

Future releases may introduce:

* Multi-tenancy
* Document Versioning
* Tags
* Labels
* Collections
* AI Evaluation Tables
* Prompt Version History
* Usage Analytics
* Cost Tracking
* Team Management
* Permissions
* Role-Based Access Control

---

# 14. Database Design Principles

* UUIDs for primary keys
* Soft delete where appropriate
* Immutable audit logs
* Provider-independent vector storage
* Metadata stored separately from embeddings
* Foreign key integrity
* Indexed lookup fields
* Minimal redundancy
* Workspace isolation by design
* Database responsibilities clearly separated

---

# 15. Traceability

| Requirement                  | Database Component     |
| ---------------------------- | ---------------------- |
| FR-001 Authentication        | User                   |
| FR-002 Workspace Management  | Workspace              |
| FR-003 Document Upload       | Document               |
| FR-005 Embedding Generation  | DocumentChunk + Qdrant |
| FR-007 Multi-Agent Workflow  | Conversation + Message |
| FR-008 Conversation History  | Conversation + Message |
| NFR-003 Security             | AuditLog               |
| NFR-006 Modular Architecture | Polyglot Persistence   |
