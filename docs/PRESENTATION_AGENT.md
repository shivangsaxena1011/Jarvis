# SHIVANI — Presentation Agent

## Overview
The Presentation Agent (`agents/presentation/`) turns ideas, project architectures, and hackathon requirements into production-quality PowerPoint (`.pptx`) decks, multi-duration pitch scripts, and comprehensive judge Q&A preparation.

```
UNDERSTAND ──▶ RESEARCH ──▶ PROJECT ANALYSIS ──▶ STORYLINE ──▶ SLIDE STRUCTURE ──▶ GENERATION ──▶ REVIEW ──▶ EXPORT
```

---

## Capabilities & Outputs

1. **PowerPoint (.pptx) Deck Generation**:
   - Generates native `.pptx` presentations using `python-pptx`.
   - 16:9 widescreen layout (`13.333" x 7.5"`).
   - Professional dark-first technical color palette (Slate 900 background, Cyan 500 accents, Emerald 500 callouts, Slate 50 text).
   - Generates contextual **Speaker Notes** attached to each slide.

2. **Presentation Modes**:
   - `PresentationMode.HACKATHON`: Fast-paced, high-impact storytelling designed for judges.
   - `PresentationMode.TECHNICAL`: Architecture, deep-dives, benchmarks.
   - `PresentationMode.EXECUTIVE`: High-level business impact, ROI, roadmap.

3. **Slide Structure**:
   - Slide 1: Title & Team
   - Slide 2: The Core Problem & Industry Friction
   - Slide 3: Our Proposed Solution
   - Slide 4: System Architecture & Technology Stack
   - Slide 5: Key Features & Core Capabilities
   - Slide 6: Live Demo Walkthrough
   - Slide 7: Impact, Scalability & Future Roadmap

4. **Multi-Duration Pitch Scripts**:
   - **30-second**: Elevator pitch focusing on the core value proposition.
   - **1-minute**: Concise problem, solution, and differentiator summary.
   - **3-minute**: Expanded walkthrough including architecture and safety principles.
   - **5-minute**: Complete demo day pitch covering market impact, scalability, and ROI.

5. **Anticipated Judge Q&A Generator**:
   Generates targeted questions, suggested answers, and supporting evidence across 8 dimensions:
   - **Technical**
   - **Security**
   - **Scalability**
   - **AI/ML**
   - **Business**
   - **Data**
   - **Deployment**
   - **Innovation**

6. **Quality & Layout Inspection (`inspect_slides`)**:
   - Validates slide titles.
   - Checks against walls of text (flags bullet points exceeding 160 characters).
   - Ensures presence of speaker notes.

---

## Registered Tools
- `presentation.generate_deck`: Builds PowerPoint (.pptx) deck and returns metadata.
- `presentation.generate_pitch`: Synthesizes 30s, 1m, 3m, and 5m pitch scripts.
- `presentation.generate_qa`: Anticipates judge questions with answers and evidence.
