# ITINERARY (Iter)

> INSTRUCTION: Hierarchical map of goals and logical dependencies.
> UPDATE RULE: Update this file EVERY TIME:
>
> 1. A task or sub-task is completed (mark as [DONE]).
>    CONSTRAINT: Do NOT mark a task as [DONE] until the corresponding tests have been executed and passed.
> 2. New tasks are identified or priorities shift via user override.
> 3. We move to a new Chronicle Chapter.
>    ACTION: Re-calculate the "Critical Path". Ensure blocked tasks are indented.

## Content structure

- Dependency Graph (Text): Use an indented structure to show which tasks block which (e.g., Task A -> Task B).
- Critical Path Analysis: Identify the sequence of tasks that determine the possibility of completing others.
- Priority Matrix: For branches at the same level of dependency, prioritize according to the degree of alignment with the principles defined in the "docs/Architectural Principles.md" file. Effort should focus on consolidating the fundamental pillars before refinement or extension tasks.
- Special attention to logical dependencies that occur when a task requires other tasks to be completed before it can be finished.
- If the biography does not provide enough details about a branch (such as the acronym spelling engine), mark it as [TO BE DEFINED] based on your technical knowledge of what a system of the type we are building needs. Do not invent facts; identify technical needs.
- Every major task in the itinerary should ideally be justified by a principle in the methodology

## UPDATABLE CONTENT

- [x] Project Setup
- [x] Initialize Mnemosyne Framework
- [x] Parser LISP (Universal Converter)
  - [x] Implement LispParser.to_anytree logic
  - [x] Unit tests for LISP parsing
- [x] Bridge Stanza (Default Accurate)
- [x] Bridge spaCy (Benepar integration) [NOTE: English/Fallback only. Spanish requires Seq2Seq]
- [x] Bridge Transformers (Seq2Seq SOTA) [BLOCKED: PlanTL models empty; BLOOM requires fine-tuning]
- [x] AnyTree Exporter
- [x] Interactive Demo Application (Streamlit Polished)
- [x] Model & Language Inventory [DONE: Stanza=ES/IT/PT, Benepar=EN/FR/DE]
- [x] Local Model Registry & Updater [DONE: tools/manage_models.py]
- [x] Performance Benchmark Suite [DONE: tests/benchmark.py]
- [x] RESTful Service (FastAPI) [DONE]
  - [x] API Skeleton (FastAPI + Pydantic)
  - [x] Endpoint: /parse (Constituency Tree)
  - [x] Endpoint: /render/ascii (Text)
  - [x] Endpoint: /render/graphviz (Image)
  - [x] Endpoint: /render/json (Raw Tree)
  - [x] Endpoint: /render/lisp (Penn Treebank)
  - [x] Unit Tests (TestClient) [DONE]
