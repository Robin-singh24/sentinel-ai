# 07_TECH_STACK.md

# Sentinel AI
## Technology Stack & Engineering Decisions

**Version:** 1.0  
**Status:** Draft

---

# Engineering Philosophy

Technology selection is guided by:

- Simplicity
- Scalability
- Maintainability
- Extensibility
- Provider Independence
- Enterprise Readiness

---

# Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19 | UI |
| TypeScript | 5.x | Type Safety |
| Tailwind CSS | 4.x | Styling |
| TanStack Query | Latest | Server State |
| React Router | 7.x | Routing |

---

# Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.116+ | REST APIs |
| Python | 3.12+ | Backend |
| SQLAlchemy | 2.x | ORM |
| Alembic | Latest | Migrations |
| Pydantic | v2 | Validation |

---

# AI Layer

| Technology | Purpose |
|------------|---------|
| Antigravity | Agent Orchestration |
| Groq | Default LLM |
| DeepSeek | Alternate Provider |
| Provider Abstraction Layer | Avoid Vendor Lock-in |

Future providers:
- OpenAI
- Gemini
- Anthropic
- Ollama

---

# Embeddings

Default:
- BAAI BGE-M3

---

# Data Layer

| Technology | Purpose |
|------------|---------|
| PostgreSQL | Relational Data |
| Qdrant | Vector Database |
| Redis | Cache & Sessions |

---

# Infrastructure

- Docker
- Docker Compose
- GitHub Actions

Future:
- Kubernetes
- Terraform
- AWS ECS

---

# Authentication

- JWT
- Refresh Tokens
- bcrypt

Future:
- OAuth2
- SAML

---

# Storage

MVP:
- Local Filesystem

Production:
- AWS S3

---

# Engineering Standards

- SOLID
- DRY
- Clean Architecture
- Dependency Injection
- Repository Pattern
- Factory Pattern
- Modular Monolith
- Provider Abstraction

---

# Development Tooling

- Ruff
- Black
- isort
- mypy
- pytest

---

# Repository Structure

```text
backend/
frontend/
docs/
prompts/
tests/
docker/
.github/
```

---

# Dependency Policy

Before adding any dependency:

1. Prefer the Python standard library.
2. Reuse existing project dependencies.
3. Choose actively maintained libraries.
4. Avoid unnecessary vendor lock-in.
5. Prefer proven production-ready packages.

---

# Future Evolution

Every major dependency (LLM, embedding model, vector database, storage backend) must be replaceable without changing business logic.
