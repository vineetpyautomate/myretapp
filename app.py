import streamlit as st
import pandas as pd
import re
from io import BytesIO

# --- GREEK & FREQUENCY MAPPING ---
GREEK_DIRS = {"Alpha": "1", "Beta": "2", "Gamma": "3", "Delta": "4", "Epsilon": "5", "Zeta": "6"}
FREQ_MAP = {"1": "ALPHA", "2": "BETA", "3": "GAMMA", "4": "DELTA", "5": "EPSILON", "6": "ZETA"}

st.set_page_config(layout="wide", page_title="Vineet Script Engine Web")

# Custom CSS to make it look professional on 10-11 inch laptops
# Custom CSS to make it look professional on 10-11 inch laptops
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .stButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True) # Fixed parameter name here

st.title("🚀 Script Engine Pro (Web Edition)")

# --- HELPERS ---
def calculate_address(site_name, selected_names):
    if not selected_names or "None" in selected_names: return site_name
    found_freqs = set()
    greek_name = ""
    for name in selected_names:
        match = re.search(r'_([1-6])', name)
        if match:
            code = match.group(1)
            greek_name = FREQ_MAP[code]
            if f"_{code}_2_3" in name: found_freqs.add("PCS")
            elif any(f"_{code}_{s}" in name for s in ["2_4", "2_6", "2_8"]): found_freqs.add("AWS")
            elif f"_{code}_7" in name: found_freqs.add("850")
            else: found_freqs.add("700")
    if greek_name:
        order = {"700": 1, "850": 2, "AWS": 3, "PCS": 4}
        sorted_f = sorted(list(found_freqs), key=lambda x: order.get(x, 99))
        return f"{site_name}_{greek_name}_{'_'.join(sorted_f)}"
    return site_name

# --- SIDEBAR: CONFIG MANAGER ---
with st.sidebar:
    st.header("⚙ Config Manager")
    uploaded_file = st.file_uploader("Upload config.xlsx", type="xlsx")
    
    if uploaded_file:
        models_df = pd.read_excel(uploaded_file, sheet_name="Models")
        names_df = pd.read_excel(uploaded_file, sheet_name="Names")
        sources_df = pd.read_excel(uploaded_file, sheet_name="Source")
        
        model_opts = models_df["ModelName"].tolist()
        name_opts = names_df["PersonName"].tolist()
        source_opts = sources_df["VolName"].tolist()
    else:
        st.info("👋 Upload your config.xlsx to start.")
        st.stop()

# --- STEP 1: INPUT COORDINATES ---
st.subheader("1. Input Coordinates")
if 'rows' not in st.session_state:
    st.session_state.rows = [{"site": "", "model": model_opts[0], "pos": "", "dir": "Alpha"}]

def add_row():
    last_site = st.session_state.rows[-1]["site"]
    st.session_state.rows.append({"site": last_site, "model": model_opts[0], "pos": "", "dir": "Alpha"})

for idx, row in enumerate(st.session_state.rows):
    c1, c2, c3, c4, c5 = st.columns([2, 3, 1, 2, 0.5])
    st.session_state.rows[idx]["site"] = c1.text_input("Site Name", value=row["site"], key=f"s_{idx}")
    st.session_state.rows[idx]["model"] = c2.selectbox("Model", model_opts, index=model_opts.index(row["model"]), key=f"m_{idx}")
    st.session_state.rows[idx]["pos"] = c3.text_input("Pos", value=row["pos"], key=f"p_{idx}")
    st.session_state.rows[idx]["dir"] = c4.selectbox("Dir", list(GREEK_DIRS.keys()), index=list(GREEK_DIRS.keys()).index(row["dir"]), key=f"d_{idx}")
    if c5.button("✖", key=f"del_{idx}"):
        st.session_state.rows.pop(idx)
        st.rerun()

st.button("+ Add Row", on_click=add_row)

