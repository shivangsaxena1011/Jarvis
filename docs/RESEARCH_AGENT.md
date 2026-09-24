# SHIVANI — Research Agent

## Overview
The Research Agent (`agents/research/`) enables SHIVANI to conduct academic and industrial research, verify findings across primary and secondary sources, handle contradictions transparently, and generate structured research reports.

```
SEARCH ──▶ COLLECT ──▶ FILTER ──▶ CLASSIFY ──▶ ANALYZE ──▶ SYNTHESIZE ──▶ CITE ──▶ REPORT
```

---

## Source Classification & Provenance
Sources are categorized into three authority tiers:
1. **Primary**:
   - Academic papers (`arXiv.org`, `doi.org`, `acm.org`, `ieee.org`, `nature.com`).
   - Official language and framework documentation (`docs.python.org`, `w3.org`, `rfc-editor.org`).
2. **Secondary**:
   - Reputable engineering blogs, benchmarks, and GitHub repositories.
3. **Community**:
   - Technical discussions, forum posts, social engineering threads.

### Source Record Schema
```json
{
  "id": "src_1",
  "title": "Recent Advances in Multimodal AI",
  "url": "https://arxiv.org/abs/2304.03442",
  "publisher": "arXiv / Academic",
  "date": "2026-09-24",
  "source_type": "primary",
  "relevance": 0.95,
  "summary": "Comprehensive survey on multimodal architecture and performance benchmarks."
}
```

---

## Contradiction & Tradeoff Handling
When sources present differing benchmarks, performance metrics, or architectural opinions:
- The agent retains both perspectives and documents the divergence explicitly in a `ContradictionRecord`.
- Never fabricates consensus or silently selects one viewpoint.

---

## 9-Section Technical Research Report
Every comprehensive research task outputs a structured report containing:
1. **Executive Summary**
2. **Problem Statement**
3. **Existing Approaches**
4. **Technology Landscape**
5. **Key Findings**
6. **Comparative Matrix** (Accuracy, Latency, Compute Cost)
7. **Tradeoffs & Differing Perspectives**
8. **Limitations & Future Opportunities**
9. **References & Provenance**

---

## Isolated Research Memory
All research artifacts are stored in `workspace/shivani-artifacts/research/` (`<slug>_report.md`, `<slug>_sources.json`, `<slug>_summary.json`). They are kept strictly separate from permanent personal user memory.
