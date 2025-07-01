# ADR-001: Adopt LangGraph for LLM Agent and Tool Orchestration

## Status
Accepted

## Context

The project initially implemented LLM-powered features using the classic LangChain agent and tool abstractions. However, the LangChain maintainers now recommend using LangGraph for advanced agent, tool, and workflow orchestration. LangGraph provides a more flexible, maintainable, and stateful approach for building LLM applications, supporting multi-step reasoning, tool use, and complex branching logic.

## Decision

We will migrate all core LLM agent and tool orchestration to LangGraph, replacing the classic LangChain agent abstractions. This migration will be performed as a full rewrite of the relevant core LLM module files, rather than incrementally, since the feature is new and not yet widely used in production.

## Reasoning

- **Future-proofing:** LangGraph is the recommended and actively developed approach for LLM workflows in the LangChain ecosystem.
- **Flexibility:** LangGraph supports more complex, stateful, and multi-step workflows, which aligns with our long-term goals for LLM-powered features.
- **Maintainability:** The graph-based approach is easier to extend, test, and observe as our LLM integrations grow.
- **Simplicity:** Migrating early avoids technical debt and reduces the cost of future refactors.

## Consequences

- All new LLM-powered features and refactors will use LangGraph.
- The core LLM module will be rewritten to use LangGraph, and documentation will be updated accordingly.
- Domain modules and consumers will extend the new LangGraph-based core, ensuring consistency and maintainability.

---

_Update this ADR if the decision or rationale changes._
