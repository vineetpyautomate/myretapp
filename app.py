import streamlit as st
import pandas as pd
import re
from io import BytesIO

# --- GREEK & FREQUENCY MAPPING ---
GREEK_DIRS = {"Alpha": "1", "Beta": "2", "Gamma": "3", "Delta": "4", "Epsilon": "5", "Zeta": "6"}
FREQ_MAP = {"1": "ALPHA", "2": "BETA", "3": "GAMMA", "4": "DELTA", "5": "EPSILON", "6": "ZETA"}

st.set_page_config(layout="wide", page_title="Script Engine Pro")

# --- PROFESSIONAL COMPACT UI STYLING ---
st.markdown("""
    <style>
    /* Global font scale for 10-11 inch laptops */
    html, body, [class*="ViewContainer"] {
        font-size: 0.82rem !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    /* Tighten widget spacing */
    .stSelectbox, .stTextInput, .stMultiSelect { margin-bottom: -10px; }
    
    /* Technical Header */
    .main-header {
        background-color: #2c3e50;
        color: white;
        padding: 8px;
        border-radius: 4px;
        margin-bottom: 15px;
        font-weight: bold;
        text-align: center;
        font-size: 1rem;
    }
    
    /* Style for Block labels */
    .block-label {
        background-color: #f1f2f6;
        padding: 5px;
        border-radius: 3px;
        font-weight: bold;
        color: #2f3542;
        display: block;
        margin-bottom: 10px;
        border-left: 4px solid #3498db;
    }
    </style>
    <div class="main-header">PRO SCRIPT GENERATOR - WEB INTERFACE</div>
    """, unsafe_allow_html=True)

# --- ADDRESS LOGIC FUNCTION ---
def calculate_address(site_name, selected_names):
    if not selected_names: return site_name
    found_freqs = set()
    greek_name = ""
    
    for name in selected_names:
        # Regex to find the first underscore followed by 1-6
        match = re.search(r'_([1-6])', name)
        if match:
            code = match.group(1)
            greek_name = FREQ_MAP[code]
            
            # Identify specific suffixes
            if f"_{code}_2_3" in name: found_freqs.add("PCS")
            elif any(f"_{code}_{s}" in name for s in ["2_4", "2_6", "2_8"]): found_freqs.add("AWS")
            elif f"_{code}_7" in name: found_freqs.add("850")
            else: found_freqs.add("700") # Default if no suffix
            
    if greek_name:
        # Sorting priority: 700, 850, AWS, PCS
        order = {"700": 1, "850": 2, "AWS": 3, "PCS": 4}
        sorted_f = sorted(list(found_freqs), key=lambda x: order.get(x, 99))
        return f"{site_name}_{greek_name}_{'_'.join(sorted_f)}"
    return site_name

# --- SIDEBAR: DATA SOURCE ---
with st.sidebar:
    st.header("⚙ Config Manager")
    uploaded_file = st.file_uploader("Upload config.xlsx", type="xlsx")
    
    if uploaded_file:
        try:
            models_df = pd.read_excel(uploaded_file, sheet_name="Models")
            names_df = pd.read_excel(uploaded_file, sheet_name="Names")
            sources_df = pd.read_excel(uploaded_file, sheet_name="Source")
            
            model_opts = models_df["ModelName"].astype(str).tolist()
            name_opts = names_df["PersonName"].astype(str).tolist()
            source_opts = sources_df["VolName"].astype(str).tolist()
            st.success("Config Loaded")
        except Exception as e:
            st.error(f"Excel Error: {e}")
            st.stop()
    else:
        st.warning("Please upload config.xlsx to continue.")
        st.stop()

# --- 1. COORDINATE INPUT ---
st.markdown('<div class="block-label">1. INPUT COORDINATES</div>', unsafe_allow_html=True)
if 'rows' not in st.session_state:
    st.session_state.rows = [{"site": "", "model": model_opts[0], "pos": "", "dir": "Alpha"}]

def add_row():
    last_site = st.session_state.rows[-1]["site"]
    st.session_state.rows.append({"site": last_site, "model": model_opts[0], "pos": "", "dir": "Alpha"})

for idx, row in enumerate(st.session_state.rows):
    c1, c2, c3, c4, c5 = st.columns([2, 2.5, 1, 1.5, 0.5])
    st.session_state.rows[idx]["site"] = c1.text_input("Site", value=row["site"], key=f"site_{idx}", label_visibility="collapsed")
    st.session_state.rows[idx]["model"] = c2.selectbox("Model", model_opts, index=model_opts.index(row["model"]), key=f"mod_{idx}", label_visibility="collapsed")
    st.session_state.rows[idx]["pos"] = c3.text_input("Pos", value=row["pos"], key=f"pos_{idx}", label_visibility="collapsed", placeholder="Pos")
    st.session_state.rows[idx]["dir"] = c4.selectbox("Dir", list(GREEK_DIRS.keys()), index=list(GREEK_DIRS.keys()).index(row["dir"]), key=f"dir_{idx}", label_visibility="collapsed")
    if c5.button("✖", key=f"del_{idx}"):
        st.session_state.rows.pop(idx)
        st.rerun()

