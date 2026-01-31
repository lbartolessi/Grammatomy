# ITINERARY (Iter)

> INSTRUCTION: Hierarchical map of goals and logical dependencies.
> UPDATE RULE: Update this file EVERY TIME:
>
> 1. A task or sub-task is completed (mark as [DONE]).
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
- [ ] RESTful Service (FastAPI/Flask) [TO BE DEFINED]
- [ ] Hugging Face Space Deployment [TO BE DEFINED]
