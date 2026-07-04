import streamlit as st
import pandas as pd
from lexer import tokenize
from parser import Parser
import tac
from attributes import evaluate_attributes
from postfix import to_postfix
from visualizer import visualize_ast
from backpatch import backpatch
from interpreter import build_symbol_table

# Preset programs definition
PRESETS = {
    "Arithmetic Expression": "a = 5;\nb = 10;\nc = a + b * 2 - 3;\n",
    "If-Statement": "a = 10;\nb = 20;\nif (a < b) {\n    max = b;\n}\n",
    "For/While Loop": "sum = 0;\ni = 1;\nwhile (i <= 5) {\n    sum = sum + i;\n    i = i + 1;\n}\n",
    "Nested Expression with Variables": "a = 5;\nb = 10;\nx = (a + b) * (b - a) / (2 * a);\n",
    "If-Else Statement": "a = 10;\nb = 20;\nif (a < b) {\n    max = b;\n} else {\n    max = a;\n}\n",
    "Short-circuit Boolean": "a = 5;\nb = 10;\nx = 0;\nif (a < b || x == 1) {\n    x = 100;\n} else {\n    x = 200;\n}\n",
    "Nested Loop (Even/Odd count)": "i = 0;\nevens = 0;\nodds = 0;\nwhile (i < 6) {\n    if (i * 1 - (i / 2) * 2 == 0) {\n        evens = evens + 1;\n    } else {\n        odds = odds + 1;\n    }\n    i = i + 1;\n}\n"
}

# Page Configuration
st.set_page_config(
    page_title="Compiler Design Web Visualizer",
    layout="wide",
    page_icon="⚙️"
)

