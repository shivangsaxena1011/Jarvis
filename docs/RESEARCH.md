# SHIVANI — Autonomous Research & Synthesis Integration

## Overview
The Research integration (`integrations/research/service.py`) automates academic and web research, citation tracking, and structured synthesis.

## Core Capabilities
- **Multi-Source Web Search**: Queries web engines and academic repositories for relevant literature.
- **Citation Extraction & Provenance**: Tracks title, URL, publication year, snippet, and confidence score for every reference.
- **Structured Synthesis**:
  - Executive Overview
  - Key Findings
  - Methodological Approaches
  - Comparative Analysis & Tradeoffs
  - Recommended Next Steps
- **Multi-Format Export**: Generates:
  - `report.md`: Markdown report with embedded citations
  - `sources.json`: Raw bibliographic data and provenance
  - `summary.json`: High-level metrics and executive takeaways

## Registered Tools
- `research.search`: Searches sources on a topic and returns citations.
- `research.synthesize`: Synthesizes search results into structured findings.
- `research.save`: Exports report and data bundles to the target directory.
