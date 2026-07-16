# 08_DEVELOPMENT_GUIDELINES.md

# Sentinel AI

### Development Guidelines

**Version:** 1.0

**Status:** Active

**Applies To:** All contributors (Human & AI)

---

# 1. Purpose

This document defines the engineering standards and development practices for Sentinel AI.

Its objective is to ensure that every contribution—whether written by a human developer or generated using AI—remains consistent, maintainable, testable, and production-ready.

These guidelines are mandatory for all future development.

---

# 2. Core Engineering Principles

Every implementation must prioritize:

* Simplicity over cleverness
* Readability over brevity
* Reusability over duplication
* Maintainability over shortcuts
* Modularity over coupling
* Composition over inheritance where practical

---

# 3. General Rules

Every implementation must:

* Follow the existing project architecture.
* Reuse existing modules whenever possible.
* Avoid duplicate business logic.
* Respect module boundaries.
* Maintain backward compatibility where practical.
* Keep the codebase production-ready.

---

# 4. File Modification Rules

Before modifying any file:

1. Inspect the existing implementation.
2. Determine whether the required functionality already exists.
3. Extend existing modules before creating new ones.
4. Never rewrite working code unless explicitly requested.
5. Modify only the files required for the current task.

Every implementation should begin by identifying:

* Files to modify
* Files to create
* Reason for each change

---

# 5. Reuse Before Create

Before creating:

* a service
* a utility
* a repository
* a schema
* a helper
* a configuration

always verify whether one already exists.

Duplicate implementations are not permitted.

---

# 6. Module Responsibilities

Each module owns its own:

* API routes
* Business logic
* Data access
* Validation
* Models

Modules should communicate only through well-defined service interfaces.

Direct database access across modules is prohibited.

---

# 7. Coding Standards

* Follow SOLID principles.
* Follow DRY.
* Prefer explicit code over implicit behavior.
* Keep functions focused on one responsibility.
* Avoid deeply nested logic.
* Prefer dependency injection.
* Keep modules cohesive.

---

# 8. Naming Conventions

## Files

Use lowercase with underscores where appropriate.

Examples:

* auth_service.py
* workspace_repository.py
* document_parser.py

---

## Classes

Use PascalCase.

Example:

* AuthService
* WorkspaceRepository

---

## Functions

Use snake_case.

Example:

* create_workspace()
* generate_embeddings()

---

## Variables

Use descriptive names.

Avoid abbreviations unless universally understood.

---

# 9. Function Guidelines

Functions should:

* Have a single responsibility.
* Be easy to test.
* Return predictable results.
* Avoid side effects where possible.

Prefer small functions over large ones.

---

# 10. Error Handling

Never silently ignore exceptions.

Every error should:

* Be logged.
* Return a standardized response.
* Include meaningful context.
* Preserve stack traces in logs.

Avoid generic `except Exception` unless rethrowing or wrapping appropriately.

---

# 11. Logging

Use structured logging.

Every request should include:

* Request ID
* User ID (if authenticated)
* Workspace ID (when applicable)
* Module name
* Execution time

Avoid logging:

* Passwords
* Tokens
* Secrets
* Sensitive document content

---

# 12. Configuration

Configuration must come exclusively from environment variables.

Never hardcode:

* API keys
* Database credentials
* JWT secrets
* File paths
* Provider URLs

Provide sensible defaults only for local development.

---

# 13. Dependency Rules

Before adding a new dependency, verify:

1. Can the Python standard library solve this?
2. Does an existing dependency already provide this functionality?
3. Is the dependency actively maintained?
4. Is it production-ready?
5. Does it introduce vendor lock-in?

Avoid unnecessary packages.

---

# 14. LLM Integration Rules

Business logic must never directly depend on a specific AI provider.

Always use the Provider Abstraction Layer.

Supported providers include:

* Groq
* DeepSeek
* OpenAI (Future)
* Gemini (Future)
* Ollama (Future)

Switching providers should require configuration changes only.

---

# 15. Database Rules

* Use SQLAlchemy ORM.
* Use Alembic for migrations.
* Never write raw SQL unless justified.
* Preserve foreign key integrity.
* Keep migrations reversible where practical.

---

# 16. API Rules

All APIs must:

* Validate inputs.
* Return consistent response formats.
* Use appropriate HTTP status codes.
* Document request and response schemas.
* Be versioned.

---

# 17. Security Rules

Always:

* Validate user authorization.
* Enforce workspace isolation.
* Sanitize user inputs.
* Validate uploaded files.
* Protect against prompt injection where applicable.

