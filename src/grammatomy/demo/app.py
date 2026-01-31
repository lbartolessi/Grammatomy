import streamlit as st
import time
import streamlit.components.v1 as components
import graphviz
from grammatomy import get_syntax_tree
from grammatomy.visualization import render_ascii_colored, get_graphviz_dot, render_json_colored, render_lisp_colored
from langdetect import detect_langs, LangDetectException

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Grammatomy Demo",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLES ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .stTextArea textarea { font-family: monospace; }
    
    /* Sidebar Width Adjustment */
    [data-testid="stSidebar"] {
        min-width: 450px;
    }
    </style>
""", unsafe_allow_html=True)

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

def get_interactive_svg_html(svg_content):
    """Wraps SVG content in HTML/JS for Pan/Zoom."""
    # Inject ID and Style to force full size
    svg_content = svg_content.replace('<svg', '<svg id="main-svg" style="width: 100%; height: 100%;"', 1)
    
    return f"""
    <style>html, body {{ height: 85vh; margin: 0; overflow: hidden; }}</style>
    <div id="svg-container" style="width: 100%; height: 100%; border: 1px solid #333; background: #fff; overflow: hidden; box-sizing: border-box;">
        {svg_content}
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
        <button class="copy-btn" onclick="navigator.clipboard.writeText(this.nextElementSibling.innerText).then(() => {{ this.innerHTML = '✅'; setTimeout(() => this.innerHTML = '📋', 1500); }})" title="Copy to Clipboard">
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
        "de": ["spmrl_charlm"]
    },
    "spacy": {
        "en": ["benepar_en3"]
    }
}

DEFAULT_SENTENCES = {
    "es": "",
    "en": "",
    "fr": "",
    "it": "",
    "pt": "",
    "de": ""
}

# Initialize session state variables
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
if "detected_lang" not in st.session_state:
    st.session_state.detected_lang = None
if "input_text" not in st.session_state:
    st.session_state.input_text = DEFAULT_SENTENCES["es"]
if "last_lang" not in st.session_state:
    st.session_state.last_lang = "es"

# --- SIDEBAR (Input & Config - Compact Mode) ---
with st.sidebar:
    st.title("🌳 Grammatomy")
    
    # Compact Configuration in 2 columns
    col1, col2 = st.columns(2)
    
    with col1:
        engine = st.selectbox("Engine", list(AVAILABLE_MODELS.keys()), index=0)
        
        # Dynamic Language List based on Engine
        available_langs = list(AVAILABLE_MODELS.get(engine, {}).keys())
        
        # Disable language selection if auto-detected
        lang_disabled = st.session_state.detected_lang is not None
        # If detected, try to set index to detected lang, else default to 0
        default_index = available_langs.index(st.session_state.detected_lang) if st.session_state.detected_lang in available_langs else 0
        lang = st.selectbox("Language", available_langs, index=default_index, disabled=lang_disabled)
        
        # Update input text only if language changes
        if lang != st.session_state.last_lang:
            st.session_state.input_text = DEFAULT_SENTENCES.get(lang, "")
            st.session_state.last_lang = lang
        
    with col2:
        use_gpu = False
        try:
            import torch
            if torch.cuda.is_available():
                device_opt = st.selectbox("Device", ["GPU", "CPU"], index=0)
                use_gpu = (device_opt == "GPU")
            else:
                st.text_input("Device", "CPU", disabled=True)
        except ImportError:
            st.text_input("Device", "CPU", disabled=True)
            
        # Dynamic Model List based on Engine & Language
        models_for_lang = AVAILABLE_MODELS.get(engine, {}).get(lang, ["default"])
        model_package = st.selectbox("Model", models_for_lang, index=0)
    
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
            
    with col_btn2:
        if st.button("Clear 🗑️", use_container_width=True):
            st.session_state.analyzed = False
            st.session_state.detected_lang = None
            st.rerun()

# --- MAIN CONTENT (Results) ---