st.button("+ Add Row", on_click=add_row)

# --- 2. INITIALIZATION ---
if st.button("INITIALIZE BLOCKS", type="primary"):
    data_a, data_b = [], []
    curr_k, curr_n, curr_u = 1, 1, 1
    last_dir, last_pos = None, None

    for r in st.session_state.rows:
        if not r['model']: continue
        dr_code = GREEK_DIRS[r['dir']]
        m_info = models_df[models_df["ModelName"] == r['model']].iloc[0]
        motor, m_type = int(m_info["Motor"]), m_info["Type"]
        
        if last_dir and dr_code != last_dir: curr_k, curr_n, curr_u = 1, 1, 1
        elif last_pos and r['pos'] != last_pos: curr_k, curr_n, curr_u = 1, curr_n + 1, 1
        
        v_val = f"{dr_code}{r['pos']}"
        last_dir, last_pos = dr_code, r['pos']

        if str(m_type).upper() == "M":
            data_a.append({"v": v_val, "k": curr_k, "src": source_opts[0], "extra": "", "type": "17"})
            for i in range(1, motor + 1):
                data_b.append({"v": v_val, "k": curr_k, "t": i, "n": curr_n, "u": curr_u, "names": [], "site": r['site'], "tilt": "", "addr": r['site']})
                curr_u += 1
            curr_k += 1
        else:
            for _ in range(motor):
                data_a.append({"v": v_val, "k": curr_k, "src": source_opts[0], "extra": "", "type": "1"})
                data_b.append({"v": v_val, "k": curr_k, "t": 1, "n": curr_n, "u": curr_u, "names": [], "site": r['site'], "tilt": "", "addr": r['site']})
                curr_u += 1; curr_k += 1

    st.session_state.data_a = data_a
    st.session_state.data_b = data_b

# --- 3. WORKSPACE ---
if 'data_a' in st.session_state:
    st.divider()
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown('<div class="block-label">BLOCK A: SOURCES</div>', unsafe_allow_html=True)
        for idx, row in enumerate(st.session_state.data_a):
            c1, c2, c3 = st.columns([1, 1.5, 1.5])
            c1.code(f"V={row['v']} K={row['k']}")
            st.session_state.data_a[idx]["src"] = c2.selectbox(f"S_{idx}", source_opts, index=source_opts.index(row['src']), key=f"asrc_{idx}", label_visibility="collapsed")
            st.session_state.data_a[idx]["extra"] = c3.text_input(f"E_{idx}", value=row['extra'], placeholder="Extra Params", key=f"aex_{idx}", label_visibility="collapsed")

    with col_b:
        st.markdown('<div class="block-label">BLOCK B: NAMES & ADDRESS</div>', unsafe_allow_html=True)
        for idx, row in enumerate(st.session_state.data_b):
            c1, c2, c3 = st.columns([1.2, 2, 2])
            c1.code(f"V{row['v']}:K{row['k']}:T{row['t']}")
            sel_names = c2.multiselect(f"N_{idx}", name_opts, default=row['names'], key=f"bname_{idx}", label_visibility="collapsed")
            st.session_state.data_b[idx]["names"] = sel_names
            
            # Address Update Logic
            new_addr = calculate_address(row['site'], sel_names)
            st.session_state.data_b[idx]["addr"] = new_addr
            c3.text_input(f"A_{idx}", value=new_addr, key=f"addr_disp_{idx}", label_visibility="collapsed", disabled=True)

    # --- SCRIPT GENERATION ---
    st.divider()
    if st.button("🚀 GENERATE SCRIPT (PARTS 0-8)"):
        b = st.session_state.data_b
        a = st.session_state.data_a
        
        p0 = list(dict.fromkeys([f"cr Vineet={r['v']}" for r in b]))
        p1 = list(dict.fromkeys([f"cr Vineet={r['v']},Kumar={r['k']}" for r in b]))
        p2 = [f"set Vineet={r['v']},Kumar={r['k']} source={r['src']}" for r in a]
        p3 = [f"set Vineet={r['v']},Kumar={r['k']} extra={r['extra']}" for r in a]
        p4 = [f"set Vineet={r['v']},Kumar={r['k']} type={r['type']}" for r in a]
        p5 = [f"set Vineet={r['v']},Kumar={r['k']},Thakur={r['t']}{' name=' + ';'.join(r['names']) if r['names'] else ''} site={r['site']}" for r in b]
        p6 = [f"set V={r['v']},N={r['n']},U={r['u']} ref V={r['v']},K={r['k']},T={r['t']}" for r in b]
        p7 = [f"set Vineet={r['v']},Kumar={r['k']},Thakur={r['t']} tilt={r['tilt']}" for r in b]
        p8 = [f"set Vineet={r['v']},Kumar={r['k']},Thakur={r['t']} address={r['addr']}" for r in b]
        
        final = "\n\n".join([f"#part{i}\n" + "\n".join(eval(f"p{i}")) for i in range(9)])
        st.download_button("Click to Download Script", data=final, file_name="script_complete.txt", mime="text/plain")
