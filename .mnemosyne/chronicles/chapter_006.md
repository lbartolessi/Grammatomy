# CHRONICLE: Chapter 006 (Service)

> INSTRUCTION: Episodic memory. Follow .mnemosyne/prompts/log_protocol.md.

CONTINUED FROM CHAPTER 005.

SUMMARY:
Following the completion of the Interactive Demo, we have architected and implemented the **RESTful Service** layer.
This enables headless consumption of the parsing logic, decoupling the core from the UI.
The service is built on **FastAPI**, containerized with **Docker**, and validated with a comprehensive test suite.

NEXT IMMEDIATE STEP: Verify Linter status after restart and begin Web Component implementation (Tree Viewer).

---

## UPDATABLE CONTENT

- [2024-05-21] [Milestone: API] Implemented RESTful Service using FastAPI. Defined Pydantic schemas for strict typing of the syntax tree.
- [2024-05-21] [Feature: Endpoints] Added `/parse` for tree generation and `/render/{ascii,graphviz,json,lisp}` for multi-format visualization.
- [2024-05-21] [Fix: Serialization] Resolved Pydantic V2 serialization issues with `anytree` objects by filtering private attributes and updating `ConfigDict`.
- [2024-05-21] [Test: Integration] Verified all API endpoints with `TestClient`. 8/8 tests passed successfully.
- [2024-05-21] [Itinerary] Marked "RESTful Service" as [DONE].
- [2024-05-21] [Feature: Demo UI] Polished Streamlit interface: Landing Page, Custom Menu, Glossary, and Download options.
- [2024-05-21] [Refactor: Visualization] Implemented Glossary-driven tooltips for Graphviz, removing internal IDs from leaf nodes.
- [2024-05-21] [Strategy: Public Mode] Configured app to run in simplified "Public Mode" by default, forcing BERT models for Spanish.
- [2024-05-21] [Plan] Paused deployment to focus on Code Quality, Documentation, and Packaging (Release Engineering) in the next session.
- [2024-05-21] [Refactor: Core] Externalized validation rules to `assets/rules/hybrid_rules.yaml` and implemented dynamic loading in `validation.py` to support hybrid AnCora/UD/PTB structures.
- [2024-05-21] [Fix: Core] Updated `grammatomy/__init__.py` and `validation.py` exports (`__all__`) to resolve Pylance import errors.
- [2024-05-21] [Feature: Web] Scaffolded `src/web` frontend application using Vite, Lit, TypeScript, and Tailwind CSS. Configured build pipeline and basic layout.
- [2024-05-21] [Environment] Linter errors persisted despite fixes; scheduled VS Code window reload to refresh language server context.