# --- STEP 2: INITIALIZE LOGIC ---
if st.button("INITIALIZE BLOCKS", type="primary"):
    data_a = []
    data_b = []
    
    curr_k, curr_n, curr_u = 1, 1, 1
    last_dir, last_pos = None, None

    for r in st.session_state.rows:
        dr_code = GREEK_DIRS[r['dir']]
        m_info = models_df[models_df["ModelName"] == r['model']].iloc[0]
        motor, m_type = int(m_info["Motor"]), m_info["Type"]
        
        if last_dir and dr_code != last_dir: curr_k, curr_n, curr_u = 1, 1, 1
        elif last_pos and r['pos'] != last_pos: curr_k, curr_n, curr_u = 1, curr_n + 1, 1
        
        v_val = f"{dr_code}{r['pos']}"
        last_dir, last_pos = dr_code, r['pos']

        if m_type == "M":
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

# --- STEP 3: WORKSPACE ---
if 'data_a' in st.session_state:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Block A: Sources")
        for idx, row in enumerate(st.session_state.data_a):
            c = st.columns([1, 1, 1, 0.5])
            st.session_state.data_a[idx]["src"] = c[1].selectbox(f"Src {row['v']}{row['k']}", source_opts, key=f"asrc_{idx}", label_visibility="collapsed")
            st.session_state.data_a[idx]["extra"] = c[2].text_input(f"Ex {idx}", placeholder="Extra", key=f"aex_{idx}", label_visibility="collapsed")

    with col_b:
        st.subheader("Block B: Details")
        for idx, row in enumerate(st.session_state.data_b):
            c = st.columns([1.5, 2, 1, 2])
            ref = f"V={row['v']} K={row['k']} T={row['t']}"
            sel_names = c[1].multiselect(ref, name_opts, key=f"bname_{idx}", label_visibility="collapsed")
            st.session_state.data_b[idx]["names"] = sel_names
            # Apply dynamic address logic
            st.session_state.data_b[idx]["addr"] = calculate_address(row['site'], sel_names)
            c[3].text(st.session_state.data_b[idx]["addr"])

    # --- FINAL GENERATION ---
    # --- FINAL GENERATION (Parts 0-8) ---
    if st.button("DOWNLOAD SCRIPT"):
        # Unique Headers
        p0 = list(dict.fromkeys([f"cr Vineet={r['v']}" for r in st.session_state.data_b]))
        p1 = list(dict.fromkeys([f"cr Vineet={r['v']},Kumar={r['k']}" for r in st.session_state.data_b]))
        
        # Attribute Sets
        p2 = [f"set Vineet={r['v']},Kumar={r['k']} source={r['src']}" for r in st.session_state.data_a]
        p3 = [f"set Vineet={r['v']},Kumar={r['k']} extra={r['extra']}" for r in st.session_state.data_a]
        p4 = [f"set Vineet={r['v']},Kumar={r['k']} type={r['type']}" for r in st.session_state.data_a]
        
        # Name/Site Sets
        p5 = [f"set Vineet={r['v']},Kumar={r['k']},Thakur={r['t']}{' name=' + ';'.join(r['names']) if r['names'] else ''} site={r['site']}" for r in st.session_state.data_b]
        
        # References and Details
        p6 = [f"set V={r['v']},N={r['n']},U={r['u']} ref V={r['v']},K={r['k']},T={r['t']}" for r in st.session_state.data_b]
        p7 = [f"set Vineet={r['v']},Kumar={r['k']},Thakur={r['t']} tilt={r['tilt']}" for r in st.session_state.data_b]
        p8 = [f"set Vineet={r['v']},Kumar={r['k']},Thakur={r['t']} address={r['addr']}" for r in st.session_state.data_b]
        
        # Combine everything
        final_txt = (
            "#part0\n" + "\n".join(p0) + "\n\n" +
            "#part1\n" + "\n".join(p1) + "\n\n" +
            "#part2\n" + "\n".join(p2) + "\n\n" +
            "#part3\n" + "\n".join(p3) + "\n\n" +
            "#part4\n" + "\n".join(p4) + "\n\n" +
            "#part5\n" + "\n".join(p5) + "\n\n" +
            "#part6\n" + "\n".join(p6) + "\n\n" +
            "#part7\n" + "\n".join(p7) + "\n\n" +
            "#part8\n" + "\n".join(p8)
        )
        
        st.download_button("Download TXT File", data=final_txt, file_name="vineet_script_complete.txt")
