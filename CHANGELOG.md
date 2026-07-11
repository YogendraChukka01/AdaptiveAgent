# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Professional repository documentation and contribution guidance
- CI workflow for backend and frontend checks
- Environment example files and improved ignore rules

### Fixed
- Critical: thread_id state leakage across users
- Critical: pgvector TypeError in add_documents
- Critical: score_relevancy returning 0.0 instead of None on failure
- Critical: frontend SSE error events silently swallowed
- Critical: frontend Dockerfile missing package-lock.json and public directory
- High: memory distiller background task never started
- High: Redis connection not closed on shutdown
- High: non-streaming and approve endpoints missing error handling
- High: stream timeout causing unhandled promise rejection
- High: wrong environment variable names in .env.example
- High: Docker GPU requirement mandatory with no fallback
- High: missing .dockerignore files
- Medium: CORS overly permissive methods and headers
- Medium: upload endpoint missing chunk count limit
- Medium: embedder cache not thread-safe
- Medium: health check race condition
- Medium: response_node false-positive refusal patterns
- Medium: audit logging silent error swallowing
- Medium: planner silent fallback without logging
- Medium: dead configuration values and mutable defaults
- Medium: chat pending approvals leaking internal fields
- Medium: frontend error messages leaking HTTP status codes
- Medium: SidePanel duplicating ChatResult type
- Medium: missing accessibility attributes
- Medium: missing CSP security headers
- Medium:ApprovalCard buttons defaulting to submit type
- Low: MessageBubble not memoized
- Low: input missing maxLength
- Low: ApprovalCard duplicate tool name keys
- Low: unnecessary suppressHydrationWarning
- Low: missing loading.tsx and not-found.tsx
- Low: unused dark variant in globals.css
- Low: embedder/reranker dual caching
- Low: chroma_store legacy functions creating new instances
- Low: upload.py HTTPException in utility function
- Low: state.py ambiguous start_time default

## [0.1.0] - 2026-07-08

### Added
- Initial backend and frontend project structure
- Chat API, retrieval services, and agent reasoning workflow

[Unreleased]: https://github.com/YogendraChukka01/AdaptiveAgent/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YogendraChukka01/AdaptiveAgent/releases/tag/v0.1.0
