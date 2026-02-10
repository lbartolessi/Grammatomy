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
- [2024-05-21] [Decision: Validation] Adopted "Pragmatic Structural Validation" for mandatory children: requirements are satisfied by _any_ descendant (not just direct children) and follow OR logic (at least one match), accommodating Spanish syntactic flexibility.
- [2024-05-21] [Feature: Validation] Completed "Pragmatic Validation" engine. Implemented ancestor-based permission (upwards flexibility) and descendant-based mandatory checks (downwards flexibility) to accommodate neural parser variability.
- [2024-05-21] [Feature: Studio] Finalized Inspector UI with dynamic error reporting, ghost node editing (text/structure), and context-aware dropdowns.
- [2024-05-21] [Validation: External] Reviewed 'Auditoría Estructural Modelos Parsing Español'. The report confirms the necessity of the "Pragmatic Validation" strategy and the handling of hybrid UD/Constituency tags, validating the architectural pivot away from strict academic grammar towards SOTA model compatibility.
- [2024-05-21] [Plan: Next Session] Defined roadmap for Studio refinement: Ghost node verification, Export menu, ASCII sidebar, Responsiveness, and Onboarding screens. Final goal: Hugging Face Spaces deployment.
- [2024-05-21] [Environment] Linter errors persisted despite fixes; scheduled VS Code window reload to refresh language server context.
- [2024-05-22] [Strategy: Data Flywheel] User approved the implementation of a telemetry system to collect `(original, corrected)` tree pairs for future fine-tuning. [Priority] This task is scheduled as the final step before Hugging Face deployment. The long-term vision includes a dedicated telemetry service within a Grammatomy HFS organization.
- [2024-05-22] [Scope: Studio Expansion] User expanded the Studio requirements to include full IDE-like features: Undo/Redo, Drag-and-Drop (Move), Copy/Paste Subtrees, Local File I/O, and Browser-based Auto-Save. [New Concept] Proposed a "Pedagogical App" to validate the editor component's autonomy by comparing student inputs against gold-standard trees using a Tree Levenshtein algorithm.
- [2024-05-22] [Scope: Studio Configuration] Added requirements for Language Selection Dropdown and a Parsing Mode Toggle (Constituency vs. Universal Dependencies/Stanza Standard) to ensure inclusivity for different linguistic frameworks.
- [2024-05-22] [Decision: Graph Logic] Refined Ghost Node logic for strict purity. Ghost nodes are sterile leaves. Mutation is strictly validated against the parent's allowed children. Assigning a non-terminal tag to a ghost automatically spawns a new ghost child; assigning a terminal tag finalizes the branch.
- [2024-05-22] [Fix: Studio] Resolved `ROOT` node validation issues in Inspector by implementing optimistic updates and defensive checks for orphan nodes.
- [2024-05-22] [Refactor: Studio] Consolidated toolbar into Inspector panel and disabled client-side reordering to ensure structural integrity via future backend logic.
- [2024-05-22] [Feature: Export] Added requirements for academic export formats: LaTeX (Forest/Qtree) and PDF via LaTeX compilation, positioning the tool for research publication workflows.
- [2024-05-22] [Fix: Studio] Stabilized `GrammatomyEditor` initialization using `await this.updateComplete` and self-healing DOM injection to prevent race conditions in Light DOM. Restored missing `renderEditControl` method.
- [2024-05-22] [Fix: Layout] Implemented "Global DFS Indexing" to enforce strict left-to-right node ordering in Dagre layout, preventing sibling swapping during graph mutations. Added visual tie-breaking to `reindexChildren`.
- [2024-05-22] [Feature: Studio] Implemented internal Clipboard (Copy/Cut/Paste) with support for subtree serialization and intelligent pasting (Ghost replacement vs. Append).
- [2024-05-22] [Decision: Layout] Reverted to `dagre` layout. `breadthfirst` caused excessive visual disorder. Accepted `dagre`'s "anchor effect" (resistance to reordering nodes with aligned leaves) as a necessary trade-off for structural clarity.
- [2024-05-22] [Observation: UX] Validated Dagre's resistance to reordering aligned leaf nodes as a positive "Safety by Design" feature, preventing accidental word order permutation while allowing structural changes via grouping.
- [2024-05-22] [Refinement: Studio] Enforced "Atomic POS Unit" logic for Cut/Copy operations. Selecting a leaf node (word/punctuation) now automatically targets its parent POS/PUNCT node, ensuring linguistic units are moved/copied together.
- [2024-05-22] [Plan: Next Session] Defined roadmap: 1) Implement "Decalogue" Regression Tests (Editing Policy), 2) Refactor Language Architecture into a Plugin System (`plugins/{es,it,en,pt}`), 3) Implement Export System.
- [2026-02-09] [Experiment: Reconstruction] Attempted full tree reconstruction from flat POS tags using `EdgeBasedReconstructor`. Encountered recursive loop issues ("Tower of Babel") despite stratification strategies.
- [2026-02-09] [Discovery: AnCora] Confirmed via external intelligence that Stanza models for Spanish use native AnCora tags (`sn`, `grup.nom`) instead of PTB (`NP`, `VP`).
- [2026-02-09] [Strategic Pivot: Refinement] Abandoned "Reconstruction from Scratch". Adopted "Local Refinement" strategy to repair existing trees using production rules without flattening.
- [2026-02-09] [Artifact: Dump] Generated session dump to preserve context for the next session.
