import streamlit as st
import streamlit.components.v1 as components
from anytree import RenderTree
from anytree.exporter import DotExporter
from grammatomy import get_syntax_tree, to_json
import json
import tempfile
import os

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Grammatomy Demo",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STYLES ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .stTextArea textarea { font-family: monospace; }
    /* Custom Scrollbar for ASCII/JSON containers */
    .scroll-box {
        height: 500px;
        overflow: auto;
        border: 1px solid #444;
        padding: 10px;
        background-color: #0e1117;
        border-radius: 5px;
        white-space: pre; /* Essential for ASCII tree alignment */
        font-family: 'Courier New', Courier, monospace;
    }
    .node-label { color: #4ea8de; font-weight: bold; }
    .node-word { color: #80ed99; font-style: italic; }
    .tree-connector { color: #6c757d; }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def render_ascii_colored(root):
    """Generates HTML for a colored ASCII tree."""
    html_lines = []
    for pre, _, node in RenderTree(root):
        # Escape HTML characters in pre and node content
        safe_pre = pre.replace("<", "&lt;").replace(">", "&gt;")
        
        line_content = f"<span class='tree-connector'>{safe_pre}</span>"
        
        # Label (Syntactic Category)
        label = getattr(node, "label", node.name) or node.name
        line_content += f"<span class='node-label'>{label}</span>"
        
        # Word (Lexical content)
        if hasattr(node, "word") and node.word:
            line_content += f": <span class='node-word'>\"{node.word}\"</span>"
            
        html_lines.append(line_content)
    
    return "\n".join(html_lines)

def render_interactive_svg(root):
    """
    Exports tree to SVG using Graphviz and wraps it in HTML/JS for Pan/Zoom.
    Requires 'graphviz' installed in the system.
    """
    try:
        # Generate SVG string
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            DotExporter(root).to_dotfile(tmp.name)
            # We use dot command to convert to svg (assuming graphviz is installed)
            # Alternatively, DotExporter can write directly if graphviz python lib finds the binary
            pass
        
        # Re-export using the proper method to get string content
        # Note: anytree DotExporter usually writes to file. 
        # We will use a workaround to get the SVG content.
        # Actually, let's use pydot or graphviz python lib if available, 
        # but anytree handles this well via file.
        
        svg_path = tmp.name + ".svg" # DotExporter might append extension or not depending on usage
        DotExporter(root, nodeattrfunc=lambda n: 'shape=box').to_picture(svg_path)
        
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
        
        os.unlink(tmp.name)
        os.unlink(svg_path)

        # Embed in HTML with svg-pan-zoom library
        html_block = f"""
        <div id="svg-container" style="width: 100%; height: 600px; border: 1px solid #333; background: #fff; overflow: hidden;">
            {svg_content}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
        <script>
            // Wait for SVG to load
            window.onload = function() {{
                var svgElement = document.querySelector("#svg-container svg");
                // Set 100% width/height for the SVG itself
                svgElement.setAttribute("width", "100%");
                svgElement.setAttribute("height", "100%");
                
                // Initialize Pan/Zoom
                svgPanZoom(svgElement, {{
                    zoomEnabled: true,
                    controlIconsEnabled: true,
                    fit: true,
                    center: true
                }});
            }};
        </script>
        """
        return html_block
    except Exception as e:
        return f"<div style='color:red'>Error generating Graphviz SVG: {e}<br>Ensure 'graphviz' is installed on the system.</div>"

# --- MAIN APP ---

st.title("🌳 Grammatomy: Constituent Parser Demo")
st.caption("Universal Syntax Tree Visualizer using Stanza & AnyTree")

col1, col2 = st.columns([3, 1])
with col1:
    text_input = st.text_input("Input Sentence", "El científico confirmó que los resultados contradicen las teorías anteriores.")
with col2:
    st.write("") # Spacer
    st.write("")
    submit = st.button("Analyze 🚀", use_container_width=True)

if submit and text_input:
    with st.spinner("Parsing constituents..."):
        # 1. Get Tree
        # We use Stanza as it is the stable engine for Spanish
        root = get_syntax_tree(text_input, params={"engine": "stanza", "lang": "es"})
        
        if root:
            # 2. Raw LISP Output (simulated from tree reconstruction or raw if available)
            # For now, we don't have the raw LISP string stored in the Node, so we might skip or reconstruct.
            # Let's just show a success message or the JSON structure as raw.
            st.success("Analysis Complete")

            # 3. Tabs
            tab_ascii, tab_graph, tab_json = st.tabs(["📜 ASCII Tree (Colored)", "🕸️ Interactive Graph", "DATA JSON"])
            
            with tab_ascii:
                html_tree = render_ascii_colored(root)
                st.markdown(f"<div class='scroll-box'>{html_tree}</div>", unsafe_allow_html=True)
            
            with tab_graph:
                html_svg = render_interactive_svg(root)
                components.html(html_svg, height=600, scrolling=False)
                
            with tab_json:
                json_str = to_json(root, indent=2)
                st.text_area("JSON Output", json_str, height=500)
        else:
            st.error("Could not parse the sentence.")