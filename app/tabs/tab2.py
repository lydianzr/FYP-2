import io, csv
import streamlit as st
from utils import page_header, chip, heat_cls, bar, kpi

page_header(
    "Benchmark Dashboard",
    "The study that decides which model extracts what. Findings here become the routing rules that populate the RAG index.",
    [("RO1 · Extraction", "chip-accent"), ("RO2 · Comparison", "chip-accent")],
)

# ---- filter bar (visual only: hook these up to your results dataframe) ----
f = st.columns([2, 2, 2, 1.2, 1.2], vertical_alignment="bottom")
f[0].selectbox("Dataset", ["DocILE", "SROIE", "DocVQA", "INNONICS (30)", "Synthetic (500)", "All combined"])
f[1].selectbox("Task", ["All", "A · Text fields", "B · Table structure", "C · Visual elements", "D · Handwritten", "E · Multi-page"])
f[2].selectbox("Doc type", ["All", "Air Waybill", "Invoice", "Bill of Lading", "Packing List", "Purchase Order", "Delivery Order"])
f[3].markdown(chip("n = 812 documents", "", True), unsafe_allow_html=True)

buf = io.StringIO()
w = csv.writer(buf)
w.writerow(["model", "type"] + [c.replace("|", " ") for c in BENCH_COLS])
for n, k, v in BENCH_ROWS:
    w.writerow([n, k] + v)
f[4].download_button("Export CSV", buf.getvalue(), "benchmark.csv", "text/csv", use_container_width=True)

# ---- KPI row ----
k = st.columns(4)
k[0].markdown(kpi("Best F1 (Text Fields)", "0.912", "Qwen2-VL 7B", "+0.24 vs Tesseract baseline"), unsafe_allow_html=True)
k[1].markdown(kpi("Best TEDS (Tables)", "0.847", "GPT-4o", "OCR baseline: 0.31"), unsafe_allow_html=True)
k[2].markdown(kpi("Fastest MLLM", "1.4s", "LayoutLMv3", "per document, local GPU", "#a9d7ff"), unsafe_allow_html=True)
k[3].markdown(kpi("Lowest FAR", "0.06", "GPT-4o", "false-acceptance rate"), unsafe_allow_html=True)

# ---- main table + side panels ----
main, side = st.columns([8, 4])
with main:
    head = "".join(f'<th>{c.split("|")[0]}<br/><span style="text-transform:none">{c.split("|")[1]}</span></th>' for c in BENCH_COLS)
    body = []
    for name, kind, vals in BENCH_ROWS:
        cells = "".join(f'<td><div class="heat {heat_cls(i, v)}">{v}</div></td>' for i, v in enumerate(vals))
        body.append(f'<tr><td><div style="font-size:14px;font-weight:500">{name}</div><div class="soft" style="font-size:10px">{kind}</div></td>{cells}</tr>')
    st.markdown(
        '<div class="panel" style="padding:0">'
        '<div style="padding:12px 18px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between">'
        '<div class="title" style="margin:0">Model × Task performance</div>'
        '<div class="soft" style="font-size:11px">metric: task-appropriate (F1 / TEDS / CER)</div></div>'
        f'<table class="t mono"><thead><tr><th>Model</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'
        '<div class="soft" style="padding:12px 18px;font-size:11px;display:flex;justify-content:space-between">'
        '<span>Green ≥ 0.80 · Amber 0.50–0.79 · Red &lt; 0.50 · CER lower is better (inverted)</span>'
        '<span>95% CI via bootstrap · seed = 42</span></div></div>', unsafe_allow_html=True)

with side:
    bars = "".join(bar(n, f"{v:.2f}", v, "#4ade80") for n, v in F1_BY_TYPE)
    st.markdown(f'<div class="panel"><div class="title">F1 by Document Type · Qwen2-VL</div>{bars}</div>', unsafe_allow_html=True)

    li = "".join(f'<li style="display:flex;gap:8px;margin-bottom:8px"><span style="color:{c}">{ic}</span>'
                 f'<span><b style="color:var(--ink)">{t}</b> — {d}</span></li>' for ic, c, t, d in FINDINGS)
    st.markdown(f'<div class="panel"><div class="title">Where MLLMs actually win</div>'
                f'<ul class="dim" style="list-style:none;padding:0;margin:0;font-size:12px;line-height:1.5">{li}</ul></div>', unsafe_allow_html=True)

    st.markdown('<div class="panel"><div class="title">Statistical notes</div><div class="dim" style="font-size:11px;line-height:1.6">'
                "McNemar's test between GPT-4o vs Qwen2-VL on Task A: <span class='mono'>p = 0.32</span> (n.s.). "
                "On Task B: <span class='mono'>p = 0.008</span> (significant).<br/><br/>"
                "Held-out INNONICS test set (n=30) shows the same ranking as DocILE, supporting external validity."
                '</div></div>', unsafe_allow_html=True)

# ---- hand-off to RO3 ----
r1, r2 = st.columns([7, 5])
with r1:
    rows = "".join(
        f'<tr><td style="text-align:left">{d}</td><td style="text-align:left">{chip(m, "chip-accent", True)}</td>'
        f'<td class="dim" style="text-align:left">{why}</td><td style="color:#4ade80">{g}</td></tr>'
        for d, m, why, g in ROUTING)
    st.markdown(
        '<div class="panel"><div class="title" style="margin:0">Routing decisions derived from this study</div>'
        '<div class="soft" style="font-size:11px;margin-bottom:8px">The extraction pipeline that feeds the RAG index uses these rules.</div>'
        '<table class="t mono"><thead><tr><th>Doc type</th><th style="text-align:left">Chosen model</th>'
        f'<th style="text-align:left">Why</th><th>F1 gain vs baseline</th></tr></thead><tbody>{rows}</tbody></table></div>',
        unsafe_allow_html=True)
    st.page_link("tabs/tab2.py", label="Open RAG index →")

with r2:
    bars = "".join(bar(n, f"Faithfulness {v:.2f}", v, c) for n, v, c in ABLATION)
    st.markdown(
        '<div class="panel" style="background:linear-gradient(180deg,#0e1a24 0%,#101317 60%);border-color:#1e3a5f">'
        f'<div style="margin-bottom:10px">{chip("RO1 · RO2 → RO3", "chip-accent", True)} <b style="font-size:14px">Impact on downstream RAG</b></div>'
        '<div class="dim" style="font-size:11px;margin-bottom:14px">Ablation on n=100 held-out queries. Same retriever, same LLM, only the extraction pipeline changes.</div>'
        f'{bars}<hr style="border-color:var(--line)"/>'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;text-align:center">'
        '<div class="panel-2"><div class="soft" style="font-size:10px">Answer accuracy</div><div class="metric-num" style="color:#4ade80">+22%</div></div>'
        '<div class="panel-2"><div class="soft" style="font-size:10px">Hallucinated fields</div><div class="metric-num" style="color:#4ade80">−68%</div></div></div>'
        '<div class="dim" style="font-size:11px;margin-top:12px"><b style="color:var(--ink)">Read this as:</b> RO3 quality is bounded by RO1 quality. '
        'The comparative study (RO2) is what allows us to pick the right extractor per doc type.</div></div>',
        unsafe_allow_html=True)
