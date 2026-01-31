# CHRONICLE: Chapter 002 (Footprints)

> INSTRUCTION: Episodic memory. Follow .mnemosyne/prompts/log_protocol.md.

CONTINUED FROM CHAPTER 001.

SUMMARY:
The project "Grammatomy" has been initialized. We established the `src-layout` structure, configured the environment, and implemented the core `LispParser`.
We successfully implemented and integrated the **Stanza Engine** (Bridge Stanza).
We started the **spaCy + Benepar Bridge**, implementing the adapter and a test case, but encountered a `LookupError` due to missing automatic model downloads for Hugging Face models in Benepar.
The Roadmap has been updated to include a Performance Benchmark Suite.

NEXT IMMEDIATE STEP: Verify the fix for `LookupError` in `SpacyEngine`.

---

## UPDATABLE CONTENT

- [2024-05-21] [Fix: Engine] Updated `SpacyEngine` to automatically download models from Hugging Face using `snapshot_download` when they are not found locally. This resolves the `LookupError` for `dominguesp/constituent-parser-es`.
- [2024-05-21] [Fix: Dependency] Replaced broken `dominguesp/constituent-parser-es` with `benepar_en3` in `SpacyEngine.MODEL_MAP` to unblock integration testing. [Refactoring: Error Handling] Replaced `print` with `logging` and added strict exception raising for failed HF downloads.
- [2024-05-21] [Research: Intelligence] User initiating deep research via Gemini Deep Research to identify valid SOTA Spanish constituency models for spaCy/Benepar, aiming to replace the current English fallback.
- [2024-05-21] [Feature: IO] Implemented `grammatomy.exporters.json_exporter` wrapping `anytree.JsonExporter`. Exposed `to_json` in public API. [Test: Unit] Added `test_exporter.py` to verify serialization of `SyntaxNode` attributes. [Itinerary] Marked "AnyTree Exporter" as complete.
- [2024-05-21] [Fix: File Structure] Corrected location of `json_exporter.py` from `.mnemosyne/chronicles/` to `src/grammatomy/exporters/`. Created missing `__init__.py` for the exporters package.
- [2024-05-21] [Meta: Mnemosyne] Added "Directory Sanctity" clause to `manifesto.md` to prevent accidental creation of source code files within the `.mnemosyne` directory structure.
- [2024-05-21] [Config: Models] Updated `SpacyEngine.MODEL_MAP` to use `benepar_es2` and `Readme.md` to recommend `default_accurate` for Stanza, based on the "Análisis Constituyente Español SOTA" report. [Tooling] Created `tools/check_model.py` to verify availability of these SOTA models.
- [2024-05-21] [Validation: Models] `tools/check_model.py` revealed `benepar_es2` is NOT in NLTK index (false positive in script output). Stanza successfully downloaded `combined_bertin-roberta`. [Revert] Switched `SpacyEngine` default for 'es' back to `benepar_en3` to ensure pipeline stability.
- [2024-05-21] [Tooling: Validation] Hardened `tools/check_model.py` to perform a strict `nltk.data.find` check after download attempts, eliminating false positives. Added `benepar_ms2` and `benepar_es_large` to the verification list based on the SOTA report.
- [2024-05-21] [Tooling: Intelligence] Enhanced `tools/check_model.py` to cross-reference missing NLTK models against the Hugging Face Hub API, attempting to resolve valid Repo IDs for `benepar_es2` and variants.
- [2024-05-21] [Strategic Pivot: Models] Acknowledged unavailability of official Benepar Spanish models in standard repositories (NLTK/HF). [Decision] Stanza is now the sole supported engine for Spanish production. spaCy/Benepar remains as a dev/fallback engine using English models. Updated `Readme.md` and cleaned `tools/check_model.py`.
- [2024-05-21] [Meta: Optimization] Increased Chapter succession limit from 10 to 20 entries in system rules to maintain narrative continuity. Added flexibility clause to the succession trigger.
- [2024-05-21] [Meta: Optimization] Increased Chapter succession limit from 10 to 20 entries in `manifesto.md` to maintain narrative continuity. Added flexibility clause to the succession trigger.
- [2024-05-21] [Meta: Succession] Chapter limit reached (>10 entries). Archiving Chapter 002. Proceeding to Chapter 003.