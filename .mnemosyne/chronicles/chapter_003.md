# CHRONICLE: Chapter 003 (Footprints)

> INSTRUCTION: Episodic memory. Follow .mnemosyne/prompts/log_protocol.md.

CONTINUED FROM CHAPTER 002.

SUMMARY:
We have established a dual-engine architecture. **Stanza** is fully operational with the SOTA `combined_bertin-roberta` model.
**spaCy/Benepar** is integrated but limited to English/Multilingual fallback as specific Spanish models are unavailable in standard registries.
We implemented the `AnyTree` JSON exporter and hardened the Mnemosyne protocol.
A Deep Research report identified that SOTA Spanish parsing has shifted to **Seq2Seq models (GPT-2/BLOOM)**, rendering the Benepar search obsolete.

NEXT IMMEDIATE STEP: Update documentation to reflect the Seq2Seq findings and proceed to the Interactive Demo.

---

## UPDATABLE CONTENT

- [2024-05-21] [Strategy: Redundancy] User confirmed decision to keep `SpacyEngine` active despite current model unavailability, citing future-proofing and language coverage.
- [2024-05-21] [Meta: Optimization] Increased Chapter succession limit from 10 to 20 entries in `manifesto.md` to maintain narrative continuity. Added flexibility clause to the succession trigger.
- [2024-05-21] [Strategic Pivot: Intelligence] Analyzed "Correcciones al Análisis Constituyente Español SOTA". Confirmed Benepar Spanish models are non-existent in registries. Identified Seq2Seq (GPT-2/BLOOM) as the true SOTA path.
- [2024-05-21] [Itinerary: Update] Marked "Bridge spaCy" as Done (with limitations). Added "Bridge Transformers (Seq2Seq)" to Roadmap as a future high-precision alternative.
- [2024-05-21] [Feature: Demo] Created `src/grammatomy/demo/app.py` using Streamlit. Implemented colored ASCII tree visualization (HTML/CSS), interactive SVG graph with Pan/Zoom (via `svg-pan-zoom` JS library), and JSON export view. Added `streamlit` and `graphviz` to dependencies.
- [2024-05-21] [Fix: Demo] Refactored `render_interactive_svg` in `app.py` to use `graphviz` python library directly instead of `anytree`'s file-based `to_picture`. This resolves the issue where the graph was not rendering due to temp file/path handling.
- [2024-05-21] [Fix: Visualization] Sanitized SVG output in `app.py` by stripping XML headers and forcing `width/height="100%"` via regex. Added explicit `id="main-svg"` to ensure `svg-pan-zoom` correctly targets the element.
- [2024-05-21] [Fix: Frontend] Resolved `SVGMatrix.inverse` error in Streamlit demo by adding a 500ms `setTimeout` to the JS initialization and using CSS injection instead of Regex to force SVG dimensions. This ensures the DOM is fully laid out before `svg-pan-zoom` calculates the viewport.
- [2024-05-21] [Fix: Frontend] Implemented a JS polling loop (`initPanZoom`) in `app.py` to handle Streamlit tabs. The script now waits for `clientWidth > 0` before initializing `svg-pan-zoom`, preventing the `Matrix is not invertible` crash when the graph tab is hidden. Also finalized the switch from `tempfile` to `graphviz` pipe.
- [2024-05-21] [Refactoring: Demo] Provided full rewrite of `src/grammatomy/demo/app.py` to eliminate patching artifacts. Enhanced JS logic with robust polling, error catching, and resize handling for `svg-pan-zoom`.
- [2024-05-21] [Fix: Visualization] Solved Graphviz node merging issue by configuring `DotExporter` with `nodenamefunc=id(n)`, ensuring unique nodes even with identical labels. [UI: Style] Unified ASCII and Graphviz color palettes (Okabe-Ito) in `app.py` for consistent visual semantics (Phrasal/POS/Punct/Word).
- [2024-05-21] [Refactoring: Architecture] Extracted visualization logic from `app.py` into a reusable module `src/grammatomy/visualization/`. Implemented `ascii_renderer`, `graphviz_renderer` (with tooltip removal), and `json_renderer` (with semantic coloring). Updated `app.py` to consume these components.
- [2024-05-21] [Feature: Demo] Updated `StanzaEngine` and `SpacyEngine` to attach the raw constituency string (`raw_lisp`) to the root node. Modified `app.py` to display this raw LISP output instead of a generic success message.
- [2024-05-21] [Feature: Demo] Enhanced `app.py` layout with a right-side control column. Added dynamic dropdowns for Engine, Language, Model, and GPU detection. Implemented `lisp_renderer.py` to pretty-print and colorize the raw LISP output in a dedicated tab.
- [2024-05-21] [Fix: Sync] Regenerated `src/grammatomy/visualization/lisp_renderer.py` and updated `__init__.py` to resolve `ImportError`. The previous file creation step was seemingly skipped or incomplete on the filesystem.
- [2024-05-21] [Cleanup: Mnemosyne] Deleted misplaced source files (`ascii_renderer.py`, `graphviz_renderer.py`, `json_renderer.py`, `check_model.py`, `__init__.py`) from `.mnemosyne/chronicles/` to enforce Directory Sanctity.
- [2024-05-21] [Research: Transformers] Created `tools/poc_transformers.py` to investigate the integration of `PlanTL-GOB-ES/gpt2-large-bne` for Seq2Seq constituency parsing. This script tests model loading and prompt strategies to determine the correct input format for tree generation.
- [2024-05-21] [UX: Demo] Finalized `app.py` layout by moving all inputs and controls to the Streamlit Sidebar. Implemented dynamic CSS height (`70vh`) for result containers to eliminate page scrolling and focus on data visualization.
- [2024-05-21] [UX: Refinement] Compacted Sidebar in `app.py` by removing headers/dividers and increasing text area height to 300px. Moved App Title to Main Area. Applied CSS to widen the sidebar (`min-width: 450px`).
- [2024-05-21] [UX: Optimization] Refactored `app.py` sidebar to use a 2-column layout for configuration dropdowns, saving vertical space. Merged title and subtitle into a single Markdown line to maximize the viewport for results.
- [2024-05-21] [Fix: UX] Resolved disappearing results in `app.py` by using `st.session_state` for persistence. Fixed Copy Button styling (transparent background, correct right alignment) and moved Export PNG button to the top of the graph tab for visibility.
- [2024-05-21] [Fix: Styling] Injected `CONTENT_CSS` directly into `st.components.v1.html` iframes in `app.py`. This resolves the "invisible text" issue (by forcing white color on dark background) and the "broken ASCII tree" issue (by enforcing `white-space: pre`).
- [2024-05-21] [UI: Polish] Updated JSON tab icon to 🪆 (Matryoshka) in `app.py`. [Strategy: Deployment] Confirmed Streamlit as the sole frontend framework for Hugging Face Spaces, discarding the Gradio alternative to leverage the custom JS visualization components already built.
- [2024-05-21] [Fix: UI] Removed f-string indentation in `wrap_with_copy_button` to fix ASCII tree shifting. Renamed "Raw LISP" tab to "Penn Treebank". Reduced iframe height to 500px to prevent overflow on standard screens.
- [2024-05-21] [Fix: Sync] Forced rewrite of `src/grammatomy/visualization/graphviz_renderer.py` and `__init__.py` to resolve persistent `ImportError: cannot import name 'get_graphviz_dot'`. The previous refactoring step likely failed to persist the function rename on disk.
- [2024-05-21] [Fix: Import] Corrected `app.py` to import `get_graphviz_dot` instead of the deprecated `render_graphviz_svg`. Added `import graphviz` and implemented client-side DOT-to-SVG/PNG rendering logic in the demo app.
- [2024-05-21] [Fix: Sync] Forced full rewrite of `src/grammatomy/demo/app.py` to resolve version mismatch. The file on disk had reverted to an older state (single-column sidebar, no session state), causing UI regression. Restored the "Compact Sidebar" layout, `CONTENT_CSS` injection, and copy/export functionality.
- [2024-05-21] [Fix: UI] Corrected Graphviz iframe height issue in `app.py`. Removed incorrect `calc(100vh - 280px)` from inside the iframe (which caused shrinking) and replaced it with `100vh`. Increased component height to 700px to match the visual weight of other tabs.
- [2024-05-21] [UX: Final Polish] Moved App Title to Sidebar and removed Subtitle to maximize main area space. Relocated "Export Graph PNG" button to Sidebar (contextual action). Increased component height to 750px for better vertical coverage.
- [2024-05-21] [UX: Adjustment] Reduced component height to 600px to prevent page scrolling on standard screens. Moved "Export PNG" button back to the main area (top-right of Graph tab) for better discoverability.
- [2024-05-21] [Fix: CSS] Changed `.scroll-box` and `#svg-container` height from `100vh` (viewport relative) to `100%` (container relative) in `app.py`. This ensures the content strictly respects the iframe height defined by Streamlit, preventing layout shifts or double scrollbars.
- [2024-05-21] [Milestone: Version Control] Project reached a stable state. User initiated Git repository commit. [Research: Hypothesis] Defined validation strategy for complex syntax: compare Góngora's original hyperbaton against a normalized "plain syntax" version to test model robustness beyond AnCora standards.
- [2024-05-21] [Experiment: Setup] Updated `tools/poc_transformers.py` to include both the original and a plain-syntax version of a Góngora stanza. This sets up a direct A/B test to evaluate the model's ability to handle extreme hyperbaton.
- [2024-05-21] [Fix: Tooling] Hardened `tools/poc_transformers.py` with a fallback mechanism. If `gpt2-large-bne` fails (due to missing weights or connection issues), the script now automatically attempts to load `gpt2-base-bne`. Added `huggingface_hub` inspection for debugging.
- [2024-05-21] [Debug: Transformers] Enhanced `tools/poc_transformers.py` to print the exact file list of the remote repository and automatically attempt `from_tf=True` or `from_flax=True` if standard PyTorch weights are missing. This addresses the `does not appear to have a file named pytorch_model.bin` error.
- [2024-05-21] [Debug: Transformers] PlanTL repositories appear empty (metadata only) in local execution. Updated `tools/poc_transformers.py` to include `bigscience/bloom-560m` (SOTA alternative) and `openai-community/gpt2` (sanity check) to isolate whether the issue is model-specific or environmental.
- [2024-05-21] [Research: Conclusion] `tools/poc_transformers.py` results confirm PlanTL repos are empty/broken. BLOOM loads but performs generic text completion (hallucination) instead of parsing, proving it lacks specific fine-tuning for this task. [Decision] Abandoned "Bridge Transformers" for now; Stanza remains the only viable SOTA engine for Spanish. Deleted PoC script.
- [2024-05-21] [Fix: Studio] Resolved `NameError` in `tools/studio.py` during drag-and-drop operation. The variable `target_node` was referenced but not defined in the `mouseReleaseEvent` scope; corrected to `target_item.node_ref`.