# Inject custom CSS for premium design
st.markdown(
    """
    <style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Animated gradient aurora background */
    body {
        background-color: #0a0a12 !important;
        overflow-x: hidden;
    }

    body::before {
        content: "";
        position: fixed;
        top: -20%;
        left: -20%;
        width: 140%;
        height: 140%;
        background: 
            radial-gradient(circle at 20% 20%, rgba(139, 92, 246, 0.25), transparent 40%),
            radial-gradient(circle at 80% 30%, rgba(236, 72, 153, 0.2), transparent 40%),
            radial-gradient(circle at 50% 80%, rgba(45, 212, 191, 0.18), transparent 40%);
        filter: blur(60px);
        animation: drift 18s ease-in-out infinite;
        z-index: -1;
    }

    @keyframes drift {
        0%   { transform: translate(0, 0) scale(1); }
        33%  { transform: translate(5%, -5%) scale(1.1); }
        66%  { transform: translate(-5%, 5%) scale(0.95); }
        100% { transform: translate(0, 0) scale(1); }
    }
    
    /* App background and global text styling */
    html {
        background-color: transparent !important;
    }
    
    body {
        color: #e2e8f0 !important;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"], .main {
        background-color: transparent !important;
        background: transparent !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0c0e14 !important;
        border-right: 1px solid #1e293b !important;
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* Typography & Headers styling */
    h1, h2, h3, h4, h5, h6, label, [data-testid="stWidgetLabel"] {
        color: #f8fafc !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .gradient-text {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        background: linear-gradient(90deg, #5B8DEF 0%, #A78BFA 33%, #2DD4BF 66%, #FB7185 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    
    /* Monospace for code/data */
    code, pre, kbd, samp {
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        background-color: #161920 !important;
        color: #e2e8f0 !important;
    }
    
    /* Card-styled container for the source code input */
    div[data-testid="stTextArea"] {
        border: 1.5px solid #5B8DEF !important;
        border-radius: 12px !important;
        box-shadow: inset 0 2px 8px rgba(91, 141, 239, 0.15), 0 0 10px rgba(91, 141, 239, 0.05) !important;
        background-color: #161920 !important;
        padding: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stTextArea"]:focus-within {
        box-shadow: inset 0 2px 8px rgba(91, 141, 239, 0.25), 0 0 15px rgba(91, 141, 239, 0.15) !important;
        border-color: #5B8DEF !important;
    }
    
    div[data-testid="stTextArea"] textarea {
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-size: 0.95rem !important;
        background-color: #1a1d24 !important;
        color: #f8fafc !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Pill button with four-stage gradient background */
    .stButton>button {
        background: linear-gradient(90deg, #5B8DEF 0%, #A78BFA 33%, #2DD4BF 66%, #FB7185 100%) !important;
        color: #0c0e14 !important;
        font-weight: 800 !important;
        padding: 0.8rem 2.5rem !important;
        border-radius: 9999px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(167, 139, 250, 0.4) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        letter-spacing: 1px;
        text-transform: uppercase;
        width: 100% !important;
    }
    
    .stButton>button:hover {
        box-shadow: 0 8px 25px rgba(167, 139, 250, 0.6) !important;
        transform: translateY(-2px) !important;
        filter: brightness(1.15) !important;
        color: #0c0e14 !important;
    }
    
    .stButton>button:active {
        transform: translateY(1px) !important;
    }
    
    /* Interactive Tabs and Stage Colors styling */
    div[data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161920 !important;
        padding: 6px !important;
        border-radius: 12px !important;
        border: 1px solid #1e293b !important;
    }
    
    div[data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        border-bottom: none !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-baseweb="tab"]:hover {
        color: #f8fafc !important;
        background-color: rgba(255, 255, 255, 0.03) !important;
    }
    
    /* Hide the default underline bar */
    div[data-baseweb="tab-highlight-bar"] {
        background-color: transparent !important;
    }
    
    /* Underlines and Text Colors for Active Tabs */
    div[data-baseweb="tab-list"] button:nth-of-type(1)[aria-selected="true"] {
        color: #5B8DEF !important;
        background-color: #1e293b !important;
        border-bottom: 2.5px solid #5B8DEF !important;
    }
    div[data-baseweb="tab-list"] button:nth-of-type(2)[aria-selected="true"] {
        color: #A78BFA !important;
        background-color: #1e293b !important;
        border-bottom: 2.5px solid #A78BFA !important;
    }
    div[data-baseweb="tab-list"] button:nth-of-type(3)[aria-selected="true"] {
        color: #2DD4BF !important;
        background-color: #1e293b !important;
        border-bottom: 2.5px solid #2DD4BF !important;
    }
    div[data-baseweb="tab-list"] button:nth-of-type(4)[aria-selected="true"] {
        color: #FB7185 !important;
        background-color: #1e293b !important;
        border-bottom: 2.5px solid #FB7185 !important;
    }
    
    /* Tab label colored dots/badges */
    div[data-baseweb="tab-list"] button:nth-of-type(1)::before {
        content: "●";
        color: #5B8DEF;
        margin-right: 8px;
        font-size: 14px;
    }
    div[data-baseweb="tab-list"] button:nth-of-type(2)::before {
        content: "●";
        color: #A78BFA;
        margin-right: 8px;
        font-size: 14px;
    }
    div[data-baseweb="tab-list"] button:nth-of-type(3)::before {
        content: "●";
        color: #2DD4BF;
        margin-right: 8px;
        font-size: 14px;
    }
    div[data-baseweb="tab-list"] button:nth-of-type(4)::before {
        content: "●";
        color: #FB7185;
        margin-right: 8px;
        font-size: 14px;
    }
    
    /* Custom CSS styled tables and listings */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1rem;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        background-color: #161920;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #334155;
    }
    .custom-table th {
        padding: 12px 16px;
        text-align: left;
        font-weight: 700;
        color: #0f1117;
        border-bottom: 1px solid #334155;
    }
    .tokens-table th {
        background-color: #5B8DEF; /* Lexer Blue */
    }
    .custom-table td {
        padding: 10px 16px;
        border-bottom: 1px solid #1e293b;
        color: #e2e8f0;
    }
    .custom-table tr:last-child td {
        border-bottom: none;
    }
    .tok-type {
        color: #5B8DEF;
        font-weight: 600;
    }
    
    /* TAC and Backpatch styles */
    .tac-container {
        background-color: #161920;
        border: 1px solid #2DD4BF; /* Teal border */
        border-radius: 8px;
        padding: 16px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.95rem;
        min-height: 300px;
        max-height: 450px;
        overflow-y: auto;
        box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.4);
    }
    .tac-row {
        display: flex;
        align-items: center;
        margin-bottom: 6px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
    }
    .tac-line-num {
        color: #475569;
        width: 32px;
        text-align: right;
        margin-right: 12px;
        border-right: 1px solid #334155;
        padding-right: 8px;
        user-select: none;
    }
    .tac-code {
        color: #f8fafc;
    }
    .tac-keyword {
        color: #A78BFA; /* Parser Purple for goto/if */
        font-weight: 600;
    }
    .tac-op {
        color: #FB7185; /* Coral for operators */
    }
    .tac-var {
        color: #e2e8f0;
    }
    .tac-jump-target {
        color: #0f1117;
        background-color: #2DD4BF; /* Teal background for resolved targets */
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .tac-jump-unresolved {
        color: #f59e0b; /* Amber */
        background-color: rgba(245, 158, 11, 0.15);
        border: 1px dashed #f59e0b;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 4px;
        font-size: 0.85rem;
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.6; }
    }
    .tac-unresolved {
        color: #64748b;
        font-style: italic;
    }
    
    /* Backpatch trace log */
    .backpatch-log-container {
        background-color: #161920;
        border: 1px solid #2DD4BF; /* Teal border */
        border-radius: 8px;
        padding: 12px 16px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.9rem;
        color: #e2e8f0;
        max-height: 180px;
        overflow-y: auto;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        margin-top: 8px;
    }
    .backpatch-log-line {
        margin-bottom: 6px;
        border-bottom: 1px dashed #1e293b;
        padding-bottom: 4px;
    }
    .backpatch-log-line:last-child {
        margin-bottom: 0;
        border-bottom: none;
        padding-bottom: 0;
    }
    .log-indices {
        color: #FB7185; /* Coral indices */
        font-weight: 600;
    }
    .log-target {
        color: #2DD4BF; /* Teal target */
        font-weight: 600;
    }
    
    /* Polish notation custom box */
    .postfix-box {
        background-color: #161920;
        border: 1px solid #FB7185; /* Coral border */
        border-radius: 8px;
        padding: 16px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 1.1rem;
        color: #e2e8f0;
        margin-top: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# App Header
st.markdown('<div class="gradient-text">Compiler Design Web Visualizer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">An interactive syntax-directed translation dashboard. Lex, parse, evaluate attributes, view AST, generate TAC, and translate to postfix.</div>', unsafe_allow_html=True)

# Initialize session state for source code
if "source_code" not in st.session_state:
    st.session_state.source_code = PRESETS["Arithmetic Expression"]

# Helper function to run the translation pipeline
def run_translation():
    try:
        # Reset TAC state
        tac.reset_temp()
        
        # 1. Tokenize
        tokens = list(tokenize(st.session_state.source_code))
        
        # 2. Parse
        parser = Parser(tokens)
        ast = parser.parse()
        
        # 3. Evaluate Attributes & Backpatch top level
        evaluate_attributes(ast)
        if 'next' in ast.attrs:
            backpatch(ast.attrs['next'], tac.nextinstr())
            
        # 4. Generate AST SVG string using visualizer
        svg_str = visualize_ast(ast, "output")
        
        # 5. Postfix Notation
        postfix_str = to_postfix(ast)
        
        # 6. Build Symbol Table
        try:
            symbol_table = build_symbol_table(ast)
        except Exception as e:
            symbol_table = {}
            
        # Save results in session state
        st.session_state.tokens = tokens
        st.session_state.svg_str = svg_str
        st.session_state.ast_text = str(ast)
        st.session_state.tac_instructions = list(tac.instructions)
        st.session_state.emitted_history = list(tac.emitted_history)
        st.session_state.postfix_str = postfix_str
        st.session_state.symbol_table = symbol_table
        st.session_state.error = None
    except Exception as e:
        # Clean state and save error
        st.session_state.tokens = None
        st.session_state.svg_str = None
        st.session_state.ast_text = None
        st.session_state.tac_instructions = None
        st.session_state.emitted_history = None
        st.session_state.postfix_str = None
        st.session_state.symbol_table = None
        st.session_state.error = str(e)

def format_quad_to_html(quad, idx, is_before=False):
    line_num_html = f'<span class="tac-line-num">{idx}</span>'
    
    # Determine target/result formatting
    is_jump = (quad.op == 'goto' or quad.op.startswith('if'))
    
    if quad.result is None:
        result_str = '_'
    else:
        result_str = str(quad.result)
        
    if is_jump:
        if result_str == '_':
            result_html = '<span class="tac-jump-unresolved">_</span>'
        else:
            result_html = f'<span class="tac-jump-target">{result_str}</span>'
    else:
        if result_str == '_':
            result_html = '<span class="tac-unresolved">_</span>'
        else:
            result_html = f'<span class="tac-var">{result_str}</span>'
            
    arg1_str = str(quad.arg1) if quad.arg1 is not None else ""
    arg2_str = str(quad.arg2) if quad.arg2 is not None else ""
    
    # Format instruction structure
    if quad.op == 'goto':
        inst_html = f'<span class="tac-keyword">goto</span> {result_html}'
    elif quad.op.startswith('if'):
        relop = quad.op[2:]
        inst_html = f'<span class="tac-keyword">if</span> <span class="tac-var">{arg1_str}</span> <span class="tac-op">{relop}</span> <span class="tac-var">{arg2_str}</span> <span class="tac-keyword">goto</span> {result_html}'
    elif quad.op == '=':
        inst_html = f'{result_html} <span class="tac-op">=</span> <span class="tac-var">{arg1_str}</span>'
    else:
        inst_html = f'{result_html} <span class="tac-op">=</span> <span class="tac-var">{arg1_str}</span> <span class="tac-op">{quad.op}</span> <span class="tac-var">{arg2_str}</span>'
        
    return f'<div class="tac-row">{line_num_html}<span class="tac-code">{inst_html}</span></div>'


# Callback when sample selection changes
def on_sample_change():
    sel = st.session_state.sample_select
    if sel != "-- Select --":
        st.session_state.source_code = PRESETS[sel]
        st.session_state.play_tac_animation = True
        run_translation()
        # Reset selection to allow reloading the same sample
        st.session_state.sample_select = "-- Select --"

# Run translation on first startup so it's not empty
if "tokens" not in st.session_state and "error" not in st.session_state:
    st.session_state.play_tac_animation = False
    run_translation()

# Two-column layout using st.columns
col_left, col_right = st.columns([1, 1.2])

with col_left:
    # Load sample program selectbox
    st.selectbox(
        "Load a sample program",
        options=["-- Select --"] + list(PRESETS.keys()),
        key="sample_select",
        on_change=on_sample_change
    )
    # Text area for source code input and translate button
    st.text_area("Source code", height=400, key="source_code")
    translate_clicked = st.button("Translate")

with col_right:
    # Tabs for different visualizer outputs
    tab_tokens, tab_ast, tab_tac, tab_postfix, tab_symtable = st.tabs([
        "Tokens", "Annotated AST", "Three-Address Code", "Polish Notation", "Symbol Table"
    ])

# Execute pipeline on manual click of Translate button
if translate_clicked:
    st.session_state.play_tac_animation = True
    run_translation()

# Display compilation errors globally if any
error_msg = st.session_state.get("error")
if error_msg is not None:
    st.error(error_msg)

# 1. Tokens Tab
with tab_tokens:
    st.markdown('<h3 style="color: #5B8DEF; font-family: \'Outfit\', sans-serif; margin-bottom: 12px;">Tokens List</h3>', unsafe_allow_html=True)
    if error_msg:
        st.info("No tokens list available due to syntax error.")
    elif st.session_state.get("tokens") is not None:
        html_tokens = "<table class='custom-table tokens-table'><thead><tr><th>Type</th><th>Value</th><th>Line</th></tr></thead><tbody>"
        for t in st.session_state.tokens:
            html_tokens += f"<tr><td><span class='tok-type'>{t.type}</span></td><td><code>{t.value}</code></td><td>{t.line}</td></tr>"
        html_tokens += "</tbody></table>"
        st.markdown(html_tokens, unsafe_allow_html=True)
        
# 2. Annotated AST Tab
with tab_ast:
    st.markdown('<h3 style="color: #A78BFA; font-family: \'Outfit\', sans-serif; margin-bottom: 12px;">Annotated AST</h3>', unsafe_allow_html=True)
    if error_msg:
        st.info("No AST diagram available due to syntax error.")
    elif st.session_state.get("svg_str") is not None:
        # Embed SVG in an iframe wrapper
        st.components.v1.html(
            f"""
            <div style="
                display: flex; 
                justify-content: center; 
                align-items: center; 
                overflow: auto; 
                padding: 16px; 
                background-color: #161920; 
                border: 2.5px solid #A78BFA; 
                border-radius: 12px;
                box-shadow: inset 0 2px 4px 0 rgba(0,0,0,0.5);
            ">
                {st.session_state.svg_str}
            </div>
            """,
            height=500,
            scrolling=True
        )
        if st.session_state.get("ast_text") is not None:
            with st.expander("Show Text-based AST (Fallback)"):
                st.code(st.session_state.ast_text, language="text")

# 3. Three-Address Code Tab
with tab_tac:
    st.markdown('<h3 style="color: #2DD4BF; font-family: \'Outfit\', sans-serif; margin-bottom: 12px;">Three-Address Code (TAC)</h3>', unsafe_allow_html=True)
    if error_msg:
        st.info("No TAC instructions available due to syntax error.")
    else:
        col_before, col_after = st.columns(2)
        col_before.markdown('<h5 style="color: #94a3b8; font-family: \'Outfit\', sans-serif; margin-bottom: 8px;">1. Emitted TAC (Before Backpatching)</h5>', unsafe_allow_html=True)
        col_after.markdown('<h5 style="color: #94a3b8; font-family: \'Outfit\', sans-serif; margin-bottom: 8px;">2. Final TAC (After Backpatching)</h5>', unsafe_allow_html=True)
        
        emitted_history = st.session_state.get("emitted_history", [])
        tac_instructions = st.session_state.get("tac_instructions", [])
        
        if st.session_state.get("play_tac_animation", False) and (emitted_history or tac_instructions):
            # Run typewriter animation
            placeholder_before = col_before.empty()
            placeholder_after = col_after.empty()
            
            max_lines = max(len(emitted_history), len(tac_instructions))
            for i in range(1, max_lines + 1):
                # Before backpatching
                history_sub = emitted_history[:i]
                unpatched_html = "<div class='tac-container'>"
                if history_sub:
                    for idx, quad in enumerate(history_sub):
                        unpatched_html += format_quad_to_html(quad, idx, is_before=True)
                else:
                    unpatched_html += "<span class='tac-unresolved'>No TAC instructions emitted.</span>"
                unpatched_html += "</div>"
                placeholder_before.markdown(unpatched_html, unsafe_allow_html=True)
                
                # After backpatching
                tac_sub = tac_instructions[:i]
                patched_html = "<div class='tac-container'>"
                if tac_sub:
                    for idx, quad in enumerate(tac_sub):
                        patched_html += format_quad_to_html(quad, idx, is_before=False)
                else:
                    patched_html += "<span class='tac-unresolved'>No TAC instructions generated.</span>"
                patched_html += "</div>"
                placeholder_after.markdown(patched_html, unsafe_allow_html=True)
                
                import time
                time.sleep(0.3)
            
            st.session_state.play_tac_animation = False
        else:
            # Render instantly
            unpatched_html = "<div class='tac-container'>"
            if emitted_history:
                for idx, quad in enumerate(emitted_history):
                    unpatched_html += format_quad_to_html(quad, idx, is_before=True)
            else:
                unpatched_html += "<span class='tac-unresolved'>No TAC instructions emitted.</span>"
            unpatched_html += "</div>"
            col_before.markdown(unpatched_html, unsafe_allow_html=True)
            
            patched_html = "<div class='tac-container'>"
            if tac_instructions:
                for idx, quad in enumerate(tac_instructions):
                    patched_html += format_quad_to_html(quad, idx, is_before=False)
            else:
                patched_html += "<span class='tac-unresolved'>No TAC instructions generated.</span>"
            patched_html += "</div>"
            col_after.markdown(patched_html, unsafe_allow_html=True)
            
        # Display the backpatching trace if log is present
        if hasattr(tac, 'backpatch_log') and tac.backpatch_log:
            st.markdown('<h5 style="color: #2DD4BF; font-family: \'Outfit\', sans-serif; margin-top: 20px; margin-bottom: 8px;">Backpatching Resolution Trace</h5>', unsafe_allow_html=True)
            log_html = "<div class='backpatch-log-container'>"
            for log_entry in tac.backpatch_log:
                indices_str = ", ".join(f"[{i}]" for i in log_entry['indices'])
                target = log_entry['target']
                log_html += f"<div class='backpatch-log-line'>Backpatching instructions <span class='log-indices'>{indices_str}</span> with target jump address <span class='log-target'>{target}</span></div>"
            log_html += "</div>"
            st.markdown(log_html, unsafe_allow_html=True)

# 4. Polish Notation Tab
with tab_postfix:
    st.markdown('<h3 style="color: #FB7185; font-family: \'Outfit\', sans-serif; margin-bottom: 12px;">Polish Notation</h3>', unsafe_allow_html=True)
    if error_msg:
        st.info("No Polish notation available due to syntax error.")
    elif st.session_state.get("postfix_str") is not None:
        st.markdown(f'<div class="postfix-box">{st.session_state.postfix_str}</div>', unsafe_allow_html=True)

# 5. Symbol Table Tab
with tab_symtable:
    st.markdown('<h3 style="color: #A78BFA; font-family: \'Outfit\', sans-serif; margin-bottom: 12px;">Symbol Table</h3>', unsafe_allow_html=True)
    if error_msg:
        st.info("No Symbol Table available due to syntax error.")
    elif st.session_state.get("symbol_table") is not None:
        symbol_list = []
        for name, info in st.session_state.symbol_table.items():
            symbol_list.append({
                "Name": name,
                "Type": info.get("type", "int"),
                "Value": info.get("value", "Uninitialized"),
                "Line Declared": info.get("line", "-")
            })
        if symbol_list:
            df = pd.DataFrame(symbol_list)
            # Reorder columns
            df = df[["Name", "Type", "Value", "Line Declared"]]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No variables declared or initialized in this program.")
