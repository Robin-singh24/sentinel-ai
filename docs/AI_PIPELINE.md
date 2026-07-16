# 09_AI_PIPELINE.md

# Sentinel AI

### AI Pipeline Architecture

**Version:** 1.0

**Status:** Draft

---

# 1. Purpose

This document defines the complete AI pipeline for Sentinel AI, from document ingestion to AI-generated responses.

The objective is to build a modular, provider-independent Retrieval-Augmented Generation (RAG) platform capable of processing enterprise documents, retrieving relevant context, and producing accurate, cited responses through a multi-agent architecture.

The pipeline is designed to be scalable, extensible, and production-ready.

---

# 2. High-Level Pipeline

```text
                Upload Document
                       │
                       ▼
             Document Processing
                       │
                       ▼
               Text Extraction
                       │
                       ▼
                Text Cleaning
                       │
                       ▼
                  Chunking
                       │
                       ▼
             Metadata Generation
                       │
                       ▼
               Generate Embeddings
                       │
                       ▼
             Store in Qdrant
                       │
────────────────────────────────────────────
                       │
                  User Query
                       │
                       ▼
               Supervisor Agent
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
  Retrieval Required?         Direct Response
          │
         Yes
          │
          ▼
            Retriever Agent
                   │
                   ▼
        Semantic Search (Qdrant)
                   │
                   ▼
          Top-K Relevant Chunks
                   │
                   ▼
            Response Agent
                   │
                   ▼
             LLM (Groq/DeepSeek)
                   │
                   ▼
         Response + Citations
```

---

# 3. Pipeline Stages

## Stage 1 — Document Upload

Input:

- PDF
- Markdown
- TXT

Output:

- Stored document
- Database metadata
- Upload event

Responsibilities:

- Validate upload
- Generate checksum
- Store file
- Persist metadata

---

## Stage 2 — Document Processing

The ingestion service extracts raw text from uploaded documents.

Supported parsers:

| Type | Parser |
|------|--------|
| PDF | PyMuPDF |
| Markdown | markdown-it-py |
| TXT | Native Python |

Responsibilities:

- Parse document
- Extract text
- Preserve page boundaries
- Handle parsing failures

---

## Stage 3 — Text Normalization

Before chunking, extracted text is normalized.

Normalization includes:

- Unicode normalization
- Remove duplicate whitespace
- Normalize line endings
- Preserve paragraph boundaries
- Remove unsupported control characters

Normalization must never modify document meaning.

---

## Stage 4 — Chunking

Large documents are divided into semantic chunks suitable for embedding.

### MVP Strategy

Fixed-size chunking with overlap.

Configuration:

```text
Chunk Size      : 1000 characters
Chunk Overlap   : 200 characters
```

Future improvements:

- Recursive chunking
- Heading-aware chunking
- Semantic chunking
- Token-aware chunking

---

# 5. Chunk Metadata

Every chunk contains:

```json
{
  "chunk_id": "...",
  "document_id": "...",
  "workspace_id": "...",
  "chunk_index": 0,
  "page_number": 3,
  "text": "...",
  "character_count": 950,
  "token_count": 285
}
```

Metadata enables:

- Citations
- Ranking
- Filtering
- Traceability

---

# 6. Embedding Generation

Each chunk is converted into a dense vector representation.

### MVP

Embedding Model:

```
BAAI/bge-m3
```

Requirements:

- Batch embedding
- Retry on transient failures
- Provider abstraction
- Configurable model selection

Embeddings are generated only once per document version.

---

# 7. Vector Storage

Embeddings are stored in Qdrant.

Collection:

```
documents
```

Payload:

```json
{
  "workspace_id": "...",
  "document_id": "...",
  "chunk_id": "...",
  "page_number": 4,
  "chunk_index": 12
}
```

Vector payload must never contain sensitive application state.

---

# 8. User Query Pipeline

When a user submits a question:

```text
User Query
      │
      ▼
Supervisor Agent
```

The Supervisor determines:

- Is retrieval required?
- Can memory answer?
- Is clarification needed?
- Should the LLM be called?

---

# 9. Supervisor Agent

Responsibilities:

- Intent detection
- Query classification
- Route requests
- Coordinate downstream agents

The Supervisor never calls the LLM directly.

---

# 10. Retriever Agent

Responsibilities:

- Generate query embedding
- Search Qdrant
- Apply workspace filtering
- Rank retrieved chunks
- Return Top-K context

Default:

```
Top-K = 5
```

Future:

- Hybrid search
- BM25
- Metadata filtering
- Re-ranking

---

# 11. Response Agent

Responsibilities:

- Assemble prompt
- Inject retrieved context
- Apply system instructions
- Invoke LLM
- Parse response
- Generate citations

Supported Providers:

- Groq
- DeepSeek

Future:

- OpenAI
- Gemini
- Anthropic
- Ollama

The Response Agent must remain provider-independent.

---

# 12. Prompt Construction

Prompt consists of:

- System Prompt
- Retrieved Context
- Conversation History
- User Query

Prompt templates must remain external to application logic.

```
prompts/
```

---

# 13. Citation Strategy

Every generated response should include:

- Document name
- Page number
- Chunk identifier

Example:

```text
Source:
Employee Handbook.pdf
Page 12
```

Responses without supporting evidence should indicate that no relevant information was found.

---

# 14. Conversation Memory

Conversation history is maintained separately from document retrieval.

Memory stores:

- Previous user messages
- Previous AI responses
- Conversation metadata

Memory is never embedded into Qdrant.

---

# 15. Error Handling

Pipeline failures should be isolated.

Examples:

| Failure | Expected Behavior |
|----------|------------------|
| PDF parse fails | Mark document failed |
| Embedding API timeout | Retry |
| Qdrant unavailable | Retry with backoff |
| LLM unavailable | Return graceful error |

No pipeline stage should corrupt persisted data.

---

# 16. Retry Strategy

Retry only transient failures.

Default:

- Maximum retries: 3
- Exponential backoff
- Circuit breaker for repeated failures

Permanent failures should be recorded.

---

# 17. Security

Every retrieval operation must enforce:

- Workspace isolation
- User authorization
- Prompt injection mitigation
- Input validation

Users must never retrieve another workspace's embeddings.

---

# 18. Performance Targets

Target metrics:

| Operation | Target |
|-----------|--------|
| PDF Parsing | < 3 sec |
| Chunk Generation | < 1 sec |
| Embedding Generation | < 5 sec |
| Vector Search | < 200 ms |
| AI Response | < 5 sec |

These values are development targets and may evolve.

---

# 19. Future Enhancements

Planned improvements:

- Streaming responses
- Hybrid retrieval
- Multi-query retrieval
- Context compression
- Re-ranking models
- Knowledge graph integration
- Multi-modal document support
- OCR pipeline
- Background ingestion workers
- Document versioning
- Incremental re-indexing

---

# 20. AI Pipeline Principles

The Sentinel AI pipeline is designed around the following principles:

- Provider independence
- Modular architecture
- Deterministic document processing
- Secure workspace isolation
- Explainable AI through citations
- Fault-tolerant processing
- Production-ready scalability

Every pipeline stage should remain independently testable, replaceable, and extensible without impacting the rest of the system.