Never expose internal errors to clients.

---

# 18. Documentation Rules

Every new feature must update any affected documentation.

If a change impacts:

* Architecture
* Database
* API
* Deployment

the corresponding document must also be updated.

Documentation is considered part of the implementation.

---

# 19. Testing Guidelines

Every new feature should include:

* Unit tests where practical.
* Integration tests for critical flows.
* Edge case validation.
* Failure scenario handling.

Tests should be deterministic and isolated.

---

# 20. AI-Assisted Development Guidelines

When using AI (Antigravity or similar):

The AI must:

* Inspect the current project structure before generating code.
* Explain the planned modifications before implementation.
* Modify only the requested files.
* Reuse existing components.
* Avoid placeholder implementations unless requested.
* Avoid introducing unnecessary abstractions.
* Preserve consistency with the existing codebase.

The AI must **never**:

* Rewrite unrelated files.
* Duplicate business logic.
* Change public interfaces without justification.
* Introduce breaking changes silently.
* Add dependencies without explanation.

---

# 21. Git Workflow

* One feature per commit.
* Write meaningful commit messages.
* Keep commits focused and atomic.
* Avoid committing generated files, secrets, or local configuration.

---

# 22. Definition of Done

A task is complete only when:

* Requirements are implemented.
* Code follows project standards.
* No duplicate logic exists.
* Errors are handled correctly.
* Logging is added where appropriate.
* Documentation is updated.
* Tests pass.
* The feature integrates cleanly with the existing architecture.

---

# 23. Guiding Principle

> **Every line of code should leave the project easier to understand, easier to maintain, and easier to extend than it was before.**

# 24. Code Comment Guidelines

Comments should explain intent, assumptions, trade-offs, or non-obvious implementation details.

Do not comment code that is self-explanatory.

Examples of acceptable comments:

- Business rules
- Architectural decisions
- Performance optimizations
- Security considerations
- Edge cases

Avoid comments that merely restate the code.

Maximum comment length: one concise sentence.

Prefer docstrings for public modules, classes, and functions.

Code should be readable enough that comments are rarely needed.

# 25. Commenting Rules

- Comments must explain WHY, not WHAT.
- Do not comment obvious code.
- Keep comments to a single concise sentence.
- Prefer docstrings for public modules, classes and functions.
- Avoid decorative or verbose comments.
- Remove autogenerated comment blocks.

# 26. Code Generation Rules

- Prefer modifying existing files over creating new ones.
- Do not create abstraction layers unless they are immediately required.
- Avoid placeholder classes and functions.
- Avoid TODO comments.
- Do not generate future-proof code that is not used in the current phase.
- Every generated file must have a concrete purpose in the current implementation.

# 27. Import Rules

- Group imports into:
  1. Standard library
  2. Third-party packages
  3. Internal project imports

- Remove unused imports.
- Avoid wildcard imports.
- Prefer absolute imports over relative imports.
- Keep imports alphabetically sorted within each group.

# 28. Type Hint Rules

- Public functions must include type hints.
- Public methods must include return types.
- Prefer explicit typing over Any.
- Use Optional only when None is a valid value.
- Keep type annotations readable.

# 29. API Design Rules

- REST endpoints should represent resources.
- Use plural nouns for collections.
- Validate all request payloads.
- Return consistent response envelopes.
- Never expose internal exceptions.
- Keep endpoints idempotent where appropriate.

# 30. Folder Ownership

Each folder has a single responsibility.

api/
- Route definitions only.

modules/
- Business logic and feature implementation.

database/
- Database configuration only.

config/
- Application configuration only.

common/
- Shared utilities and reusable components.

utils/
- Stateless helper functions only.

llm/
- AI provider abstraction only.

# 31. File Size Guidelines

- Prefer files under 300 lines.
- Refactor files exceeding 500 lines.
- Keep classes focused on one responsibility.
- Split large modules into smaller components.

# 32. Function Size Guidelines

- Prefer functions under 40 lines.
- Extract complex logic into private helper methods.
- Avoid nested conditionals deeper than three levels.

# 33. AI Workflow Rules

Before generating code:

- Inspect the existing project.
- Explain the implementation plan.
- Wait for approval before writing code.

After generating code:

- Summarize all created files.
- Summarize all modified files.
- List all dependencies added.
- Provide verification steps.

# 34. YAGNI (You Aren't Gonna Need It)

Implement only what is required for the current phase.

Do not introduce abstractions, interfaces, helper classes, configuration, or extension points that are not immediately required.

Optimize for clarity over theoretical future requirements.