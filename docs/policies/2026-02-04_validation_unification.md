# Log Entry: 2026-02-04

## Summary
Unified the validation architecture by merging the legacy logic into the modern `ValidationEngine` and enforcing strict rules for editing operations.

## Key Changes
1.  **Engine Unification:**
    *   Ported `validate_node` (recursive yield logic) and `validate_context` from legacy engine to `src/core/grammatomy/validation_engine.py`.
    *   Implemented dual strategy support: `lax` (recursive yield check, context bypass) vs `strict` (direct children check, mandatory groups).
    *   Added legacy rule normalization to support `rules_es.yaml` format transparently.
    *   Deleted obsolete `src/core/validation_engine.py`.

2.  **Strict Editing Policy:**
    *   Updated `src/core/grammatomy/validation.py` endpoints (`check/requirements`, `check/delete`) to enforce `strategy="strict"`.
    *   Refactored `can_delete_child` to strictly validate mandatory sibling groups (OR logic).
    *   Documented the "Asymmetry Principle" in Methodology: Lax for visualization, Strict for editing.

3.  **Quality & Testing:**
    *   Fixed Pylint warnings (logging f-strings, cognitive complexity).
    *   Updated `run_tests.py` to handle `pytest-cov` absence gracefully.
    *   Cleaned up `environment.yml` (removed unused libs like spacy, nltk).
    *   Verified integration tests pass with the unified engine.