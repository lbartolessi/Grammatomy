# CHRONICLE: Chapter 001 (Footprints)

> INSTRUCTION: Episodic memory. Follow .mnemosyne/prompts/log_protocol.md.

---

## UPDATABLE CONTENT

- Journey started. Mnemosyne framework initialized.
- [2024-05-21] Project scaffolding created. Defined `environment.yml` and `pyproject.toml`. Initialized `src` and `tests` directories.
- [2024-05-21] Implemented `LispParser` core logic and unit tests. The universal converter is ready.
- [2024-05-21] [Refactoring: Structure] Corrected package structure from `src/parsers` to `src/grammatomy/parsers`. [Feature: Engine] Implemented `StanzaEngine` with caching and auto-download.
- [2024-05-21] [Fix: Linting] Fixed `pyproject.toml` syntax errors. [Cleanup] Removed duplicate root files and standardized `grammatomy.engines` package structure.
- [2024-05-21] [Maintenance: Sync] User manually verified and corrected directory structure (`engines` pluralization). Final cleanup of root `__init__.py`. Project layout is now canonical.
- [2024-05-21] [Environment: Issue] Persistent import errors detected despite editable install. User initiating VS Code window reload to refresh extension context. Session checkpoint saved.
- [2024-05-21] [Config: IDE] Created `.vscode/settings.json` to force `src` resolution in Pylance. [Environment: Sync] Added missing dev dependencies (`pylint`, `black`, `isort`, `mypy`) to `environment.yml` to align with `pyproject.toml`.
- [2024-05-21] [Architecture: Validation] Confirmed `src-layout` strategy. User questioned complexity due to tooling friction, but the decision stands to prevent import parity issues and ensure packaging integrity.
- [2024-05-21] [Config: Linter] Added `[tool.pylint]` to `pyproject.toml` to define source roots and suppress noisy docstring warnings. [Guidance] Advised using `__all__` in `__init__.py` to resolve `unused-import` false positives in package facades.
- [2024-05-21] [Fix: Typing] Resolved Pylance false positive in `StanzaEngine`. Explicitly typed `doc` as `Any` to bypass incorrect `list[Unknown]` inference on `stanza.Pipeline` return value.
- [2024-05-21] [Refactoring: Core] Introduced `SyntaxNode` (subclass of `anytree.Node`) in `LispParser` to provide explicit attribute definitions (`label`, `word`, `pos`). [Fix: Linting] Resolved Pylint `E1101` (no-member) in tests by replacing dynamic `Node` usage with typed `SyntaxNode`.
- [2024-05-21] [Fix: Tests] Applied Type Narrowing assertions (`assert root is not None`) in `test_lisp_parser.py` to satisfy Pylance strict null checks and ensure fail-fast behavior.
- [2024-05-21] [Refactoring: Quality] Refactored `LispParser.to_anytree` to reduce cognitive complexity (SonarLint S3776). Extracted token processing logic into static helper methods `_create_pending_node` and `_process_content`.
- [2024-05-21] [Fix: Typing] Resolved Pylance `reportMissingTypeArgument` in `LispParser`. Replaced generic `list` with specific `list[SyntaxNode]` in helper methods to enable full static analysis.
- [2024-05-21] [Feature: API] Implemented `get_syntax_tree` in `__init__.py` as the unified public facade. [Test: Integration] Added `test_stanza_engine.py` to verify end-to-end Stanza pipeline with a lightweight model.
- [2024-05-21] [Refactoring: DX] Added `if __name__ == "__main__":` block to `test_stanza_engine.py` to allow direct execution via python interpreter for easier debugging.
- [2024-05-21] [Fix: Tests] Corrected `test_stanza_engine.py` to use `model_package="default"` instead of invalid `"gem"`. [Config: Pytest] Registered `slow` marker in `pyproject.toml` to suppress warnings.
- [2024-05-21] [Milestone: Integration] Successfully passed end-to-end test for Stanza engine. [Config: Pytest] Added `filterwarnings` to `pyproject.toml` to suppress `DeprecationWarning`s from third-party SWIG bindings.
- [2024-05-21] [Debug: Visualization] Enhanced `test_stanza_engine.py` with `anytree.RenderTree` and added `-s` flag to pytest execution to print the parsed tree structure to stdout.
- [2024-05-21] [Refactoring: Performance] Parameterized `use_gpu` in `StanzaEngine` and `get_syntax_tree`. [Test: Optimization] Forced `use_gpu=False` in integration tests to avoid VRAM overhead and ensure CPU execution.
- [2024-05-21] [Planning: Roadmap] Added "Performance Benchmark Suite" to `Readme.md`. Defined scope: CPU/GPU comparison, cold/warm start metrics, and multilingual model validation using complex sentences.
- [2024-05-21] [Meta: Mnemosyne] Hardened `manifesto.md` with a "Context Integrity" clause to prevent silent context loss of critical files (`itinerary.md`, `methodology.md`). [Sync] Updated `itinerary.md` to include the new Benchmark task.
- [2024-05-21] [Debug: Visualization] Improved `test_stanza_engine.py` output to display lexical content (`node.word`) alongside syntactic labels, confirming that `SyntaxNode` captures full parse data.
- [2024-05-21] [Fix: Tests] Updated assertion in `test_stanza_engine.py` to match the new complex sentence content. [Feature: Engine] Implemented `SpacyEngine` with Benepar integration, supporting automatic Hugging Face model download via `transformers`. [API] Updated `get_syntax_tree` facade to route `engine="spacy"` requests.
- [2024-05-21] [Test: Integration] Created `test_spacy_engine.py` to validate `SpacyEngine` with the Spanish Hugging Face model (`dominguesp/constituent-parser-es`). [Itinerary] Marked "Bridge spaCy" as complete.
- [2024-05-21] [Meta: Succession] Chapter limit reached (>10 entries). Archiving Chapter 001. Proceeding to Chapter 002.
