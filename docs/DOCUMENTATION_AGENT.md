# SHIVANI — Documentation Agent

## Overview
The Documentation Agent (`agents/documentation/`) inspects actual codebases, manifest files, route decorators, and test suites to produce accurate, production-grade documentation.

> **Principle**: The Documentation Agent strictly reflects actual implemented files and routes. It never documents nonexistent features as implemented.

---

## Capabilities

1. **Production README.md Generation**:
   - Project Identity, badges, and tech stack tags.
   - High-level overview and problem context.
   - Interactive Mermaid architecture diagrams.
   - Prerequisites, installation commands, and package manager instructions.
   - Safe run and test commands.
   - Documented environment variables table (names and descriptions only).

2. **API Route Extraction & OpenAPI Documentation**:
   - Inspects FastAPI, Flask, or Express route definitions using AST parsing.
   - Extracts HTTP methods (`GET`, `POST`, `PUT`, `DELETE`, etc.), paths, handler function names, and docstrings.
   - Exports markdown documentation and structured JSON endpoint schemas.

3. **Architecture Decision Records (ADRs)**:
   - System context and component boundaries.
   - Technology stack rationales and security guardrails.

---

## Registered Tools
- `documentation.generate_readme`: Inspects project directory and generates production-grade README.md.
- `documentation.generate_api_docs`: Scans routes and controllers to generate API specifications.
- `documentation.generate_architecture_doc`: Synthesizes Architecture Decision Records (ADRs).