- [ ] Release Engineering & Documentation [IN PROGRESS]
  - [x] Define Architectural Objectives & Personas [DONE]
  - [x] Define Frontend Stack (Lit/TS) [DONE]
  - [x] Monorepo Restructuring [DONE]
    - [x] Create folder structure (core, api, web, studio)
    - [x] Define per-module dependencies (pyproject.toml/package.json)
    - [x] Migrate existing Python logic to `src/core` [DONE]
  - [ ] Hugging Face Space Deployment (v2: Stateless Web App) [NEW TARGET]
    - [ ] Archive Legacy Streamlit Demo
    - [x] Deploy FastAPI Backend (Docker)
    - [x] Deploy Static Frontend (Lit Build)
  - [x] Code Quality Audit (Pylint/SonarQube cleanup) [DONE]
  - [ ] Standard Logging Implementation (Replace print statements)
  - [ ] PyPI Packaging Strategy (Library vs Demo separation)
  - [ ] ReadTheDocs Integration (MkDocs setup)
  - [ ] Grammatomy Studio (Phased Roadmap) [NEXT TARGET]
    - [x] Editor Layout & Chrome (Toolbar, Sidebar) [DONE]
    - [x] Cytoscape.js Integration (Basic)
    - [x] PTB-based State Management (Client-Side Parsing) [DONE]
    - [x] Rule-Based Editing Logic (Validation) [DONE]
      - [x] Connect Inspector Dropdown to Backend Rules (Context-Aware)
      - [x] Implement Graph Mutation Logic (Move/Delete/Ghost Nodes)
      - [x] Implement Visual Validation Feedback (Hexagons/Red Edges) [DONE]
    - [ ] Phase 1.5: UI Refactoring & Workflow [NEXT TARGET]
      - [x] Refactor Sidebar: Implement Tree List / Project Navigator [DONE]
      - [x] Implement Top Bar Menu (Project Level: New/Load/Save/Export) [DONE]
      - [x] Define Multi-Tree File Format (`.gmy` v1) [DONE]
      - [x] Implement "New Project" Wizard (Text Splitting Logic) [DONE]
      - [x] Implement Text-Tree Synchronization (Click sentence -> Load Tree) [DONE]
      - [x] Implement Subtree Extraction & Navigation (The "Góngora" Feature) [DONE]
      - [x] Implement Structural Search (Query-by-Example) [DONE]
      - [x] Markdown Annotation Layer [DONE]
        - [x] Select JS Markdown Editor (EasyMDE vs TipTap) [DONE: TipTap]
        - [x] Implement Project/Tree/Subtree Notes in Data Model [DONE]
        - [x] UI: Editor Integration in Sidebar/Inspector [DONE]
      - [x] Refactor: Server-Side Mutation (Migration) [DONE]
        - [x] Endpoint: /api/mutation/detach [DONE]
        - [x] Endpoint: /api/mutation/reabsorb [DONE]
      - [ ] UX Polish: Mutation Workflow [NEXT TARGET]
        - [ ] Fix: Auto-focus/Centering after Reabsorb
        - [ ] Fix: Selection state management during transitions
    - [ ] Phase 1: v0.1.0 (Foundation & Persistence) [TARGET]
      - [x] Verify Ghost Node Logic (Recursive Delete / Auto-Spawn Child) [DONE]
      - [x] Implement Sibling Node Reordering (Move Left/Right) [DONE - Visual Only]
      - [x] Implement Undo/Redo Stack (State History) [DONE]
      - [x] Implement Clipboard Operations (Cut/Copy/Paste Subtrees) [DONE]
      - [x] UX: Visual Semantics (Triangle shape for LINK/Ghost nodes) [DONE]
      - [ ] Testing & Stability
        - [x] Implement Decalogue Regression Suite (Editing Policy Validation) [DONE]
        - [x] Configure Coverage Reporting (pytest-cov for Coverage Gutters) [DONE]
        - [ ] Setup Frontend Testing Infrastructure (Vitest) [NEW]
      - [ ] IO & Persistence (Local-First)
        - [x] Design Basic `.gmy` JSON Schema (Multi-tree structure only) [DONE]
        - [x] Implement Multi-Tree File I/O (Load/Save `.gmy` locally via Browser) [DONE]
        - [x] Context Menu Exports (Granular) [DONE]
          - [x] Implement Right-Click Context Menu in Editor [DONE]
          - [x] Export Formats: PNG, SVG, WebP (Modern Web) [DONE]
          - [x] Export Formats: PTB (Text), ASCII Tree (LLM), LaTeX Forest (Academic) [DONE]
          - [x] Logic: Export Fragment vs Export Whole Tree based on target [DONE]
        - [ ] Project Level Exports (Main Menu)
          - [ ] Export Project as ZIP / Directory Structure
          - [ ] Cloud Integration (Google Drive, Dropbox, Mega) [FUTURE]
        - [ ] Interoperability
          - [ ] Research & Implement Import/Export for NLTK, Tregex, etc.
      - [ ] UX Refinement
        - [x] Consolidate Toolbar into Inspector Panel [DONE]
        - [ ] Implement Drag-and-Drop Node Moving (Cytoscape) [POSTPONED]
        - [ ] Implement Sliding ASCII Tree Sidebar
        - [ ] Welcome Screen & Help Page
    - [ ] Phase 2: v1.0.0 (Advanced Annotation & Fidelity) [FUTURE]
      - [ ] Architecture Refactoring
        - [ ] Implement Language Plugin System (`plugins/{es,it,en,pt}`) [BLOCKED]
        - [ ] Migrate `hybrid_rules.yaml` to per-language configuration
      - [ ] Advanced Annotation Features
        - [ ] Extend `.gmy` Schema for Annotation Layer (Metadata, Visual Props)
        - [ ] Research Cytoscape support for non-structural edges (Movement/Binding)
        - [ ] Implement Node Feature Editor (Phi-features, indices)
        - [ ] Implement Split-View Architecture (Interactive Editor / Static Preview)
        - [ ] Research Live LaTeX Forest Preview strategies (Server-side SVG vs WASM)
      - [ ] Configuration & Controls
        - [ ] Implement Parsing Mode Toggle (Constituency vs Universal Dependencies)
  - [ ] Algorithmic Tooling [NEW]
    - [ ] Implement Tree Edit Distance (Tree Levenshtein) for comparison
  - [ ] Pedagogical App (Component Validation) [NEW]
    - [ ] Scaffold simple "Student vs Solution" app reusing Editor Component
  - [ ] Telemetry System (Data Flywheel) [NEW]
    - [ ] Design data schema (SQLite) and FastAPI endpoint
    - [ ] Implement user consent UI in Studio
    - [ ] Implement data collection logic on tree edit/save
- [ ] Linguistic Edge-Case Suite (Native/Non-Translated) [POSTPONED]
- [x] Scientific Limitations Report (Model Characterization) [DONE: references/Auditoría Estructural Modelos Parsing Español.md]
