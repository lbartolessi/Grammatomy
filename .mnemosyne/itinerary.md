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
- [ ] Release Engineering & Documentation [NEXT SESSION]
  - [x] Define Architectural Objectives & Personas [DONE]
  - [x] Define Frontend Stack (Lit/TS) [DONE]
  - [x] Monorepo Restructuring [DONE]
    - [x] Create folder structure (core, api, web, studio)
    - [x] Define per-module dependencies (pyproject.toml/package.json)
    - [ ] Migrate existing Python logic to `src/core` [USER ACTION REQUIRED]
  - [ ] Hugging Face Space Deployment (v2: Stateless Web App) [NEW TARGET]
    - [ ] Archive Legacy Streamlit Demo
    - [x] Deploy FastAPI Backend (Docker)
    - [x] Deploy Static Frontend (Lit Build)
  - [x] Code Quality Audit (Pylint/SonarQube cleanup) [DONE]
  - [ ] Standard Logging Implementation (Replace print statements)
  - [ ] PyPI Packaging Strategy (Library vs Demo separation)
  - [ ] ReadTheDocs Integration (MkDocs setup)
  - [ ] Grammatomy Studio (Phased Roadmap) [STRATEGIC PIVOT]
    - [x] Editor Layout & Chrome (Toolbar, Sidebar) [DONE]
    - [x] Cytoscape.js Integration (Basic)
    - [x] PTB-based State Management (Client-Side Parsing) [DONE]
    - [x] Rule-Based Editing Logic (Validation) [DONE]
      - [x] Connect Inspector Dropdown to Backend Rules (Context-Aware)
      - [x] Implement Graph Mutation Logic (Move/Delete/Ghost Nodes)
    - [ ] Phase 1: v0.1.0 (Foundation & Persistence) [TARGET]
      - [x] Verify Ghost Node Logic (Recursive Delete / Auto-Spawn Child) [DONE]
      - [x] Implement Sibling Node Reordering (Move Left/Right) [DONE - Visual Only]
      - [x] Implement Undo/Redo Stack (State History) [DONE]
      - [x] Implement Clipboard Operations (Cut/Copy/Paste Subtrees) [DONE]
      - [ ] Implement Drag-and-Drop Node Moving (Cytoscape) [NEW]
      - [ ] Testing & Stability
        - [x] Implement Decalogue Regression Suite (Editing Policy Validation) [DONE]
        - [x] Configure Coverage Reporting (pytest-cov for Coverage Gutters) [DONE]
      - [ ] IO & Persistence (Local-First)
        - [x] Design Basic `.gmy` JSON Schema (Multi-tree structure only) [DONE]
        - [ ] Implement Multi-Tree File I/O (Load/Save `.gmy` locally)
        - [ ] Implement Tree Index/Selector Sidebar
        - [ ] Implement Export Menu (SVG, PNG, PTB, JSON, Simple LaTeX Forest)
      - [ ] UX Refinement
        - [x] Consolidate Toolbar into Inspector Panel [DONE]
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
