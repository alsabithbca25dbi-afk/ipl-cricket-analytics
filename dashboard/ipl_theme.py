"""IPL premium dark theme (charcoal cards, one orange accent) for the Streamlit dashboard.
Put this file next to your dashboard script (same folder)."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ---- Palette: near-black canvas, IPL orange accent, gold highlight ----------
BG, CARD, LINE, MUTED = "#0A0A0F", "#13131A", "#24242E", "#8B8B99"
ORANGE, GOLD, TEAL, NAVY, ROYAL = "#FF6B00", "#F5B301", "#2EE6D6", "#0A0A0F", "#13307A"
CSCALE = ["#3A1F0A", "#FF6B00", "#FFC24A"]
HEAT = ["#16161D", "#4A2108", "#B04A00", "#FF6B00", "#FFD27A"]
PALETTE = [ORANGE, GOLD, "#6C8CFF", TEAL, "#E63B7A", "#8E5CFF", "#7BD33F"]

TEAM_COLORS = {  # keyword (lowercase) -> franchise colour
    "chennai": "#F9CD1C", "mumbai": "#2F7FE0", "bangalore": "#E5262B", "bengaluru": "#E5262B",
    "kolkata": "#8B5CF6", "delhi": "#3B82F6", "capitals": "#3B82F6", "daredevils": "#3B82F6",
    "hyderabad": "#FF822A", "sunrisers": "#FF822A", "deccan": "#8FB4E3", "rajasthan": "#EA4F9B",
    "punjab": "#E8383D", "kings xi": "#E8383D", "gujarat titans": "#1FB5C6", "gujarat lions": "#F57C00",
    "lucknow": "#3AC1E8", "pune": "#B86BFF", "kochi": "#F07F2E",
}

def team_color(name):
    n = str(name).lower()
    for key, col in TEAM_COLORS.items():
        if key in n:
            return col
    return ORANGE

def team_color_map(names):
    return {n: team_color(n) for n in names}

def _rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Bebas+Neue&display=swap');
html, body, [class*="css"], .stApp {{ font-family:'Inter',sans-serif; }}
.stApp {{ background: radial-gradient(900px 480px at 100% -5%, #FF6B0026, transparent 60%),
  radial-gradient(700px 420px at 0% 0%, #F5B30014, transparent 60%), {BG}; color:#F2F2F7; }}
.block-container {{ padding-top:1.6rem; max-width:1320px; }}
header[data-testid="stHeader"] {{ background:transparent; }}
h1,h2,h3 {{ font-family:'Inter',sans-serif !important; letter-spacing:-.02em; font-weight:600 !important; color:#F2F2F7; }}

/* Top bar */
.topbar {{ position:relative; min-height:210px; padding:6px 4px 10px; }}
.brand {{ display:inline-flex; align-items:center; gap:10px; padding:6px 16px 6px 8px; border-radius:999px;
  background:{CARD}; border:1px solid {LINE}; font-weight:600; font-size:.95rem; }}
.brand .logo {{ width:28px; height:28px; border-radius:50%; display:grid; place-items:center; font-size:.95rem;
  background:linear-gradient(135deg,{GOLD},{ORANGE}); }}
.welcome {{ font-size:clamp(2.2rem,4.6vw,3.4rem); line-height:1.08; margin:22px 0 8px; font-weight:600; color:#F2F2F7; }}
.welcome span {{ color:#6B6B78; }}
.tagline {{ color:{MUTED}; max-width:52ch; margin:0; }}
/* Stadium illustration removed to keep the header clean. */

/* Cards */
.card {{ background:{CARD}; border:1px solid {LINE}; border-radius:20px; padding:22px 26px; animation: rise .6s ease-out both; }}
.card.eq {{ min-height:262px; }}
.card.tall {{ min-height:400px; }}
[data-testid="stAlert"] > div, [data-testid="stAlertContainer"] {{ background:#1C1408 !important; border:1px solid #5A3A00; border-radius:14px; }}
[data-testid="stAlert"] p {{ color:#FFD9A0 !important; }}
[data-testid="stAlert"] {{ margin:14px 0; }}
.lbl {{ color:{MUTED}; font-size:.9rem; font-weight:500; }}
.big {{ font-size:3.6rem; font-weight:700; letter-spacing:-.04em; line-height:1.1; margin:6px 0 4px; color:#fff; }}
.big span {{ color:#6B6B78; }} .big.sm {{ font-size:2.4rem; }}
.sub {{ color:#B9B9C6; font-size:.9rem; margin-top:4px; }} .foot {{ color:{MUTED}; font-size:.82rem; margin-top:18px; }}
.chip {{ display:inline-block; margin-top:14px; padding:4px 12px; border-radius:999px; font-size:.8rem; font-weight:600;
  color:#1a1200; background:linear-gradient(90deg,{GOLD},{ORANGE}); }}
.bars {{ display:flex; align-items:flex-end; gap:5px; height:118px; margin-top:12px; }}
.bars i {{ flex:1; border-radius:4px 4px 0 0; background:linear-gradient(180deg,{ORANGE},#5A2300);
  transform-origin:bottom; animation: grow .8s cubic-bezier(.2,.8,.2,1) both; transition:filter .2s; }}
.bars i:hover {{ filter:brightness(1.4); }}
.axis {{ display:flex; justify-content:space-between; color:{MUTED}; font-size:.78rem; margin-top:8px; }}
.row {{ display:flex; align-items:center; gap:10px; padding:13px 0; border-bottom:1px solid #1D1D26; font-size:.9rem; }}
.row b {{ flex:1; font-weight:500; }} .row em {{ font-style:normal; font-weight:600; color:{GOLD}; min-width:36px; text-align:right; }}
.pill {{ display:inline-flex; align-items:center; gap:6px; padding:3px 11px; border-radius:999px; background:#1E1E27; color:#B9B9C6; font-size:.76rem; }}
.pill i {{ width:6px; height:6px; border-radius:50%; background:{ORANGE}; }}
@keyframes rise {{ from{{opacity:0; transform:translateY(16px)}} to{{opacity:1; transform:none}} }}
@keyframes grow {{ from{{transform:scaleY(0)}} to{{transform:scaleY(1)}} }}

/* Native widgets */
[data-testid="stMetric"] {{ background:{CARD}; border:1px solid {LINE}; border-radius:18px; padding:18px 22px; transition:border-color .25s, transform .25s; }}
[data-testid="stMetric"]:hover {{ border-color:{ORANGE}; transform:translateY(-3px); }}
[data-testid="stMetricLabel"] p {{ color:{MUTED}; font-weight:500; }}
[data-testid="stMetricValue"] {{ font-weight:700; letter-spacing:-.03em; color:#fff; }}
[role="tablist"], [data-baseweb="tab-list"] {{ gap:6px; background:{CARD}; padding:5px; border-radius:999px; width:fit-content; border:1px solid {LINE}; }}
button[role="tab"], [data-testid="stTab"] {{ border-radius:999px; padding:7px 24px; color:#B9B9C6; background:transparent; transition:all .25s; }}
button[role="tab"][aria-selected="true"], [data-testid="stTab"][aria-selected="true"] {{ color:{BG}; background:#fff; }}
button[role="tab"] p, [data-testid="stTab"] p {{ color:inherit !important; font-weight:600; font-size:.95rem; }}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{ display:none; }}
[data-testid="stSidebar"] {{ background:#0E0E14; border-right:1px solid {LINE}; }}
[data-testid="stSidebar"] h1 {{ color:{GOLD}; font-size:1.3rem; }}
[data-testid="stExpander"] {{ background:{CARD}; border:1px solid {LINE}; border-radius:14px; }}
[data-testid="stExpander"] summary:hover {{ color:{GOLD}; }}
[data-testid="stPlotlyChart"] {{ background:{CARD}; border:1px solid {LINE}; border-radius:20px; overflow:hidden; padding:6px;
  animation: rise .7s ease-out both; transition:border-color .3s; }}
[data-testid="stPlotlyChart"]:hover {{ border-color:#FF6B0066; }}
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul {{ background:{CARD} !important; border:1px solid {LINE}; }}
[data-baseweb="popover"] li:hover {{ background:#1E1E27 !important; }}
.sec {{ margin:34px 0 4px; font-size:1.15rem; font-weight:600; }} .sec span {{ color:{MUTED}; font-weight:400; }}

/* Venue photo card */
.vcard {{ position:relative; height:240px; border-radius:20px; overflow:hidden; background:{CARD};
  border:1px solid {LINE}; animation: rise .6s ease-out both; }}
.vcard img.photo {{ width:100%; height:100%; object-fit:cover; animation: kb 16s ease-in-out infinite alternate; }}
@keyframes kb {{ from{{transform:scale(1)}} to{{transform:scale(1.12)}} }}
.vcard .fallback {{ height:100%; display:flex; align-items:center; justify-content:center;
  background:radial-gradient(circle at 50% 40%, #2A1608, {CARD} 70%); }}
.vcard .fallback img {{ width:88%; }}
.vcard .cap {{ position:absolute; left:0; right:0; bottom:0; padding:34px 18px 12px; background:linear-gradient(transparent,#0A0A0Ff2); }}
.vcard .cap b {{ font-size:1.25rem; font-weight:600; color:#fff; }}
.vcard .cap small {{ display:block; color:{GOLD}; font-weight:600; }}
.vcard .cap small.hint {{ color:{MUTED}; font-weight:400; font-size:.75rem; }}

@media (prefers-reduced-motion: reduce) {{ *, *::before, *::after {{ animation:none !important; transition:none !important; }} }}
</style>
"""

