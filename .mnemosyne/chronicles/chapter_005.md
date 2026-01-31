# CHRONICLE: Chapter 005 (Footprints)

> INSTRUCTION: Episodic memory. Follow .mnemosyne/prompts/log_protocol.md.

CONTINUED FROM CHAPTER 004.

SUMMARY:
We have established a robust, multi-engine architecture for Constituency Parsing.
**Stanza** is the primary engine, fully validated for Spanish, Italian, and Portuguese (using efficient CharLM models) and English.
**spaCy/Benepar** is integrated as a secondary engine, fully functional for English.
We implemented "Model Sovereignty" via `tools/manage_models.py` to ensure offline capability.
French support is currently suspended due to incompatibility between `benepar_fr2` and modern `transformers` libraries (we chose not to downgrade).

NEXT IMMEDIATE STEP: Define the deployment strategy (Hugging Face Spaces) or extend the API service.

---

## UPDATABLE CONTENT

- [2024-05-21] [Status: Baseline] Project v0.1.0 is stable with 4 supported languages. French is documented as unsupported.
- [2024-05-21] [Feature: Sovereignty] Implemented local model storage in `models/` directory. Updated `tools/manage_models.py` to download Stanza and Benepar models to this local path and backup spaCy wheels. Configured `StanzaEngine` and `SpacyEngine` to consume models from this local source, ensuring offline capability and preservation.
- [2024-05-21] [Fix: Tooling] Corrected `stanza.download` argument from `dir` to `model_dir` in `tools/manage_models.py` and `StanzaEngine` to fix API compatibility error. Updated `manage_models.py` to download `lg` (Large) spaCy models instead of `md`, aligning with the production configuration.
- [2024-05-21] [Feature: Demo] Updated `app.py` to dynamically populate the "Language" and "Model" dropdowns based on the validated inventory (`AVAILABLE_MODELS`). Added context-aware default sentences for ES, EN, FR, IT, PT, and DE to improve UX.
- [2024-05-21] [Validation: Infrastructure] User confirmed successful execution of `tools/manage_models.py`. All required models are now locally persisted, validating the "Model Sovereignty" architecture.
- [2024-05-21] [Refinement: Demo] Removed French (`fr`) from `AVAILABLE_MODELS` in `app.py` to align the UI with the supported/validated capabilities (French is currently unstable due to library conflicts).
- [2024-05-21] [Fix: Models] Migrated German (`de`) support from Benepar to Stanza (`spmrl_charlm`) due to `position_ids` incompatibility in `benepar_de2`. Updated `manage_models.py`, `app.py`, `benchmark.py`, and `Readme.md` to reflect this architectural change.
- [2024-05-21] [UX: Demo] Enhanced `app.py` with `langdetect` for automatic language switching and `st.status` ("⚙️ Processing...") to provide explicit visual feedback during analysis. Added `langdetect` to dependencies.
- [2024-05-21] [UX: Refinement] Removed `requirements.txt` in favor of `environment.yml`. Updated `app.py` to implement a stricter language detection flow: detection triggers on "Analyze", locks the language dropdown if confidence > 80%, and resets via a new "Clear" button.
- [2024-05-21] [Config: Environment] Synchronized `environment.yml` with the final project dependencies. Updated `spacy` to `>=3.7.0`, `transformers` to `>=4.30.0`, and added `nltk`, `huggingface_hub`, and `langdetect`.
- [2024-05-21] [UX: Metrics] Added GPU memory usage display (VRAM used/total) in the sidebar and processing time measurement in the status update of `app.py`.
- [2024-05-21] [UX: Polish] Refactored `app.py` to persist user input across model changes, resetting text only when the language changes (via `st.session_state.last_lang`). Replaced the persistent `st.status` expander with a transient `st.spinner` for a cleaner result view.
- [2024-05-21] [UX: Layout] Moved all status messages (Language Detection, Analysis Success/Metrics) from the main area to the sidebar (below the text input) using `st.empty()` placeholders. Simplified VRAM display to show only used memory.
- [2024-05-21] [Fix: Sync] Re-applied failed patch for `app.py` to ensure status messages are correctly routed to the sidebar placeholders. Synchronized `pyproject.toml` with `transformers>=4.30.0` constraint.
- [2024-05-21] [UX: Compact] Replaced `st.info`/`st.success` with `st.markdown` (using `<small>` tags) for status messages in `app.py`. This removes the default Streamlit padding/borders, keeping the feedback compact and close to the input area.
- [2024-05-21] [Fix: StanzaEngine] Resolved `PipelineRequirementsException` for German (`de`). Updated `StanzaEngine` and `manage_models.py` to treat German like English: using the default model for POS and the specific package (`spmrl_charlm`) only for constituency, ensuring the `pos` processor is correctly loaded.
- [2024-05-21] [Fix: UI] Updated `CONTENT_CSS` and `get_interactive_svg_html` in `app.py` to use `height: 100vh` and `overflow: hidden` on the body. This forces the iframe content to respect the component's fixed height (600px) and enables internal scrolling, preventing the layout from expanding indefinitely.
- [2024-05-21] [UX: Tuning] Reduced iframe body height to `90vh` in `app.py` to provide a safety margin for layout rendering. Cleared all `DEFAULT_SENTENCES` to prevent pre-filled text from interfering with user testing, while maintaining the dictionary structure for language switching logic.
- [2024-05-21] [UX: Tuning] Further reduced text area height to 250px and iframe body height to `85vh` in `app.py` to optimize vertical layout and prevent scrolling on smaller viewports.
- [2024-05-21] [Refactoring: CSS] Optimized layout logic in `app.py`. Set child containers (`.scroll-box`, `#svg-container`) to `height: 100%`, relying on the parent `body` being defined as `100vh`. This adheres to standard CSS practices for relative sizing.
- [2024-05-21] [Refinement: Demo] Removed French (`fr`) from `AVAILABLE_MODELS` in `app.py` to align the UI with the supported/validated capabilities (French is currently unstable due to library conflicts).
- [2024-05-21] [Milestone: Demo] User validated the final UI state ("Perfectísimo"). The Interactive Demo is fully polished, stable, and visually optimized. Session closed.