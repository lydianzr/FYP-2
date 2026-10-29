"""Shared styling + small HTML helpers (no indentation in HTML so markdown doesn't treat it as code)."""
import streamlit as st

CSS = """
<style>
:root{--bg:#0b0d10;--panel:#101317;--panel-2:#161a20;--line:#232830;--ink:#e7ecf1;--ink-dim:#9aa4b2;--ink-soft:#6b7280;--accent:#7cc4ff;}
.block-container{max-width:1400px;padding-top:4rem;padding-bottom:2rem;}
.mono{font-family:'JetBrains Mono',ui-monospace,monospace;}
.hl{color:#a9d7ff;font-weight:600;}
.soft{color:var(--ink-soft);} .dim{color:var(--ink-dim);}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px;}
.panel-2{background:var(--panel-2);border:1px solid var(--line);border-radius:12px;padding:10px;}
.chip{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:500;border:1px solid var(--line);color:var(--ink-dim);background:#0e1216;margin:1px 2px 1px 0;}
.chip-accent{color:#a9d7ff;border-color:#274b6b;background:#0e1a24;}
.chip-good{color:#a7f3d0;border-color:#1f5138;background:#0f1c17;}
.chip-mid{color:#fde68a;border-color:#5b4a1a;background:#1c1810;}
.chip-low{color:#fecaca;border-color:#5c2626;background:#1c1212;}
.label{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-soft);margin-bottom:6px;}
.title{font-size:14px;font-weight:600;margin-bottom:8px;}
.metric-num{font-family:'JetBrains Mono',monospace;font-weight:600;letter-spacing:-.02em;}
.cite{display:inline-block;padding:1px 6px;border-radius:5px;font-size:11px;font-family:'JetBrains Mono',monospace;background:#0e1a24;color:#a9d7ff;border:1px solid #274b6b;margin:0 2px;}
.doc-thumb{background:#0e1216;border:1px solid var(--line);border-radius:8px;padding:12px;font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--ink-dim);line-height:1.5;}
.heat{border-radius:6px;padding:6px 8px;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;text-align:center;}
.heat-good{background:#0f2a1c;color:#4ade80;border:1px solid #1f5138;}
.heat-mid{background:#2a230f;color:#fbbf24;border:1px solid #5b4a1a;}
.heat-low{background:#2a1414;color:#f87171;border:1px solid #5c2626;}
.bar{height:5px;border-radius:3px;background:#1a2029;overflow:hidden;margin-top:4px;}
.bar>div{height:100%;border-radius:3px;}
.row{display:flex;justify-content:space-between;font-size:12px;}
table.t{width:100%;border-collapse:collapse;font-size:12px;}
table.t th{font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-soft);font-weight:500;padding:10px 8px;border-bottom:1px solid var(--line);text-align:center;}
table.t td{padding:8px;border-bottom:1px solid var(--line);}
table.t th:first-child,table.t td:first-child{text-align:left;}
.docrow{padding:8px;border-radius:8px;font-size:13px;margin-bottom:4px;}
.docrow.sel{background:#141920;border:1px solid #2a3340;}
.brand{display:flex;align-items:center;gap:12px;margin:12px 0 10px;min-height:32px;}
.logo{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#7cc4ff,#a48bff);display:flex;align-items:center;justify-content:center;color:#0b0d10;font-weight:700;}
.pipe{display:flex;align-items:center;gap:8px;overflow-x:auto;padding:8px 0 14px;border-bottom:1px solid var(--line);margin-bottom:18px;min-height:38px;box-sizing:border-box;}
.pstage{display:flex;align-items:center;gap:8px;padding:6px 12px;border-radius:8px;font-size:12px;color:var(--ink-soft);border:1px solid transparent;white-space:nowrap;}
.pnum{width:20px;height:20px;border-radius:50%;background:#1a2029;color:var(--ink-dim);font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;display:flex;align-items:center;justify-content:center;}
.pro{font-family:'JetBrains Mono',monospace;font-size:10px;padding:1px 5px;border-radius:4px;background:#0e1a24;color:#6b8fa8;border:1px solid #1e3a5f;}
.pstage.done{color:var(--ink-dim);} .pstage.done .pnum{background:#0f2a1c;color:#4ade80;}
.pstage.active{background:#141a22;border-color:#2b527f;color:var(--ink);}
.pstage.active .pnum{background:linear-gradient(135deg,#7cc4ff,#a48bff);color:#0b0d10;}
.pstage.active .pro{background:#1e3a5f;color:#c9e2ff;border-color:#2b527f;}
.parrow{color:#374151;}
.fbox{outline:1px solid;outline-offset:2px;border-radius:3px;display:inline-block;margin-top:2px;}
.fbox.good{outline-color:#4ade80;} .fbox.mid{outline-color:#fbbf24;} .fbox.nobox{outline:none;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def chip(text, kind="", mono=False):
    return f'<span class="chip {kind} {"mono" if mono else ""}">{text}</span>'


def page_header(title, desc, chips=()):
    c = "".join(chip(t, k) for t, k in chips)
    left, right = st.columns([3, 1])
    with left:
        st.markdown(f'<h2 style="margin:0;font-weight:600">{title}</h2>'
                    f'<p class="dim" style="font-size:14px;margin-top:4px">{desc}</p>', unsafe_allow_html=True)
    with right:
        st.markdown(f'<div style="text-align:right">{c}</div>', unsafe_allow_html=True)


def brand_header():
    st.markdown(
        '<div class="brand"><div class="logo">M</div><div>'
        '<div style="font-size:14px;font-weight:600;line-height:1.2">Logistics Doc Intelligence</div>'
        '<div class="soft" style="font-size:11px">Extract · Compare · Ask &nbsp;·&nbsp; Norlydia · 22002422</div>'
        '</div></div>', unsafe_allow_html=True)


PIPE = [("ingest", "Ingest", None), ("extract", "Extract Fields", "RO1"), ("compare", "Compare &amp; Route", "RO2"),
        ("index", "Index (fields + page vectors)", None), ("ask", "Ask", "RO3")]
STAGE_MAP = {"try": ["ingest", "extract"], "bench": ["compare"], "rag": ["index", "ask"]}


def pipeline_strip(tab):
    active = STAGE_MAP.get(tab, [])
    first = next((i for i, (k, _, _) in enumerate(PIPE) if k in active), 0)
    parts = ['<span class="label" style="margin:0 8px 0 0">Pipeline</span>']
    for i, (k, name, ro) in enumerate(PIPE):
        cls = "active" if k in active else ("done" if i < first else "")
        badge = f'<span class="pro">{ro}</span>' if ro else ""
        parts.append(f'<div class="pstage {cls}"><span class="pnum">{i+1}</span><span>{name}</span>{badge}</div>')
        if i < len(PIPE) - 1:
            parts.append('<span class="parrow">→</span>')
    parts.append('<span class="soft" style="margin-left:auto;font-size:11px">One system · three research objectives</span>')
    st.markdown(f'<div class="pipe">{"".join(parts)}</div>', unsafe_allow_html=True)


def conf_color(c):
    return "#4ade80" if c >= 0.80 else "#fbbf24" if c >= 0.50 else "#f87171"


def heat_cls(col, v):
    """Colour rules from the prototype. col = column index in BENCH_COLS."""
    if col == 3:   # CER, lower is better
        return "heat-good" if v < 0.20 else "heat-mid" if v < 0.40 else "heat-low"
    if col == 5:   # latency, seconds
        return "heat-good" if v < 2 else "heat-mid"
    return "heat-good" if v >= 0.80 else "heat-mid" if v >= 0.50 else "heat-low"


def bar(label, value_text, pct, color):
    return (f'<div style="margin-bottom:10px"><div class="row"><span>{label}</span>'
            f'<span class="mono dim">{value_text}</span></div>'
            f'<div class="bar"><div style="width:{pct*100:.0f}%;background:{color}"></div></div></div>')


def kpi(label, value, who, sub, color="#4ade80"):
    return (f'<div class="panel"><div class="label">{label}</div>'
            f'<div style="display:flex;align-items:baseline;gap:8px"><span class="metric-num" style="font-size:24px;color:{color}">{value}</span>'
            f'<span class="soft" style="font-size:12px">{who}</span></div>'
            f'<div class="soft" style="font-size:11px;margin-top:4px">{sub}</div></div>')