if st.session_state.analyzed and text_input:
    # Spacer to prevent spinner from being hidden by top bar
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Use st.status for better visual feedback (Gears/Engranajes)
    with st.spinner("⚙️ Processing..."):
        
        # 1. Language Detection
        target_lang = lang
        # We need to re-fetch the model list because 'lang' might have changed if we force it via detection
        # But 'lang' variable comes from the widget which is now potentially disabled/locked to previous state.
        # Actually, we should detect first, update state, and rerun if needed, OR just use the detected lang for processing.
        # Let's use the detected lang for processing logic.
        
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
                        lang_status.markdown(f"<small style='color: #4ea8de;'>🌍 Language detected: <b>{target_lang.upper()}</b> ({best_match.prob:.2%}). Context locked.</small>", unsafe_allow_html=True)
                    else:
                        lang_status.markdown(f"<small style='color: #ffc107;'>⚠️ Detected language <b>{detected_code.upper()}</b> is not supported by '{engine}'. Proceeding with selected <b>{lang.upper()}</b>.</small>", unsafe_allow_html=True)
        except LangDetectException:
            lang_status.warning("Could not detect language. Proceeding with selection.")

        # Determine model for the (potentially new) target language
        # If the user selected a model for 'es' but we detected 'en', we must switch to a valid 'en' model.
        # We pick the first available model for the target language as a safe default.
        models_for_target = AVAILABLE_MODELS.get(engine, {}).get(target_lang, ["default"])
        # If the target lang matches the selected lang, we respect the user's model choice if possible
        if target_lang == lang and model_package in models_for_target:
            target_model = model_package
        else:
            target_model = models_for_target[0]

        # 2. Get Tree with dynamic params
        params = {
            "engine": engine,
            "lang": target_lang,
            "model_package": target_model,
            "use_gpu": use_gpu
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
                    used_mem = (total_mem - free_mem) / (1024 ** 2)
                    gpu_info = f" | 🎮 VRAM: {used_mem:.0f} MB"
            except Exception:
                pass
        
        result_status.markdown(f"<small style='color: #28a745;'>✅ Analysis Complete ({elapsed_time:.2f}s{gpu_info})</small>", unsafe_allow_html=True)
        
        if root:
            # 2. Tabs
            tab_ascii, tab_graph, tab_json, tab_lisp = st.tabs(["📜 ASCII Tree", "🕸️ Interactive Graph", "🪆 JSON Data", "🧬 Penn Treebank"])
            
            # Calculate dynamic height for main area (Viewport - Tabs Header ~ 60px - Padding ~ 80px)
            # We use a safe 80vh or calc to fill space
            dynamic_height = 600 
            
            with tab_ascii:
                html_tree = render_ascii_colored(root)
                st.components.v1.html(wrap_with_copy_button(html_tree), height=dynamic_height, scrolling=False)
            
            with tab_graph:
                # Generate DOT source
                dot_source = get_graphviz_dot(root)
                
                # 1. PNG for Download (Export Button - Top Right)
                col_spacer, col_btn = st.columns([6, 1])
                with col_btn:
                    try:
                        png_bytes = graphviz.Source(dot_source).pipe(format='png')
                        st.download_button("📷 PNG", png_bytes, "syntax_tree.png", "image/png", use_container_width=True)
                    except Exception as e:
                        st.warning(f"Export unavailable")

                # 2. SVG for Display
                svg_bytes = graphviz.Source(dot_source).pipe(format='svg')
                svg_content = svg_bytes.decode('utf-8')
                html_svg = get_interactive_svg_html(svg_content)
                components.html(html_svg, height=dynamic_height, scrolling=False)
                
            with tab_json:
                html_json = render_json_colored(root)
                st.components.v1.html(wrap_with_copy_button(html_json), height=dynamic_height, scrolling=False)
                
            with tab_lisp:
                html_lisp = render_lisp_colored(root)
                st.components.v1.html(wrap_with_copy_button(html_lisp), height=dynamic_height, scrolling=False)
        else:
            st.error("Could not parse the sentence.")
else:
    st.info("👈 Configure parameters and click **Analyze** in the sidebar to start.")
