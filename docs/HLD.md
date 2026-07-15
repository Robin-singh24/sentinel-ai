# 03_HLD.md

# Sentinel AI

### High Level Design (HLD)

**Document Version:** 1.0

**Status:** Draft

**Architecture Type:** Modular Monolith (MVP) with Evolution Path to Microservices

**Last Updated:** July 2026

---

# 1. Purpose

This document describes the high-level architecture of Sentinel AI.

It defines the major system components, their responsibilities, communication patterns, deployment topology, external dependencies, and scalability strategy.

This document intentionally avoids implementation details. Those are covered in the Low Level Design (LLD).

---

# 2. System Overview

Sentinel AI is an Enterprise Knowledge & Investigation Platform that enables engineering teams to retrieve organizational knowledge using AI-powered multi-agent workflows.

The platform consists of:

* Web Client
* Backend API
* AI Engine
* Retrieval Engine
* Document Processing Pipeline
* Databases
* External AI Providers

---

# 3. Architectural Principles

The system follows the following principles:

* Modular Monolith for MVP
* Domain Driven Design (DDD)
* SOLID Principles
* Separation of Concerns
* Dependency Injection
* Reusable Components
* Provider Abstraction
* Security by Design
* Observability by Default
* Scalability by Design

---

# 4. System Context

```text
                    +-------------------+
                    |      User         |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    |   React Frontend  |
                    +---------+---------+
                              |
                       HTTPS / REST
                              |
                              v
                    +-------------------+
                    |  FastAPI Backend  |
                    +---------+---------+
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
 Authentication        AI Platform          Document Engine
        |                     |                     |
        +----------+----------+----------+----------+
                   |                     |
                   v                     v
            PostgreSQL             Qdrant Vector DB
                   |
                   v
                Redis Cache

                   |
                   v

            LLM Provider Layer
      (Groq / DeepSeek / OpenAI)
```

---

# 5. Container Architecture

## Frontend

Responsibilities

* Authentication
* Workspace Management
* Chat Interface
* Document Upload
* Conversation History
* Streaming Responses

Technology

* React
* TypeScript
* TailwindCSS

---

## Backend

Responsibilities

* REST APIs
* Authentication
* AI Orchestration
* Document Processing
* Retrieval
* Conversation Management
* Business Logic

Technology

* FastAPI
* Python

---

## PostgreSQL

Stores

* Users
* Workspaces
* Documents
* Conversations
* Messages
* Metadata
* Audit Logs

---

## Qdrant

Stores

* Vector Embeddings
* Chunk Metadata
* Semantic Search Index

---

## Redis

Stores

* Session Cache
* Temporary Context
* Rate Limiting Data
* Future Pub/Sub Support

---

## LLM Provider Layer

Abstracts all external AI providers.

Supported Providers

* Groq (Default)
* DeepSeek
* OpenAI
* Gemini
* Ollama (Future)

Business logic never directly depends on any provider SDK.

---

# 6. Component Architecture

The backend is organized into independent modules.

```text
Backend

├── Authentication
├── Workspace
├── Documents
├── AI Engine
├── Retrieval
├── Conversations
├── Memory
├── Database
├── Configuration
├── Logging
└── Common Utilities
```

Each module owns its own business logic and communicates through clearly defined interfaces.

---

# 7. AI Architecture

The MVP consists of three AI agents.

```text
                 Supervisor
                      |
          +-----------+-----------+
          |                       |
          v                       v
    Retriever Agent       Responder Agent
```

## Supervisor Agent

Responsibilities

* Understand user intent
* Select workflow
* Coordinate downstream agents
* Maintain execution state

---

## Retriever Agent

Responsibilities

* Search vector database
* Retrieve relevant document chunks
* Apply metadata filters
* Return contextual evidence

---

## Responder Agent

Responsibilities

* Analyze retrieved evidence
* Generate grounded response
* Produce citations
* Estimate confidence

---

Future versions may introduce:

* Planner Agent
* Reviewer Agent
* Tool Agent
* Evaluation Agent

---

# 8. Document Processing Pipeline

```text
Upload Document

↓

Validation

↓

Parsing

↓

Cleaning

↓

Chunking

↓

Embedding Generation

↓

Vector Indexing

↓

Metadata Storage

↓

Available for Retrieval
```

---

# 9. Conversation Flow

```text
User Question

↓

Authentication

↓

Supervisor Agent

↓

Retriever Agent

↓

Qdrant Search

↓

Relevant Context

↓

Responder Agent

↓

Citation Generation

↓

Streaming Response

↓

Conversation Storage
```

---

# 10. Data Flow

### Document Lifecycle

Upload

→ Parse

→ Chunk

→ Embed

→ Index

→ Ready for Search

---

### Chat Lifecycle

Question

→ Retrieval

→ Reasoning

→ Response

→ Persist Conversation

---

# 11. Deployment Architecture

Local Development

```text
Docker Compose

├── Frontend
├── Backend
├── PostgreSQL
├── Redis
└── Qdrant
```

Production (Future)

```text
Load Balancer

↓

Frontend

↓

API Service

↓

AI Service

↓

Retrieval Service

↓

PostgreSQL

Qdrant

Redis
```

---

# 12. External Dependencies

Current

* Groq API
* Embedding Model
* Qdrant

Future

* GitHub
* Jira
* Slack
* Confluence
* Google Drive
* Microsoft Teams

---

# 13. Scalability Strategy

The MVP uses a Modular Monolith architecture.

As usage grows, the following modules can be extracted into independent services without major redesign:

* AI Service
* Retrieval Service
* Document Processing Service
* Notification Service
* Integration Service

This approach minimizes development complexity during the MVP while preserving a clear migration path toward a distributed architecture.

---

# 14. High-Level Security

The system enforces:

* JWT Authentication
* Workspace Isolation
* Secure API Access
* Environment-based Secrets
* Input Validation
* Prompt Injection Detection
* Audit Logging

Detailed implementation is documented in **09_SECURITY.md**.

---

# 15. High-Level Observability

The platform captures:

* Structured Application Logs
* AI Request Metrics
* Response Latency
* Token Usage
* Error Rates
* Health Checks

Future versions will introduce distributed tracing and centralized monitoring dashboards.

---

# 16. Architecture Decisions

The following architectural decisions are fundamental to Sentinel AI:

| Decision                   | Rationale                                             |
| -------------------------- | ----------------------------------------------------- |
| Modular Monolith           | Faster development while maintaining clean boundaries |
| FastAPI                    | Async performance and strong typing                   |
| React + TypeScript         | Mature frontend ecosystem                             |
| PostgreSQL                 | Reliable relational storage                           |
| Qdrant                     | High-performance vector database                      |
| Redis                      | Caching and session management                        |
| Provider Abstraction Layer | Prevent vendor lock-in                                |
| Multi-Agent Workflow       | Separation of AI responsibilities                     |
| Docker Compose             | Consistent local development                          |

Detailed rationale is documented in **12_ARCHITECTURE_DECISIONS.md**.

---

# 17. Future Evolution

The architecture is intentionally designed to support future enhancements without major refactoring.

Planned capabilities include:

* Multi-tenancy
* Role-Based Access Control (RBAC)
* Hybrid Search
* Reranking
* Background Workers
* Enterprise Integrations
* Human-in-the-Loop Approvals
* AI Evaluation Framework
* Horizontal Scaling
* Kubernetes Deployment

The MVP implements the core architectural foundation upon which these capabilities will be incrementally added.