def inject_theme():
    st.markdown(CSS, unsafe_allow_html=True)

def _md(html):
    st.markdown(html.replace("\n", ""), unsafe_allow_html=True)

def header(title="Teams &amp; Venues", dim="Intelligence",
           tagline="Domain D · Explore team performance, ground conditions and match outcomes."):
    _md(f'<div class="topbar"><div class="brand"><span class="logo">🏏</span>IPL Analytics</div>'
        f'<h1 class="welcome">{title}<br><span>{dim}</span></h1><p class="tagline">{tagline}</p></div>')

def hero_card(label, value, sub="", foot=""):
    whole, dec = f"{value:.2f}".split(".")
    _md(f'<div class="card eq"><div class="lbl">{label}</div><div class="big">{whole}<span>.{dec}%</span></div>'
        f'<div class="sub">{sub}</div><div class="foot">{foot}</div></div>')

def season_bars(labels, values, title):
    if not values:
        return
    mx, avg = max(values) or 1, sum(values) / len(values)
    bars = "".join(f'<i title="{l}: {v}" style="height:{max(4, 100 * v / mx):.0f}%;animation-delay:{k * 0.04:.2f}s"></i>'
                   for k, (l, v) in enumerate(zip(labels, values)))
    _md(f'<div class="card eq"><div class="lbl">{title}</div><div class="big sm">{sum(values):,}<span> matches</span></div>'
        f'<div class="bars">{bars}</div><div class="axis"><span>{labels[0]}</span><span>avg {avg:.0f} per season</span>'
        f'<span>{labels[-1]}</span></div></div>')

