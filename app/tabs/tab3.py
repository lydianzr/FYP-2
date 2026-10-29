import json, time
import streamlit as st
from utils import page_header, chip, conf_color

page_header(
    "Try It Yourself",
    "Run the extraction pipeline on a single document. Once extracted, the fields are added to the RAG index "
    "and the doc becomes queryable in the assistant.",
    [("Live demo", "chip-accent"), ("API + local models", "")],
)

ctrl, prev, res = st.columns([3, 5, 4])

# =============== LEFT: controls ===============
with ctrl:
    with st.container(border=True):
        up = st.file_uploader("1. Upload document", type=["pdf", "png", "jpg", "jpeg", "tiff"],
                              help="PDF · PNG · JPG · TIFF · up to 20 MB")
        fname = up.name if up else "air_waybill_0000.png"
        fsize = f"{up.size/1024:.0f} KB" if up else "142 KB"
        st.markdown(f'<div class="panel-2" style="font-size:12px">{chip("AWB", "", True)} {fname} '
                    f'<span class="soft mono" style="float:right">{fsize}</span></div>', unsafe_allow_html=True)
        st.write("")
        task = st.radio("2. Task", TASKS)
        model = st.selectbox("3. Model", MODELS)
        st.markdown('<div class="label" style="margin-top:8px">4. Options</div>', unsafe_allow_html=True)
        show_conf = st.checkbox("Return confidence scores", True)
        show_box = st.checkbox("Overlay bounding boxes", True)
        st.checkbox("Compare to ground truth", False)
        st.checkbox("Log to benchmark", False)
        if st.button("Run Extraction  →", type="primary", use_container_width=True):
            with st.spinner(f"Running {model}…"):
                time.sleep(1.2)  # TODO: call your real extraction pipeline here
            st.toast("Extraction complete")

# =============== CENTER: preview ===============
def fld(label, value, cls):
    box = cls if show_box else "nobox"
    return (f'<div><div class="soft" style="font-size:10px;text-transform:uppercase">{label}</div>'
            f'<div class="fbox {box}">{value}</div></div>')

with prev:
    with st.container(border=True):
        st.markdown('<div class="title">Document Preview</div>', unsafe_allow_html=True)
        if up and up.type.startswith("image/"):
            st.image(up)
        else:
            st.markdown(
                '<div class="doc-thumb" style="padding:24px;min-height:560px;font-size:12px;position:relative">'
                f'<div style="position:absolute;top:12px;right:12px">{chip("bounding boxes: " + ("on" if show_box else "off"), "", True)}</div>'
                '<div style="text-align:center;border-bottom:1px dashed var(--line);padding-bottom:12px;margin-bottom:18px">'
                '<div class="soft">AIR WAYBILL</div><div style="font-size:18px;font-weight:600;color:var(--ink)">170-59244148</div></div>'
                '<div style="display:flex;justify-content:space-between;margin-bottom:18px">'
                f'{fld("Shipper", "Bird Crawford and Dixon", "good")}{fld("Consignee", "Wade-Lamb", "good")}</div>'
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">'
                f'{fld("Origin", "Japan", "good")}{fld("Destination", "Singapore", "good")}'
                f'{fld("Airline", "Singapore Airlines", "mid")}{fld("Flight No", "CA642", "good")}'
                f'{fld("Departure", "2025-07-18", "good")}{fld("Weight", "3231.08 kg", "good")}'
                f'{fld("Volume", "11.82 m³", "mid")}{fld("Pieces", "7", "good")}</div>'
                '<div style="margin-top:80px;padding-top:10px;border-top:1px dashed var(--line);display:flex;justify-content:space-between;font-size:10px">'
                '<span>Page 1 of 1</span><span>170-59244148</span></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="soft" style="font-size:11px;margin-top:8px">'
                    '<span style="color:#4ade80">■</span> high conf &nbsp; <span style="color:#fbbf24">■</span> medium &nbsp; '
                    '<span style="color:#f87171">■</span> low / flagged</div>', unsafe_allow_html=True)

# =============== RIGHT: results ===============
as_dict = {k: v for k, v, _, _ in FIELDS}
as_json = json.dumps(as_dict, indent=2, ensure_ascii=False)
as_csv = "field,value,confidence\n" + "\n".join(f'{k},"{v}",{c}' for k, v, c, _ in FIELDS)

with res:
    with st.container(border=True):
        h1, h2 = st.columns([1.2, 1.6], vertical_alignment="center")
        h1.markdown('<div class="title" style="margin:0">Extracted Fields</div>', unsafe_allow_html=True)
        view = h2.radio("view", ["Structured", "JSON"], horizontal=True, label_visibility="collapsed")
        if view == "JSON":
            st.code(as_json, language="json")
        else:
            out = []
            for k, v, c, note in FIELDS:
                col = conf_color(c)
                conf_html = f'<span class="mono" style="font-size:10px;color:{col}">{c:.2f}</span>' if show_conf else ""
                note_html = f' {chip(note, "chip-mid", True)}' if note else ""
                bar_html = f'<div class="bar"><div style="width:{c*100:.0f}%;background:{col}"></div></div>' if show_conf else ""
                out.append(f'<div style="margin-bottom:10px;font-size:12px"><div class="row"><span class="soft">{k}</span>{conf_html}</div>'
                           f'<div class="mono">{v}{note_html}</div>{bar_html}</div>')
            st.markdown("".join(out), unsafe_allow_html=True)

    avg = sum(c for _, _, c, _ in FIELDS) / len(FIELDS)
    with st.container(border=True):
        st.markdown('<div class="title">Run summary</div>', unsafe_allow_html=True)
        m = st.columns(3)
        m[0].metric("Latency", "2.7s")
        m[1].metric("Fields", f"{len(FIELDS)} / 11")
        m[2].metric("Avg conf.", f"{avg:.2f}")
        st.caption('**1 field flagged.** `airline` was normalized ("Singapore" → "Singapore Airlines") using flight-number lookup. Review recommended before writing to ERP.')
        d1, d2 = st.columns(2)
        d1.download_button("Download JSON", as_json, "extraction.json", "application/json", use_container_width=True)
        d2.download_button("Download CSV", as_csv, "extraction.csv", "text/csv", use_container_width=True)

    with st.container(border=True):
        st.markdown(f'{chip("next", "chip-accent", True)} <b style="font-size:14px">Add to RAG corpus</b>', unsafe_allow_html=True)
        st.caption("Push the extracted fields to the structured index and the page image to ColQwen2. "
                   "The document becomes queryable in the assistant.")
        st.markdown(f'<div class="panel-2 mono dim" style="font-size:11px">+1 doc · +{len(FIELDS)} fields · +1 page vector<br/>'
                    '→ collection: <span class="hl">logistics_Q3_2025</span></div>', unsafe_allow_html=True)
        st.write("")
        if st.button("Add to corpus & open Assistant", type="primary", use_container_width=True):
            st.session_state.n_docs += 1
            st.session_state.n_fields += len(FIELDS)
            st.switch_page("tabs/tab3.py")
        st.caption("Same corpus the Assistant tab queries.")
