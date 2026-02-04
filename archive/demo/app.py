# pylint: disable=invalid-name
import logging
import random
import sys
import time
from pathlib import Path

import graphviz
import streamlit as st
import streamlit.components.v1 as components
import yaml
from langdetect import LangDetectException, detect_langs

from grammatomy import get_syntax_tree
from grammatomy.glossary import TAG_MAP
from grammatomy.logger import setup_logging
from grammatomy.visualization import (
    get_graphviz_dot,
    render_ascii_colored,
    render_json_colored,
    render_lisp_colored,
)

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Grammatomy Demo",
    page_icon="🩻",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- LOGGING SETUP ---
@st.cache_resource
def get_app_logger():
    return setup_logging(
        name="grammatomy_demo",
        log_file=Path("demo.log"),
        console_level=logging.INFO,
        file_level=logging.WARNING,
    )


logger = get_app_logger()

# --- STYLES ---
st.markdown(
    """
    <style>
    /* Hide Streamlit Header and Footer to maximize space */
    /* Instead of display:none, we make it transparent and click-through */
    header[data-testid="stHeader"] {
        background: transparent;
        pointer-events: none;
    }
    /* Re-enable clicks ONLY for the sidebar toggle button */
    [data-testid="stSidebarCollapsedControl"] {
        pointer-events: auto;
        display: block !important;
        visibility: visible !important;
        z-index: 1000000;
        color: #56B4E9; /* Highlight color to make it visible */
    }
    /* Hide the right-side decoration and menu */
    header[data-testid="stHeader"] [data-testid="stToolbar"],
    header[data-testid="stHeader"] [data-testid="stDecoration"] { display: none; }
    footer { display: none; }

    /* Reduce top padding now that header is gone */
    /* Add enough padding so the sidebar toggle doesn't overlap our custom menu */
    .block-container { padding-top: 1rem; }
    .stTextArea textarea { font-family: monospace; }
    
    /* Sidebar Width Adjustment */
    [data-testid="stSidebar"] {
        min-width: 450px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- IFRAME CONTENT STYLES ---
# These styles are injected into the HTML components (iframes) to ensure correct rendering
CONTENT_CSS = """
<style>
    html, body {
        height: 85vh;
        margin: 0;
        background-color: #0e1117;
        color: #fafafa;
        font-family: sans-serif;
        overflow: hidden; /* Prevent body scroll, force inner scroll */
    }
    .scroll-box {
        height: 100%; /* Relative to body (which is 100vh) */
        overflow: auto;
        padding: 10px;
        box-sizing: border-box;
        white-space: pre; /* CRITICAL: Preserves line breaks for ASCII tree */
        font-family: 'Courier New', Courier, monospace;
    }
    .tree-connector { color: #6c757d; }
    .style-phrasal { color: #E69F00; font-weight: bold; } /* Orange */
    .style-pos { color: #56B4E9; font-weight: bold; }     /* Sky Blue */
    .style-punct { color: #999999; font-weight: bold; }   /* Grey */
    .style-word { color: #009E73; font-style: italic; }   /* Bluish Green */

    /* Copy Button Style */
    .copy-btn {
        position: absolute;
        top: 0.5rem;
        right: 1.5rem; /* Moved slightly left to avoid scrollbar overlap */
        z-index: 10;
        cursor: pointer;
        background: transparent;
        border: none;
        font-size: 1.5rem;
        opacity: 0.5;
        transition: opacity 0.2s;
        filter: grayscale(100%);
    }
    .copy-btn:hover {
        opacity: 1.0;
        filter: grayscale(0%);
        transform: scale(1.1);
    }
</style>
"""

# --- HELPER FUNCTIONS ---


def get_interactive_svg_html(svg_string: str):
    """Wraps SVG content in HTML/JS for Pan/Zoom."""
    # Inject ID and Style to force full size
    svg_string = svg_string.replace(
        "<svg", '<svg id="main-svg" style="width: 100%; height: 100%;"', 1
    )

    return f"""
    <style>html, body {{ height: 85vh; margin: 0; overflow: hidden; }}</style>
    <div id="svg-container" style="width: 100%; height: 100%; border: 1px solid #333; background: #fff; overflow: hidden; box-sizing: border-box;">
        {svg_string}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
    <script>
        var panZoomInstance;
        
        function initPanZoom() {{
            var svgElement = document.getElementById("main-svg");
            if (!svgElement) return;

            // Check if element has dimensions (is visible)
            if (svgElement.clientWidth === 0 || svgElement.clientHeight === 0) {{
                setTimeout(initPanZoom, 200);
                return;
            }}

            if (panZoomInstance) {{
                panZoomInstance.resize();
                panZoomInstance.fit();
                panZoomInstance.center();
                return;
            }}

            try {{
                panZoomInstance = svgPanZoom(svgElement, {{
                    zoomEnabled: true,
                    controlIconsEnabled: true,
                    fit: false,
                    center: true,
                    minZoom: 0.1,
                    maxZoom: 10
                }});

                window.addEventListener('resize', function(){{
                    if(panZoomInstance) {{
                        panZoomInstance.resize();
                        panZoomInstance.fit();
                        panZoomInstance.center();
                    }}
                }});

            }} catch (e) {{
                console.error("PanZoom init failed, retrying...", e);
                setTimeout(initPanZoom, 500);
            }}
        }}

        window.addEventListener('load', initPanZoom);
    </script>
    """


def wrap_with_copy_button(html_content):
    """Wraps HTML content with a JS copy-to-clipboard button."""
    # We use a simple JS function to copy the innerText of the content div
    return f"""
    {CONTENT_CSS}
    <div style="position: relative; height: 100%; width: 100%;">
        <button class="copy-btn" 
        onclick="navigator.clipboard.writeText(this.nextElementSibling.innerText).then(() => 
        {{ this.innerHTML = '✅'; setTimeout(() => this.innerHTML = '📋', 1500); }})"
        title="Copy to Clipboard">
            📋
        </button>
        <div class="scroll-box">{html_content}</div>
    </div>
    """


# --- MAIN APP ---

# --- CONSTANTS ---
AVAILABLE_MODELS = {
    "stanza": {
        "es": ["combined_bertin-roberta", "combined_charlm"],
        "en": ["ptb3-revised_electra-large"],
        "it": ["vit_charlm"],
        "pt": ["cintil_charlm"],
        "de": ["spmrl_charlm"],
    },
    "spacy": {"en": ["benepar_en3"]},
}

# Load benchmark sentences from external YAML file
try:
    EXAMPLES_FILE = Path(__file__).parent / "examples.yaml"
    with open(EXAMPLES_FILE, "r", encoding="utf-8") as f:  #
        BENCHMARK_SENTENCES = yaml.safe_load(f)
except (OSError, yaml.YAMLError) as e:
    logger.error("Error loading examples database: %s", e)
    st.error("Error loading examples database. Check logs.")
    BENCHMARK_SENTENCES = {}

DEFAULT_SENTENCES = {"es": "", "en": "", "fr": "", "it": "", "pt": "", "de": ""}

# --- APP MODE ---
IS_DEV_MODE = "--dev" in sys.argv

# Initialize session state variables
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
if "detected_lang" not in st.session_state:
    st.session_state.detected_lang = None
if "input_text" not in st.session_state:
    st.session_state.input_text = DEFAULT_SENTENCES["es"]
if "last_lang" not in st.session_state:
    st.session_state.last_lang = "es"
if "app_started" not in st.session_state:
    st.session_state.app_started = False
if "show_terms" not in st.session_state:
    st.session_state.show_terms = False
if "show_credits" not in st.session_state:
    st.session_state.show_credits = False
if "show_api" not in st.session_state:
    st.session_state.show_api = False
if "tree_result" not in st.session_state:
    st.session_state.tree_result = None
if "status_msg_lang" not in st.session_state:
    st.session_state.status_msg_lang = ""
if "status_msg_result" not in st.session_state:
    st.session_state.status_msg_result = ""
if "trigger_analysis" not in st.session_state:
    st.session_state.trigger_analysis = False

# --- LANDING PAGE ---
if not st.session_state.app_started:
    LANDING_HTML = """
    <style>
        .landing-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 85vh;
            text-align: center;
            animation: fadeIn 1.5s ease-in-out;
        }
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .landing-title {
            font-size: 5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .gradient-text {
            background: -webkit-linear-gradient(45deg, #eee, #56B4E9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .landing-subtitle {
            font-size: 1.5rem;
            color: #aaa;
            margin-bottom: 3rem;
            font-family: 'Courier New', monospace;
        }
        .landing-card {
            background-color: #262730;
            padding: 2rem;
            border-radius: 1rem;
            border: 1px solid #444;
            max-width: 700px;
            text-align: left;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .feature-list {
            list-style-type: none;
            padding: 0;
        }
        .feature-list li {
            margin-bottom: 0.5rem;
            padding-left: 1.5rem;
            position: relative;
        }
        .feature-list li::before {
            content: "✓";
            color: #56B4E9;
            position: absolute;
            left: 0;
            font-weight: bold;
        }
        </style>
        <div class="landing-container">
            <div class="landing-title">🩻 <span class="gradient-text">Grammatomy</span></div>
            <div class="landing-subtitle">Universal Constituent Parser</div>
            
            <div class="landing-card">
                <p style="font-size: 1.1rem; line-height: 1.6;">
                    Welcome to the <b>Grammatomy</b> interactive laboratory. 
                    This tool performs deep syntactic dissection to reveal hierarchical constituent structures, 
                    essential for prosodic analysis and phonological segmentation.
                </p>
                <ul class="feature-list">
                    <li><b>Multi-Engine Core:</b> Stanza (Stanford) & spaCy (Benepar)</li>
                    <li><b>Linguistic Precision:</b> Optimized for Spanish morphology and syntax.</li>
                    <li><b>Visual Anatomy:</b> ASCII Trees, Interactive Graphs, JSON, Penn Treebank.</li>
                </ul>
                <div style="margin-top: 1.5rem; padding: 1rem; background: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107; border-radius: 4px;">
                    <p style="color: #ffc107; font-size: 1.2rem; margin: 0;">
                        ⚠️ <b>System Notice:</b> Running on CPU environment. The first analysis may take a few seconds to initialize the neural models (Warm-up). Subsequent runs will be faster.
                    </p>
                </div>
            </div>
        </div>
    """
    # CRITICAL FIX: Strip all leading whitespace from every line to prevent Markdown
    # from interpreting indented HTML/CSS as code blocks.
    st.markdown(
        "\n".join([line.lstrip() for line in LANDING_HTML.split("\n")]),
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.write("")  # Spacer
        if st.button("Enter Laboratory 🧬", type="primary", use_container_width=True):
            st.session_state.app_started = True
            st.rerun()

else:
    # --- SIDEBAR (Input & Config - Compact Mode) ---
    with st.sidebar:
        st.title("🩻 Grammatomy")

        # Compact Configuration in 2 columns
        col1, col2 = st.columns(2)

        with col1:
            if IS_DEV_MODE:
                engine = st.selectbox("Engine", list(AVAILABLE_MODELS.keys()), index=0)
            else:
                engine = "stanza"

            # Dynamic Language List based on Engine
            available_langs = list(AVAILABLE_MODELS.get(engine, {}).keys())

            # Disable language selection if auto-detected
            lang_disabled = st.session_state.detected_lang is not None
            # If detected, try to set index to detected lang, else default to 0 (Spanish)
            try:
                default_index = (
                    available_langs.index(st.session_state.detected_lang)
                    if st.session_state.detected_lang in available_langs
                    else 0
                )
            except ValueError:
                default_index = 0

            lang = st.selectbox(
                "Language", available_langs, index=default_index, disabled=lang_disabled
            )

            # Update input text only if language changes
            if lang != st.session_state.last_lang:
                st.session_state.input_text = DEFAULT_SENTENCES.get(lang, "")
                st.session_state.last_lang = lang

        with col2:
            if IS_DEV_MODE:
                use_gpu = False
                try:
                    import torch

                    if torch.cuda.is_available():
                        device_opt = st.selectbox("Device", ["GPU", "CPU"], index=0)
                        use_gpu = device_opt == "GPU"
                    else:
                        st.text_input("Device", "CPU", disabled=True)
                except ImportError:
                    st.text_input("Device", "CPU", disabled=True)
            else:
                # Public Mode: Auto-detect GPU silently
                use_gpu = False
                try:
                    import torch

                    if torch.cuda.is_available():
                        use_gpu = True
                except ImportError:
                    pass

            # Dynamic Model List based on Engine & Language
            models_for_lang = AVAILABLE_MODELS.get(engine, {}).get(lang, ["default"])

            # In Public Mode for Spanish, enforce BERT only
            if not IS_DEV_MODE and lang == "es":
                models_for_lang = ["combined_bertin-roberta"]

            if IS_DEV_MODE or len(models_for_lang) > 1:
                model_package = st.selectbox("Model", models_for_lang, index=0)
            else:
                model_package = models_for_lang[0]

        # Input Area (Expanded height) - Updated default text based on language
        text_input = st.text_area("Input Sentence", key="input_text", height=250)

        # Placeholders for status messages in sidebar (Language Detection & Analysis Result)
        lang_status = st.empty()
        result_status = st.empty()

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Analyze 🚀", type="primary", use_container_width=True):
                st.session_state.analyzed = True
                # Reset detection on new analysis attempt to re-evaluate
                st.session_state.detected_lang = None
                st.session_state.trigger_analysis = True

        with col_btn2:
            if st.button("Clear 🗑️", use_container_width=True):
                st.session_state.analyzed = False
                st.session_state.detected_lang = None
                st.session_state.tree_result = None
                st.session_state.status_msg_lang = ""
                st.session_state.status_msg_result = ""
                st.rerun()

        # Random Example Button
        def on_random_click(lang_code):
            # Get examples for current lang, fallback to English if missing
            examples = BENCHMARK_SENTENCES.get(
                lang_code, BENCHMARK_SENTENCES.get("en", [])
            )
            if examples:
                st.session_state.input_text = random.choice(examples)
                # Reset analysis state so user has to click Analyze (or we could auto-trigger)
                st.session_state.analyzed = False

        st.button(
            "🎲 Random Example",
            use_container_width=True,
            on_click=on_random_click,
            args=(lang,),
        )

    # --- CUSTOM TOP MENU ---
    # Using the space freed up by the hidden header
    with st.container():
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        with col_m1:
            st.link_button(
                "🐙 GitHub",
                "https://github.com/your-repo/grammatomy",
                use_container_width=True,
            )
        with col_m2:
            st.link_button(
                "📚 Docs", "https://grammatomy.readthedocs.io", use_container_width=True
            )
        with col_m3:
            if st.button("🔌 API", use_container_width=True):
                st.session_state.show_api = not st.session_state.show_api
                st.session_state.show_terms = False
                st.session_state.show_credits = False
        with col_m4:
            if st.button("📖 Glosario", use_container_width=True):
                st.session_state.show_terms = not st.session_state.show_terms
                st.session_state.show_api = False
                st.session_state.show_credits = False  # Auto-close other
        with col_m5:
            if st.button("✨ Créditos", use_container_width=True):
                st.session_state.show_credits = not st.session_state.show_credits
                st.session_state.show_api = False
                st.session_state.show_terms = False  # Auto-close other

    # --- MENU EXPANDABLES ---
    if st.session_state.show_api:
        with st.expander("Servicio RESTful (API)", expanded=True):
            st.markdown(
                """
            **Grammatomy** incluye un servicio backend de alto rendimiento 
            que procesa sentencias en un formato JSON y devuelve un árbol de análisis. 
            Este servicio está construido con **FastAPI**.
            - **Endpoints:** `/parse`, `/render/ascii`, `/render/graphviz`, `/render/json`.
            - **Documentación:** Swagger UI disponible en `/docs` y ReDoc en `/redoc`.
            - **Integración:** Ideal para microservicios y procesamiento por lotes.
            """
            )

    if st.session_state.show_terms:
        with st.expander("Glosario de Etiquetas (AnCora/Penn)", expanded=True):
            st.markdown(
                "Fuentes: [Penn Treebank II (EN)](https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html) | "
                "[AnCora (ES)](http://clic.ub.edu/corpus/es/ancora)"
            )

            tab_phrasal, tab_pos = st.tabs(["Sintagmas (Phrasal)", "Categorías (POS)"])

            def render_table(data):
                lines = [
                    "| Etiqueta | Descripción (English Expansion) |",
                    "| :--- | :--- |",
                ]
                for tag, desc in data.items():
                    lines.append(f"| **{tag}** | {desc} |")
                return "\n".join(lines)

            with tab_phrasal:
                st.markdown(render_table(TAG_MAP["Phrasal"]))

            with tab_pos:
                st.markdown(render_table(TAG_MAP["POS"]))

    if st.session_state.show_credits:
        with st.expander("Créditos del Proyecto", expanded=True):
            st.markdown(
                """\
            ### 🩻 Grammatomy Team

            **Arquitectura & Desarrollo:** [Gemini Code Assist](https://cloud.google.com/products/gemini/code-assist)
            con la ayuda de Luis Bartolessi (extensión de VS Code para humanización de textos) :-)
            **Lingüística Computacional:** Basado en investigaciones de *PlanTL* y *Stanford NLP*.

            *Diseñado para la disección precisa de la prosodia española.*
            """
            )

    # --- MAIN CONTENT (Results) ---

    if st.session_state.analyzed and text_input:
        # Spacer to prevent spinner from being hidden by top bar
        st.markdown("<br>", unsafe_allow_html=True)

        # Only run computation if explicitly triggered
        if st.session_state.trigger_analysis:
            with st.spinner("⚙️ Processing..."):

                # 1. Language Detection
                target_lang = lang
                st.session_state.status_msg_lang = ""  # Reset status

                try:
                    # Detect with probabilities
                    langs_probs = detect_langs(text_input)
                    if langs_probs:
                        best_match = langs_probs[0]
                        # Threshold for confidence (e.g., 0.8)
                        if best_match.prob > 0.8:
                            detected_code = best_match.lang
                            supported_langs = AVAILABLE_MODELS.get(engine, {})

                            if detected_code in supported_langs:
                                st.session_state.detected_lang = detected_code
                                target_lang = detected_code
                                st.session_state.status_msg_lang = (
                                    f"<small style='color: #4ea8de;'>🌍 "
                                    f"Language detected: "
                                    f"<b>{target_lang.upper()}</b> ({best_match.prob:.2%}). "
                                    f"Context locked.</small>"
                                )
                            else:
                                st.session_state.status_msg_lang = (
                                    f"<small style='color: #ffc107;'>⚠️ Detected <b>{detected_code.upper()}</b>, "
                                    f"not supported by '{engine}'. Using selected <b>{lang.upper()}</b>.</small>"
                                )
                except LangDetectException:
                    st.session_state.status_msg_lang = (
                        "Could not detect language. Proceeding with selection."
                    )

                # Determine model for the (potentially new) target language
                models_for_target = AVAILABLE_MODELS.get(engine, {}).get(
                    target_lang, ["default"]
                )
                if target_lang == lang and model_package in models_for_target:
                    target_model = model_package
                else:
                    target_model = models_for_target[0]

                # 2. Get Tree with dynamic params
                params = {
                    "engine": engine,
                    "lang": target_lang,
                    "model_package": target_model,
                    "use_gpu": use_gpu,
                }

                start_time = time.time()
                root = get_syntax_tree(text_input, params=params)
                elapsed_time = time.time() - start_time

                # Capture GPU stats immediately after inference
                gpu_info = ""
                if use_gpu:
                    try:
                        import torch

                        if torch.cuda.is_available():
                            free_mem, total_mem = torch.cuda.mem_get_info()
                            used_mem = (total_mem - free_mem) / (1024**2)
                            gpu_info = f" | 🎮 VRAM: {used_mem:.0f} MB"
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        logger.warning("Failed to retrieve GPU stats: %s", e)
                        st.toast("GPU stats unavailable", icon="⚠️")

                st.session_state.status_msg_result = (
                    f"<small style='color: #28a745;'>✅ Analysis Complete "
                    f"({elapsed_time:.2f}s{gpu_info})</small>"
                )
                st.session_state.tree_result = root
                st.session_state.trigger_analysis = False  # Reset trigger

        # --- RENDER CACHED RESULTS ---
        if st.session_state.tree_result:
            root = st.session_state.tree_result

            # Restore status messages in sidebar
            if st.session_state.status_msg_lang:
                if "Could not detect" in st.session_state.status_msg_lang:
                    lang_status.warning(st.session_state.status_msg_lang)
                else:
                    lang_status.markdown(
                        st.session_state.status_msg_lang, unsafe_allow_html=True
                    )

            if st.session_state.status_msg_result:
                result_status.markdown(
                    st.session_state.status_msg_result, unsafe_allow_html=True
                )

                # 2. Tabs
                tabs = [
                    "🌳 ASCII Tree",
                    "🕸️ Interactive Graph",
                    "🪆 JSON Data",
                    "🧬 Penn Treebank",
                ]
                tab_ascii, tab_graph, tab_json, tab_lisp = st.tabs(tabs)

                # Calculate dynamic height for main area (Viewport - Tabs Header ~ 60px - Padding ~ 80px)
                # We use a safe 80vh or calc to fill space
                dynamic_height = 600

                with tab_ascii:
                    html_tree = render_ascii_colored(root)
                    components.html(
                        wrap_with_copy_button(html_tree),
                        height=dynamic_height,
                        scrolling=False,
                    )

                with tab_graph:
                    # Generate DOT source
                    dot_source = get_graphviz_dot(root)

                    # 1. Download Buttons
                    col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
                    with col_dl1:
                        try:
                            png_bytes = graphviz.Source(dot_source).pipe(format="png")
                            st.download_button(
                                "💾 PNG",
                                png_bytes,
                                "tree.png",
                                "image/png",
                                use_container_width=True,
                            )
                        except (
                            graphviz.backend.ExecutableNotFound,
                            graphviz.backend.CalledProcessError,
                        ) as e:
                            logger.warning("PNG export failed: %s", e)
                            st.toast("PNG export unavailable", icon="⚠️")
                    with col_dl2:
                        try:
                            svg_bytes = graphviz.Source(dot_source).pipe(format="svg")
                            st.download_button(
                                "💾 SVG",
                                svg_bytes,
                                "tree.svg",
                                "image/svg+xml",
                                use_container_width=True,
                            )
                        except (
                            graphviz.backend.ExecutableNotFound,
                            graphviz.backend.CalledProcessError,
                        ) as e:
                            logger.warning("SVG export failed:  %s", e)
                            st.toast("SVG export unavailable", icon="⚠️")
                    with col_dl3:
                        try:
                            jpg_bytes = graphviz.Source(dot_source).pipe(format="jpg")
                            st.download_button(
                                "💾 JPG",
                                jpg_bytes,
                                "tree.jpg",
                                "image/jpeg",
                                use_container_width=True,
                            )
                        except (
                            graphviz.backend.ExecutableNotFound,
                            graphviz.backend.CalledProcessError,
                        ) as e:
                            logger.warning("JPG export failed: %s", e)
                            st.toast("JPG export unavailable", icon="⚠️")
                    with col_dl4:
                        try:
                            gif_bytes = graphviz.Source(dot_source).pipe(format="gif")
                            st.download_button(
                                "💾 GIF",
                                gif_bytes,
                                "tree.gif",
                                "image/gif",
                                use_container_width=True,
                            )
                        except (
                            graphviz.backend.ExecutableNotFound,
                            graphviz.backend.CalledProcessError,
                        ) as e:
                            logger.warning("GIF export failed: %s", e)
                            st.toast("GIF export unavailable", icon="⚠️")

                    # 2. SVG for Display
                    svg_bytes = graphviz.Source(dot_source).pipe(format="svg")
                    svg_content = svg_bytes.decode("utf-8")
                    html_svg = get_interactive_svg_html(svg_content)
                    components.html(html_svg, height=dynamic_height, scrolling=False)

                with tab_json:
                    html_json = render_json_colored(root)
                    components.html(
                        wrap_with_copy_button(html_json),
                        height=dynamic_height,
                        scrolling=False,
                    )

                with tab_lisp:
                    html_lisp = render_lisp_colored(root)
                    components.html(
                        wrap_with_copy_button(html_lisp),
                        height=dynamic_height,
                        scrolling=False,
                    )
        elif st.session_state.analyzed and not st.session_state.trigger_analysis:
            # Analyzed was true but no tree result (failed parsing)
            st.error("Could not parse the sentence.")
    else:
        st.info(
            "👈 Configure parameters and click **Analyze** in the sidebar to start."
        )