def ground_list(title, rows):
    items = "".join(f'<div class="row"><b>{n}</b><span class="pill"><i></i>{p}</span><em>{v}</em></div>' for n, p, v in rows)
    _md(f'<div class="card tall"><div class="lbl">{title}</div>{items}</div>')

def section(title, dim=""):
    _md(f'<div class="sec">{title} <span>{dim}</span></div>')

def area_fig(df, x, y, title, color=ORANGE, ref=None, ref_label="50% reference", hover=()):
    tpl = "<b>%{x}</b><br>%{y:.1f}" + "".join(f"<br>{h}: %{{customdata[{i}]}}" for i, h in enumerate(hover)) + "<extra></extra>"
    fig = go.Figure(go.Scatter(
        x=df[x], y=df[y], mode="lines+markers", line=dict(color=color, width=3, shape="spline", smoothing=0.55),
        marker=dict(size=7, color=color, line=dict(width=2, color=CARD)), fill="tozeroy", fillcolor=_rgba(color, 0.16),
        customdata=df[list(hover)].values if hover else None, hovertemplate=tpl))
    lo, hi = float(df[y].min()), float(df[y].max())
    fig.update_yaxes(range=[max(0, lo - 12), min(100, hi + 10)])
    if ref is not None:
        fig.add_hline(y=ref, line_dash="dot", line_color=GOLD, annotation_text=ref_label, annotation_position="top left", annotation_font_color=GOLD)
    fig.update_layout(title=title)
    return fig

def heatmap_fig(pivot, title):
    fig = px.imshow(pivot, aspect="auto", zmin=0, zmax=100, labels=dict(color="Win %", x="Season", y="Team"))
    fig.update_layout(title=title, meta="heat")
    fig.update_xaxes(type="category", tickmode="array", tickvals=[str(c) for c in pivot.columns], tickangle=0)
    fig.update_yaxes(tickmode="array", tickvals=list(pivot.index), ticktext=list(pivot.index), automargin=True,
                     tickfont=dict(size=12))
    fig.update_layout(margin=dict(l=25, r=25, t=62, b=60))
    try:
        fig.update_traces(xgap=3, ygap=3)
    except Exception:
        pass
    return fig

def style_fig(fig, height=380):
    heat = fig.layout.meta == "heat"
    fig.update_layout(
        height=height, paper_bgcolor=CARD, plot_bgcolor=CARD, colorway=PALETTE,
        font=dict(family="Inter, sans-serif", color="#E8E8F0", size=12),
        title=dict(font=dict(family="Inter, sans-serif", size=16, color="#F2F2F7"), x=0.02),
        margin=dict(l=25, r=25, t=62, b=35),
        hoverlabel=dict(bgcolor="#1E1E27", bordercolor=ORANGE, font=dict(family="Inter", color="#fff")),
        coloraxis=dict(colorscale=HEAT if heat else CSCALE), legend=dict(bgcolor="rgba(0,0,0,0)"),
        transition=dict(duration=500, easing="cubic-in-out"))
    fig.update_xaxes(gridcolor="#1F1F28", zerolinecolor="#1F1F28", linecolor=LINE)
    fig.update_yaxes(gridcolor="#1F1F28", zerolinecolor="#1F1F28", linecolor=LINE)
    try:
        fig.update_traces(selector=dict(type="bar"), marker_cornerradius=6)
    except Exception:
        pass
    return fig

