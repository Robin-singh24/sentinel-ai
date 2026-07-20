# Sentinel AI – AI Onboarding Guide

> If any instruction in this document conflicts with the project's architecture documents (HLD/LLD/Development Guidelines), the architecture documents take precedence.
>
> If documentation is ambiguous, stop implementation, explain the ambiguity, and request clarification instead of making assumptions.

> **Purpose**
>
> This document is the single source of truth for any AI agent contributing to Sentinel AI.
>
> Before making any changes to the codebase, every AI agent MUST read this document and follow the engineering principles defined here.

---

# Mission

Sentinel AI is a production-grade, modular AI platform designed around clean architecture, maintainability, and extensibility.

The goal is not simply to make features work.

The goal is to build a codebase that remains maintainable, testable, scalable, and easy to extend over many years.

Every implementation should prioritize long-term architecture over short-term convenience.

---

# Required Reading Order

Before implementing any feature, read the project documentation in the following order.

1. PRD
2. HLD
3. LLD
4. Database Design
5. AI Pipeline
6. Tech Stack
7. Development Guidelines
8. API Specification
9. This document

Do not begin implementation until you understand the existing architecture.

---

# Project Philosophy

Sentinel AI follows these principles:

- Production-ready over prototype
- Simplicity over cleverness
- Composition over inheritance
- Reuse over duplication
- Explicit over implicit
- Readability over brevity
- Long-term maintainability over short-term speed

Every design decision should support these principles.

---

# Architecture Philosophy

The project follows strict layered architecture.

```
Application
    │
    ▼
Business Services
    │
    ▼
Infrastructure
    │
    ▼
External Systems
```

Business logic must never leak into infrastructure.

Infrastructure must never contain business rules.

---

# Layer Responsibilities

## Infrastructure

Responsible for:

- database
- vector store
- storage
- external APIs
- messaging
- caching

Infrastructure must remain generic.

Infrastructure must not know anything about:

- documents
- users
- conversations
- AI
- business workflows

---

## Business Services

Responsible for:

- orchestration
- validation
- workflows
- business rules

Services coordinate infrastructure.

Infrastructure never coordinates services.

---

## AI Pipeline

Responsible for:

- parsing
- chunking
- embeddings
- retrieval
- reranking
- prompting

The AI pipeline consumes infrastructure.

Infrastructure must never depend on the AI pipeline.

---

# Dependency Rules

Dependencies must always flow downward.

Correct:

```
Service
    ↓
Repository
    ↓
Database
```

Incorrect:

```
Repository
    ↓
Service
```

Infrastructure must never import business services.

Circular dependencies are prohibited.

---

# Engineering Principles

Every implementation must follow:

- SOLID
- DRY
- KISS
- Dependency Injection
- Single Responsibility
- Separation of Concerns

Never violate these principles for convenience.

---

# Implementation Workflow

Every feature must follow this workflow.

## Step 1

Read relevant documentation.

---

## Step 2

Understand existing implementation.

Always reuse existing code before creating new code.

---

## Step 3

Present an implementation plan.

Explain:

- files to modify
- new classes
- responsibilities
- dependency changes
- testing strategy

Do not write code yet.

---

## Step 4

Wait for approval.

Never begin implementation before approval.

---

## Step 5

Implement.

Follow existing architecture.

Do not introduce unrelated refactoring.

---

## Step 6

Test.

Write integration tests whenever infrastructure is modified.

---

# Reuse Before Create

Before creating:

- class
- helper
- utility
- abstraction
- service
- repository

Search the project for an existing implementation.

Reuse existing functionality whenever possible.

Duplication is discouraged.

---

# Avoid Over-Engineering

Do not introduce unnecessary:

- factories
- builders
- interfaces
- adapters
- managers
- wrappers

Every abstraction must solve an actual problem.

Do not create abstractions "for future flexibility."

YAGNI applies.

---

# Dependency Injection

All infrastructure should be injected.

Never instantiate shared infrastructure inside business logic.

Correct:

```
FastAPI
    ↓
Dependency
    ↓
Repository
```

Incorrect:

```
Repository
    ↓
AsyncClient(...)
```

---

# Error Handling

Infrastructure exceptions must never leak.

Wrap external SDK exceptions using project exception types.

Preserve exception chaining.

Example:

```
raise SentinelVectorStoreError(...) from e
```

---

# Logging

Use structured logging.

Log:

- lifecycle events
- startup
- shutdown
- operations
- counts
- collection names

Never log:

- secrets
- embeddings
- payload contents
- tokens
- API keys

---

# Comments

Comments should explain WHY.

Never explain WHAT.

Good:

```
# Retry to tolerate transient network failures.
```

Bad:

```
# Increment i by one.
```

---

# Code Quality

Every contribution must be:

- async-first
- strongly typed
- production-ready
- formatted
- lint clean

No:

- TODOs
- placeholder code
- commented-out code
- dead code

---

# Testing

Every completed phase must include:

- integration tests
- regression tests (when appropriate)

Prefer testing against real infrastructure.

Avoid mocking infrastructure unless absolutely necessary.

---

# Definition of Done

A phase is complete only when:

- implementation is complete
- architecture is respected
- tests pass
- documentation is updated
- code review passes
- no temporary code remains

---

# AI Agent Rules

The AI agent must NEVER:

- silently change architecture
- introduce business logic into infrastructure
- duplicate existing functionality
- create unnecessary abstractions
- ignore project documentation
- bypass dependency injection
- implement future phases early

If uncertain,

ASK.

Never assume.

---

# Phase Boundaries

Respect project phases.

Do not implement functionality belonging to future phases.

Each phase should solve exactly one architectural concern.

---

# Existing Architecture

The current project contains modules such as:

- Authentication
- Workspaces
- Documents
- Conversations
- Database
- Vector Store
- AI Pipeline

Each module has clearly defined responsibilities.

Do not merge responsibilities across modules.

---

# Preferred Design Style

Prefer:

Small classes.

Focused responsibilities.

Explicit APIs.

Immutable configuration objects.

Request/Response models instead of long parameter lists.

Generic infrastructure.

Business orchestration in services.

---

# Before Every Implementation

Ask yourself:

- Does this already exist?
- Am I duplicating code?
- Does this belong in this layer?
- Can this remain generic?
- Am I introducing unnecessary abstractions?
- Will this still make sense one year from now?

If any answer is "No" or "I'm not sure",

stop and ask for clarification.

---

# Final Rule

Architecture is more important than implementation.

Code can always be rewritten.

Poor architecture becomes technical debt.

When in doubt, preserve architectural integrity.