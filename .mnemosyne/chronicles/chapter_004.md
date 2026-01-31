# CHRONICLE: Chapter 004 (Footprints)

> INSTRUCTION: Episodic memory. Follow .mnemosyne/prompts/log_protocol.md.

CONTINUED FROM CHAPTER 003.

SUMMARY:
We successfully built and polished the **Interactive Demo** (Streamlit) with advanced visualization features (Graphviz with zoom, colored ASCII/JSON/LISP).
We investigated the **Transformers (Seq2Seq)** path for Spanish parsing but found the SOTA models (PlanTL) unavailable/broken and generic models (BLOOM) insufficient without fine-tuning.
Given the hardware constraint (3.7GB VRAM), we confirmed that training/fine-tuning is not a viable path.
**Stanza** remains the primary engine.

NEXT IMMEDIATE STEP: Implement the **Performance Benchmark Suite** to measure CPU vs GPU latency and cold/warm start times.

---

## UPDATABLE CONTENT

- [2024-05-21] [Strategy: Hardware] Acknowledged 3.7GB VRAM constraint. Reaffirmed decision to rely on pre-trained inference (Stanza) rather than local fine-tuning.
- [2024-05-21] [Planning: Scope] Inserted "Model & Language Inventory" task into Itinerary. Created `tools/inventory_models.py` to programmatically list available constituency models in Stanza and Benepar before benchmarking.
- [2024-05-21] [Discovery: Inventory] `tools/inventory_models.py` revealed Stanza lacks constituency support for French in the current version, making Benepar (`benepar_fr2`) critical for FR coverage. Stanza covers ES, IT, PT. Benepar covers EN, FR, DE.
- [2024-05-21] [Fix: StanzaEngine] Resolved benchmark failures by modifying `StanzaEngine`. The pipeline now uses a dictionary for the `package` argument, correctly mapping specialized models (e.g., `combined_bertin-roberta`) to `pos` and `constituency` while using the default tokenizer.
- [2024-05-21] [Fix: Engines] Implemented `clear_cache()` in `StanzaEngine` and `SpacyEngine` to manage VRAM usage during benchmarking. Updated `StanzaEngine` to handle English configuration (no MWT, separate POS) and `SpacyEngine` to auto-add `sentencizer` for blank models.
- [2024-05-21] [Analysis: Benchmark] Initial benchmark run revealed VRAM limitations with large Stanza models (IT, PT) and missing dependencies for Benepar. [Fix: Benchmark] Updated `tests/benchmark.py` to use lighter CharLM models for IT/PT and to auto-download required spaCy base models for Benepar tests.
- [2024-05-21] [Feature: Tooling] Created `tools/manage_models.py` to centralize the download of Stanza, spaCy, and Benepar models, enforcing the "Model Sovereignty" principle. [Debug: Benchmark] Enabled exception printing in `tests/benchmark.py` to diagnose persistent Benepar failures.
- [2024-05-21] [Config: Models] Upgraded all spaCy base models to `lg` (Large) variants in `tools/manage_models.py`, `spacy_engine.py`, and `tests/benchmark.py`. This ensures higher accuracy for POS tagging, which is critical for Benepar's performance. Added `de_core_news_lg` to the inventory.
- [2024-05-21] [Fix: Benchmark] Corrected engine key in `tests/benchmark.py` from `"benepar"` to `"spacy"`. The public API `get_syntax_tree` expects `"spacy"` to route requests to `SpacyEngine`, causing the previous `NotImplementedError`.
- [2024-05-21] [Fix: Compatibility] Implemented a monkey-patch in `SpacyEngine` to restore `build_inputs_with_special_tokens` in `transformers` tokenizers (T5, XLM-R). This resolves the `AttributeError` causing Benepar failures for English and French due to version mismatches.
- [2024-05-21] [Validation: Final] Benchmark confirmed full stability for Stanza (ES, EN, IT, PT) and Benepar (EN). Benepar (FR) remains unstable due to `state_dict` mismatch (`position_ids`), marked as a known limitation. [Release] Finalized `requirements.txt` versions.
- [2024-05-21] [Meta: Succession] Chapter limit reached. Archiving Chapter 004. Proceeding to Chapter 005.
- [2024-05-21] [Config: Dependencies] Finalized `pyproject.toml` with explicit dependencies (`nltk`, `huggingface_hub`, `protobuf`) and generated `requirements.txt` for deployment. Validated the "Poetic License" patch strategy for Benepar compatibility.
- [2024-05-21] [Strategy: Architecture] Adopted "Model Sovereignty" principle in `methodology.md`. Defined a new task for a Local Model Registry to decouple runtime execution from public repository availability (mitigating risks like the PlanTL outage).
