# ADR-006: AI Integration Timing

**Date:** 2025-04-29
**Status:** Proposed

## Context

The user requested the potential use of an AI assistant (like Gemini via Vertex AI) to help analyze folder structures and suggest organizational improvements based on file metadata summaries. This involves integrating with an external LLM API, managing API keys, designing prompts, and incorporating suggestions into the UI/workflow.

## Decision

The AI Organization Assistant component and its integration with Vertex AI will be implemented as a **Post-MVP (Minimum Viable Product)** feature. The initial release (V1) will focus on the core functionality of scanning, analysis (duplicates, large/old/temp files, similarity, corruption), review, action execution, and cloud migration.

## Rationale

*   **Focus on Core Value:** The primary value proposition of the system lies in identifying deletable/reviewable files based on objective criteria (size, age, hash, patterns) and facilitating migration. These features can be delivered effectively without AI integration.
*   **Reduced Initial Complexity:** Integrating with external AI APIs adds significant complexity:
    *   API key management (though addressed by ADR-002).
    *   Prompt engineering and optimization.
    *   Parsing and interpreting LLM responses.
    *   Designing UI elements to present AI suggestions effectively.
    *   Handling potential API costs, rate limits, and errors.
*   **Incremental Development:** Deferring AI integration allows the team to focus on building a stable, performant, and reliable core system first. User feedback on the core features can then inform the design and implementation of the AI assistant in a later phase.
*   **Optional Nature:** AI-driven organization is a "nice-to-have" feature for many users compared to the core "must-have" features of cleaning up duplicates and migrating files.

## Alternatives Considered

*   **Integrate AI in V1:** Rejected. This would significantly increase the initial development scope, complexity, and potential risks (API costs, reliability issues, UI complexity) without being essential for the core functionality. It could delay the delivery of the primary value proposition.
*   **No AI Integration Ever:** Rejected. The user explicitly requested exploring this possibility, and it offers potential future value for users struggling with organization. Deferring it keeps the option open.

## Consequences

*   The initial version of the Storage Hygiene System will not have AI-powered organization suggestions.
*   The architecture includes placeholders for the `AI Organization Assistant` component and its interactions, ensuring it can be added later without major structural changes.
*   The `Analysis Engine` and `UI` components need to be designed with future AI suggestion integration in mind (e.g., allowing flags or suggestion fields in the data model and UI).
*   User expectations should be managed; the AI feature will be clearly marked as a future enhancement.