"""Noval Properties Advisor – Streamlit app.

Answers natural-language questions about the Noval Properties portfolio, e.g.
  * "Provide a list of properties of Noval Properties"
  * "Show offices in Athens"
  * "What is the total portfolio value?"
  * "Chart value by city"
  * "Rank the properties in decreasing area"
  * "Which is the largest building?"
  * "Top 3 cities by total value" / "Which type has the lowest occupancy?"
  * "What are the investment criteria?" / "What are the capex limits?" (investment policy)
  * "Tell me about <property name>"

Data: the 16 Noval buildings from `noval_portfolio.csv` are embedded in this file
(see PORTFOLIO_ROWS). There is no upload feature.
Policy: the Greek-language Investment Policy (Board-approved 29.07.2026) is embedded as an
English knowledge base (see POLICY_ENTRIES); policy questions are always answered in English.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------
# Page configuration
# ------------------------------
st.set_page_config(
    page_title="Noval Properties Advisor",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------
# McKinsey-inspired styling
# ------------------------------
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Inter:wght@400;500;600;700&display=swap');

      :root {
        --deep-blue: #051C2C;
        --electric-blue: #2251FF;
        --light-blue: #EAF0FF;
        --gray: #5A6872;
        --border: #D9DEE3;
        --background: #F5F0E6;
      }

      html, body, [class*="css"] {
        font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
        color: #1A1A1A;
        background: var(--background);
      }

      #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {
        visibility: hidden;
      }

      /* Keep the header (it holds the arrow that re-opens the sidebar), but make it invisible */
      header[data-testid="stHeader"] {
        background: transparent !important;
      }

      [data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"] {
        visibility: visible !important;
        z-index: 1000;
      }

      [data-testid="stExpandSidebarButton"] *, [data-testid="collapsedControl"] * {
        color: var(--deep-blue) !important;
      }

      .block-container {
        padding-top: 0;
        padding-bottom: 6rem;
        max-width: 1240px;
      }

      .brand-bar {
        background: var(--deep-blue);
        color: #FFFFFF;
        padding: 0.75rem 2rem;
        margin: 0 -5.5rem 0 -5.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .brand-name {
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: -0.01em;
      }

      .brand-tag {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        opacity: 0.75;
      }

      .hero {
        padding: 2.4rem 0 1.8rem 0;
      }

      .hero-eyebrow {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: var(--electric-blue);
        margin-bottom: 0.7rem;
      }

      .hero-title {
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 3rem;
        line-height: 1.06;
        font-weight: 700;
        color: var(--deep-blue);
        max-width: 780px;
        margin-bottom: 0.9rem;
      }

      .hero-subtitle {
        font-size: 1.08rem;
        line-height: 1.55;
        color: var(--gray);
        max-width: 700px;
        margin-bottom: 1.5rem;
      }

      .hero-rule {
        width: 72px;
        height: 4px;
        background: var(--electric-blue);
        margin-bottom: 1.8rem;
      }

      .card {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-top: 3px solid var(--deep-blue);
        padding: 1.15rem 1.25rem;
        height: 100%;
      }

      .card-label {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--gray);
        margin-bottom: 0.35rem;
      }

      .card-value {
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--deep-blue);
      }

      .card-note {
        font-size: 0.79rem;
        color: var(--gray);
        margin-top: 0.3rem;
      }

      .section-title {
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--deep-blue);
        margin-bottom: 0.35rem;
      }

      .section-subtitle {
        font-size: 0.95rem;
        color: var(--gray);
        margin-bottom: 1rem;
      }

      .rule {
        height: 1px;
        background: var(--border);
        margin: 1.3rem 0 1.6rem 0;
      }

      .sidebar .sidebar-content {
        background: var(--deep-blue);
        color: #FFFFFF;
      }

      .sidebar .sidebar-content * {
        color: #FFFFFF !important;
      }

      .sidebar .sidebar-content h3,
      .sidebar .sidebar-content h4 {
        font-family: 'Source Serif 4', Georgia, serif;
        font-weight: 700;
      }

      .sidebar .stTextInput input,
      .sidebar .stSelectbox div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        color: #FFFFFF !important;
      }

      .stButton > button {
        width: 100%;
        border: 1px solid rgba(255,255,255,0.35);
        background: transparent;
        color: #FFFFFF !important;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 0;
        padding: 0.55rem 0.75rem;
        transition: all 0.15s ease;
      }

      .stButton > button:hover {
        background: var(--electric-blue);
        border-color: var(--electric-blue);
        color: #FFFFFF !important;
      }

      .stChatMessage {
        border: none;
        border-radius: 0;
        background: transparent;
      }

      .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background: #EDE5D6;
      }

      .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
        background: var(--background) !important;
      }

      [data-testid="stBottom"], [data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"],
      [data-testid="stChatInput"], [data-testid="stChatInput"] > div, .stChatInput > div {
        background: var(--background) !important;
      }

      .stChatInput textarea {
        background: var(--background) !important;
        border: 1px solid var(--border) !important;
        border-radius: 0 !important;
        font-size: 0.95rem !important;
      }

      .stChatInput button {
        background: var(--deep-blue) !important;
        color: #FFFFFF !important;
        border-radius: 0 !important;
      }

      a {
        color: var(--electric-blue);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar / button fixes (current Streamlit DOM selectors)
st.markdown(
    """
    <style>
      section[data-testid="stSidebar"] { background: var(--deep-blue); }
      section[data-testid="stSidebar"] * { color: #FFFFFF; }
      section[data-testid="stSidebar"] .stButton > button {
        border: 1px solid rgba(255,255,255,0.35);
        background: transparent;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# Data layer – the dataset is embedded in the app (source: noval_portfolio.csv).
# To update it, edit PORTFOLIO_ROWS below. None = not available.
# ------------------------------
PORTFOLIO_COLUMNS = [
    "name", "type", "country", "city", "region", "postal_code", "area_sqm", "value_eur",
    "annual_income_eur", "occupancy_pct", "status", "year_built", "note",
]
PORTFOLIO_ROWS = [
    ('The Orbit Office Campus', 'Office', 'Greece', 'Athens', 'Attica', '11524', 39664, None, None, None, 'Operating', None, 'GLA per report; LEED Platinum, flagship'),
    ('Butterfly Office Building', 'Office', 'Greece', 'Chalandri', 'Attica', '15231', 10144, None, None, None, 'Operating', None, 'GLA per report; LEED Gold, flagship'),
    ('Mare West Retail Park', 'Retail', 'Greece', 'Corinth', 'Peloponnese', '20007', 14503, None, None, None, 'Operating', None, 'BREEAM In-Use certified'),
    ('River West Shopping Centre', 'Retail', 'Greece', 'Athens', 'Attica', '12241', 63380, None, None, None, 'Operating', None, 'Expanded 2023'),
    ('IKEA Megastore', 'Retail', 'Greece', 'Athens', 'Attica', '12241', 25194, None, None, None, 'Operating', None, 'Flagship asset'),
    ('Wyndham Grand Athens', 'Hospitality', 'Greece', 'Athens', 'Attica', '10437', 23524, None, None, None, 'Operating', None, '5* hotel'),
    ('Mandra Logistics Center', 'Industrial', 'Greece', 'Mandra', 'Attica', '19600', 25538, None, None, None, 'Under development', None, 'Targeting LEED Gold; status as of 2023 report'),
    ('Cheimaras 16 Office Building', 'Office', 'Greece', 'Marousi', 'Attica', '15125', 24948, None, None, None, 'Under development', None, 'Targeting LEED Gold; status as of 2023 report'),
    ('Ardittos House Mixed-use Building', 'Mixed-use', 'Greece', 'Athens', 'Attica', '11636', 4284, None, None, None, 'Delivered 2025', None, "Mets; 'Ardittos House' – status from 2025 results coverage"),
    ('Kifisias 199 Office Building', 'Office', 'Greece', 'Marousi', 'Attica', '15124', 2074, None, None, None, 'Under development', None, 'Reconstruction targeting LEED Gold; status as of 2023 report'),
    ('Amarousiou Chalandriou', 'Office', 'Greece', 'Chalandri', 'Attica', '15125', 4092, None, None, None, 'Under development', None, 'Targeting LEED Gold; status as of 2023 report'),
    ('The Grid Office Campus', 'Office', 'Greece', 'Marousi', 'Attica', '15125', 16119, None, None, None, 'Under development', None, '50% participation via THE GRID SA; targeting LEED Platinum'),
    ('Pireos 252', 'Mixed-use', 'Greece', 'Athens', 'Attica', '17778', 56740, None, None, None, 'Under development', None, 'Urban regeneration project'),
    ('East Park Office Building', 'Office', 'Bulgaria', 'Sofia', None, '1407', 7337, None, None, None, None, None, None),
    ('Ethnikis Antistaseos Office Complex', 'Office', 'Greece', 'Chalandri', 'Attica', '15231', 6914, None, None, None, None, None, None),
    ('Vitruvit', 'Industrial', 'Greece', 'Veroia', 'Imathia', '57011', 56740, None, None, None, None, None, None),
]

NUMERIC_COLS = ["area_sqm", "value_eur", "annual_income_eur", "occupancy_pct", "year_built"]
FILTER_COLS = ["type", "country", "city", "region", "status"]
DIMENSION_WORDS = {
    "type": ["type", "category", "asset class", "use"],
    "country": ["country"],
    "city": ["city", "location"],
    "region": ["region"],
    "status": ["status"],
}
LIST_COLS = ["name", "type", "country", "city", "area_sqm", "value_eur", "occupancy_pct", "status"]
COLUMN_LABELS = {
    "name": "Building", "type": "Type", "country": "Country", "city": "City", "region": "Region",
    "postal_code": "Postal code", "area_sqm": "GLA (sqm)", "value_eur": "Value (€)",
    "annual_income_eur": "Annual income (€)", "occupancy_pct": "Occupancy (%)",
    "status": "Status", "year_built": "Year built",
    "note": "Note", "rank": "#", "value_per_sqm": "Value per sqm (€)", "yield_pct": "Gross yield (%)",
}
COMPANY_NOTE = (
    "Building-level values are not in the dataset. For reference, Noval's FY2025 annual report shows "
    "total investments of about €679M at 31 Dec 2025 (about €693.6M including its share of THE GRID's property)."
)


@st.cache_data(show_spinner=False)
def load_portfolio() -> pd.DataFrame:
    df = pd.DataFrame(PORTFOLIO_ROWS, columns=PORTFOLIO_COLUMNS)
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["name", "postal_code", "note", *FILTER_COLS]:
        df[col] = df[col].astype("string").str.strip()
    return df


# ------------------------------
# Formatting helpers
# ------------------------------
def eur(value: float) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    if abs(value) >= 1_000_000:
        return f"€{value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"€{value / 1_000:,.0f}K"
    return f"€{value:,.0f}"


def portfolio_metrics(df: pd.DataFrame) -> dict:
    """Aggregates over columns that actually contain data (never report an empty sum as 0)."""
    m: dict = {"count": len(df)}
    for key, col in (("area", "area_sqm"), ("value", "value_eur"), ("income", "annual_income_eur")):
        if col in df and df[col].notna().any():
            m[key] = df[col].sum()
            m[f"{key}_n"] = int(df[col].notna().sum())
    if "occupancy_pct" in df and df["occupancy_pct"].notna().any():
        occ = df.dropna(subset=["occupancy_pct"])
        if "area_sqm" in occ and occ["area_sqm"].sum() > 0:
            m["occupancy"] = (occ["occupancy_pct"] * occ["area_sqm"]).sum() / occ["area_sqm"].sum()
        else:
            m["occupancy"] = occ["occupancy_pct"].mean()
    return m


# ------------------------------
# Question answering
# ------------------------------
@dataclass
class Reply:
    text: str
    table: Optional[pd.DataFrame] = None
    chart: Optional[pd.Series] = None
    chart_title: str = ""


def _mentions(text: str, value: str) -> bool:
    v = str(value).lower().strip()
    return bool(v) and re.search(rf"\b{re.escape(v)}(s|es)?\b", text) is not None


def detect_filters(text: str, df: pd.DataFrame) -> dict[str, list[str]]:
    """Find values from filterable columns (type/city/region/status) named in the question."""
    found: dict[str, list[str]] = {}
    for col in FILTER_COLS:
        if col not in df:
            continue
        hits = [v for v in df[col].dropna().unique() if _mentions(text, v)]
        if hits:
            found[col] = hits
    return found


def apply_filters(df: pd.DataFrame, filters: dict[str, list[str]]) -> pd.DataFrame:
    for col, values in filters.items():
        df = df[df[col].isin(values)]
    return df


def describe_filters(filters: dict[str, list[str]]) -> str:
    if not filters:
        return ""
    return " (" + "; ".join(f"{c}: {', '.join(v)}" for c, v in filters.items()) + ")"


def list_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in LIST_COLS if c in df.columns and df[c].notna().any()]
    return df[cols] if cols else df


def metrics_text(m: dict, company_note: bool = True) -> str:
    def cov(key: str) -> str:
        n = m.get(f"{key}_n")
        return f" _(data for {n} of {m['count']} buildings)_" if n is not None and n < m["count"] else ""

    lines = [f"- **Buildings:** {m['count']}"]
    if "area" in m:
        lines.append(f"- **Total area:** {m['area']:,.0f} sqm{cov('area')}")
    if "value" in m:
        lines.append(f"- **Portfolio value:** {eur(m['value'])}{cov('value')}")
    if "income" in m:
        lines.append(f"- **Annual income:** {eur(m['income'])}{cov('income')}")
    if "occupancy" in m:
        lines.append(f"- **Occupancy (area-weighted):** {m['occupancy']:.0f}%")
    text = "\n".join(lines)
    if "value" not in m and company_note:
        text += f"\n\n{COMPANY_NOTE}"
    return text


# ------------------------------
# Ranking / superlatives
# ------------------------------
# (key, keyword regex, label, columns required). Order matters: the most specific
# metrics are tested first so "highest value per sqm" is not read as plain "value".
RANK_METRICS = [
    ("value_per_sqm", r"per (sqm|square|m2|m²)|value density|price per", "value per sqm", ["value_eur", "area_sqm"]),
    ("yield_pct", r"\byield\b|return on", "gross yield", ["annual_income_eur", "value_eur"]),
    ("value_eur", r"value|worth|valuation|price|expensive|valuable|cheap", "value", ["value_eur"]),
    ("annual_income_eur", r"income|rent|revenue|earning", "annual income", ["annual_income_eur"]),
    ("occupancy_pct", r"occupan|occupied|vacan", "occupancy", ["occupancy_pct"]),
    ("year_built", r"\byears?\b|built|oldest|newest|\bage\b", "year built", ["year_built"]),
    ("area_sqm", r"area|sqm|square|gla|size|large|biggest|smallest|\bbig\b|\bsmall\b", "GLA", ["area_sqm"]),
]
RANK_GATE = (
    r"\b(rank\w*|sort\w*|order\w*|top|bottom|decreasing|increasing|descending|ascending|"
    r"highest|lowest|largest|smallest|biggest|most|least|cheapest|oldest|newest|best|worst|"
    r"maximum|minimum|max|min)\b"
)
ASC_WORDS = r"\b(increasing|ascending|lowest|smallest|least|cheapest|bottom|worst|fewest|minimum|min|oldest)\b"
STRONG_DESC = r"\b(decreasing|descending|highest|largest|biggest|maximum|max|newest|greatest)\b"
NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_NUM = r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
DIM_RANK_PATTERNS = {
    "type": r"\b(types?|categories|category)\b",
    "country": r"\bcountr(y|ies)\b",
    "city": r"\bcit(y|ies)\b",
    "region": r"\bregions?\b",
    "status": r"\bstatus(es)?\b",
}


DIM_PLURALS = {"type": "Types", "country": "Countries", "city": "Cities", "region": "Regions", "status": "Statuses"}


def with_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed metrics (value per sqm, gross yield) when their inputs exist."""
    df = df.copy()
    if {"value_eur", "area_sqm"} <= set(df.columns):
        df["value_per_sqm"] = (df["value_eur"] / df["area_sqm"].where(df["area_sqm"] > 0)).round(0)
    if {"annual_income_eur", "value_eur"} <= set(df.columns):
        df["yield_pct"] = (df["annual_income_eur"] / df["value_eur"].where(df["value_eur"] > 0) * 100).round(2)
    return df


def fmt_metric(key: str, v: float) -> str:
    if pd.isna(v):
        return "n/a"
    if key in ("value_eur", "annual_income_eur"):
        return eur(v)
    if key == "value_per_sqm":
        return f"€{v:,.0f}/sqm"
    if key == "area_sqm":
        return f"{v:,.0f} sqm"
    if key == "occupancy_pct":
        return f"{v:.0f}%"
    if key == "yield_pct":
        return f"{v:.1f}%"
    return f"{v:.0f}"


def _parse_count(text: str) -> Optional[int]:
    m = re.search(rf"\b(?:top|bottom|first|last)\s+{_NUM}\b", text) or re.search(
        rf"\b{_NUM}\s+(?:\w+\s+)?(?:propert\w*|assets?|buildings?|largest|biggest|smallest|highest|lowest|cheapest|oldest|newest)\b",
        text,
    )
    if not m:
        return None
    raw = m.group(1)
    return int(raw) if raw.isdigit() else NUM_WORDS[raw]


def rank_reply(text: str, scoped: pd.DataFrame, scope: str) -> Optional[Reply]:
    """Handle 'rank/sort/top N/highest/lowest/which is the largest…' questions.

    Returns None when the question is not a ranking question.
    """
    if not re.search(RANK_GATE, text):
        return None

    # --- metric
    metric = next((m for m in RANK_METRICS if re.search(m[1], text)), None)
    has_prop_word = re.search(r"\b(propert\w*|assets?|buildings?)\b", text)
    wants_dim = next(
        (d for d, pat in DIM_RANK_PATTERNS.items()
         if d in scoped.columns and re.search(pat, text)
         and (not has_prop_word
              or re.search(rf"\b(which|what|top\s+\w+|bottom\s+\w+)\s+(?:{pat})", text))),
        None,
    )
    if metric is None and wants_dim is None:
        return Reply(
            "Which measure should I rank by? Try **GLA (area)**, **value**, **annual income**, "
            "**occupancy**, **year built**, **value per sqm** or **yield** – "
            "e.g. “Rank the properties in decreasing area”."
        )

    if scoped.empty:
        return Reply(f"No buildings match that filter{scope}.")

    data = with_derived(scoped)
    if metric is not None:
        key, _, label, needed = metric
        missing = [c for c in needed if c not in scoped.columns]
        if missing:
            return Reply(f"The dataset has no {label} figures (missing: {', '.join(missing)}).")
    else:
        key, label = None, "number of buildings"

    # --- direction
    asc = bool(re.search(ASC_WORDS, text)) and not re.search(STRONG_DESC, text)
    if re.search(r"vacan", text):          # "highest vacancy" == lowest occupancy
        asc = not asc
    word = "lowest" if asc else "highest"
    if key == "area_sqm":
        word = "smallest" if asc else "largest"
    elif key == "year_built":
        word = "oldest" if asc else "newest"

    # --- how many rows
    n = _parse_count(text)
    explicit_all = re.search(r"\b(rank\w*|sort\w*|order\w*|list|show|decreasing|increasing|descending|ascending)\b", text)
    plural = re.search(r"\b(properties|assets|buildings|cities|countries|types|regions)\b", text)
    top_bottom = re.search(r"\b(top|bottom)\b", text)

    # ---------- ranking of groups (city / type / region / status) ----------
    if wants_dim:
        g = data.groupby(wants_dim)
        if key is None:
            series, label_col = g.size(), "Number of buildings"
        elif key == "value_per_sqm":
            series, label_col = g["value_eur"].sum() / g["area_sqm"].sum(), "Value per sqm (€)"
        elif key == "yield_pct":
            series, label_col = g["annual_income_eur"].sum() / g["value_eur"].sum() * 100, "Gross yield (%)"
        elif key in ("occupancy_pct", "year_built"):
            series, label_col = g[key].mean(), COLUMN_LABELS[key]
        else:
            series, label_col = g[key].sum(), "Total " + COLUMN_LABELS[key]
        series = series.dropna().sort_values(ascending=asc, kind="stable")
        if series.empty:
            return Reply(f"The dataset has no {label} figures to rank by{scope}.")
        dim_plural = re.search(r"\b(cities|countries|types|regions|statuses)\b", text)
        if n is None:
            n = 5 if top_bottom else (len(series) if explicit_all or dim_plural else 1)
        shown = series.head(n)
        table = shown.rename(label_col).reset_index().rename(columns={wants_dim: COLUMN_LABELS.get(wants_dim, wants_dim)})
        table.insert(0, "rank", range(1, len(table) + 1))
        if len(shown) == 1:
            name, val = shown.index[0], shown.iloc[0]
            shown_val = f"{val:,.0f}" if key is None else fmt_metric(key or "", val)
            return Reply(
                f"The {wants_dim} with the {word} {label} is **{name}** ({shown_val}){scope}.",
                table=table,
            )
        chart = shown.copy()
        chart.index = [f"{i:02d}. {v}" for i, v in enumerate(shown.index, 1)]
        return Reply(
            f"{DIM_PLURALS[wants_dim]} ranked by **{label}**, {word} first{scope}:",
            table=table, chart=chart, chart_title=f"{label_col} by {wants_dim}",
        )

    # ---------- ranking of individual properties ----------
    valid = data.dropna(subset=[key])
    excluded = len(data) - len(valid)
    if valid.empty:
        return Reply(f"The dataset has no {label} figures for these buildings{scope}.")
    ranked = valid.sort_values(key, ascending=asc, kind="stable")
    if n is None:
        if top_bottom:
            n = 5
        elif explicit_all:
            n = len(ranked)
        elif plural:
            n = 5
        else:
            n = 1
    note = f" ({excluded} without {label} data excluded.)" if excluded else ""

    if n == 1:
        best = ranked[ranked[key] == ranked[key].iloc[0]]   # keep ties
        names = ", ".join(f"**{x}**" for x in best["name"])
        verb = "have" if len(best) > 1 else "has"
        tie = " (tied)" if len(best) > 1 else ""
        cols = [c for c in ["name", "type", "city", "area_sqm", "value_eur", "occupancy_pct", "status"] if c in best]
        if key not in cols:
            cols.insert(1, key)
        cols = [c for c in cols if c == key or best[c].notna().any()]
        if key == "year_built":
            msg = f"{names} {'are' if len(best) > 1 else 'is'} the {word} building{tie}: built {fmt_metric(key, best[key].iloc[0])}{scope}.{note}"
        else:
            msg = f"{names} {verb} the {word} {label}{tie}: {fmt_metric(key, best[key].iloc[0])}{scope}.{note}"
        return Reply(msg, table=best[cols])

    top = ranked.head(n).copy()
    top.insert(0, "rank", range(1, len(top) + 1))
    cols = ["rank", "name", key] + [c for c in ["type", "city", "status"] if c in top and c != key]
    chart = top.set_index(top.apply(lambda r: f"{int(r['rank']):02d}. {r['name']}", axis=1))[key]
    direction = "lowest to highest" if asc else "highest to lowest"
    size = "" if n >= len(ranked) else f" – showing {n} of {len(ranked)}"
    return Reply(
        f"Buildings ranked by **{label}**, {direction}{scope}{size}.{note}",
        table=top[cols], chart=chart, chart_title=f"{label.capitalize()} by building",
    )


# ------------------------------
# Financial reports knowledge base
# Source: Noval Property Annual Financial Reports FY2025 (March 2026) and FY2024.
# Figures are the company's individual/economic-interest IFRS statements, in euros.
# None = not reported in the sections loaded. Ratios are as reported in each year's report.
# ------------------------------
FIN_LABEL = "Annual Financial Reports FY2024 & FY2025"
FIN_YEARS = [2023, 2024, 2025]
FIN_METRICS = [
    # key, label, unit, {year: value}, keyword pattern (most specific first), report section
    ("net_ltv", "Net LTV", "pct", {2024: 19.5, 2025: 20.7}, r"net ltv|net loan.to.value", "Key indicators"),
    ("ltv", "Loan-to-value (LTV)", "pct", {2024: 31.0, 2025: 27.8}, r"\bltv\b|loan.to.value|leverage", "Key indicators, FY2025"),
    ("gearing", "Gearing ratio (borrowings / total assets)", "pct", {2023: 34.1, 2024: 28.2, 2025: 26.3}, r"gearing", "Key indicators"),
    ("quick", "Quick ratio", "x", {2024: 3.08, 2025: 3.52}, r"quick ratio|liquidity ratio|current ratio", "Key indicators"),
    ("nav", "Book value per share (NAV)", "eps", {2023: 3.98, 2024: 4.11, 2025: 4.39}, r"\bnav\b|book value|net asset value", "Key indicators"),
    ("eps", "Basic earnings per share", "eps", {2023: 0.60, 2024: 0.40, 2025: 0.32}, r"earnings per share|\beps\b", "Income statement"),
    ("ebitda", "Adjusted EBITDA (excl. fair-value effects)", "eur", {2024: 20_582_000, 2025: 26_177_000}, r"ebitda", "Key indicators"),
    ("rental", "Rental income", "eur", {2023: 29_338_698, 2024: 33_416_846, 2025: 37_788_006}, r"rental income|\brent(al)?s?\b|revenues?|turnover|sales", "Income statement"),
    ("fv_gain", "Fair-value gain on investment property", "eur", {2023: 47_639_595, 2024: 24_496_831, 2025: 20_188_438}, r"fair.value (gain|adjust)|revaluation|valuation gain", "Income statement"),
    ("op_profit", "Operating profit", "eur", {2023: 65_122_986, 2024: 44_685_892, 2025: 45_810_725}, r"operating (profit|result)", "Income statement"),
    ("pbt", "Profit before tax", "eur", {2023: 67_459_534, 2024: 50_836_982, 2025: 43_494_236}, r"(profit|earnings) before tax|\bpbt\b", "Income statement"),
    ("profit", "Profit after tax", "eur", {2023: 64_606_897, 2024: 47_264_114, 2025: 40_992_941}, r"profit|net income|earnings|bottom line|results", "Income statement"),
    ("tax", "Income tax", "eur", {2023: 2_852_637, 2024: 3_572_868, 2025: 2_501_295}, r"\btax(es|ation)?\b", "Income statement"),
    ("fin_exp", "Financial expenses", "eur", {2023: 8_517_873, 2024: 8_315_157, 2025: 6_659_428}, r"financial (cost|expense)s?|interest (cost|expense)s?|finance costs?", "Income statement"),
    ("fin_inc", "Financial income", "eur", {2023: 2_014_641, 2024: 5_905_717, 2025: 3_008_249}, r"financial income|interest income", "Income statement"),
    ("jv", "Share of profit from joint ventures (THE GRID)", "eur", {2023: 8_839_780, 2024: 8_560_530, 2025: 1_334_690}, r"joint venture|the grid|\bjv\b", "Income statement"),
    ("staff", "Personnel expenses", "eur", {2023: 3_915_331, 2024: 5_351_211, 2025: 4_317_893}, r"personnel|staff|payroll|salaries", "Income statement"),
    ("assets", "Total assets", "eur", {2023: 670_237_820, 2024: 746_230_395, 2025: 767_340_827}, r"total assets", "Balance sheet"),
    ("inv_prop", "Investment property (balance sheet)", "eur", {2023: 557_312_240, 2024: 616_702_637, 2025: 657_588_053}, r"investment propert|portfolio value|fair value of the portfolio|total investments|portfolio (is )?worth", "Balance sheet"),
    ("cash", "Cash and cash equivalents", "eur", {2023: 74_578_151, 2024: 72_788_823, 2025: 47_648_353}, r"\bcash\b(?! flow)|liquidity", "Balance sheet"),
    ("equity", "Total equity", "eur", {2023: 427_389_810, 2024: 519_098_806, 2025: 554_898_867}, r"equity|shareholders.? funds", "Balance sheet"),
    ("liabilities", "Total liabilities", "eur", {2023: 242_848_010, 2024: 227_131_589, 2025: 212_441_963}, r"liabilit", "Balance sheet"),
    ("net_debt", "Net borrowings (after cash and committed deposits)", "eur", {2024: 126_143_777, 2025: 143_438_422}, r"net (debt|borrowings)", "Key indicators"),
    ("debt", "Total borrowings incl. finance leases", "eur", {2024: 210_230_147, 2025: 201_866_110}, r"borrowings?|\bdebt\b|loans?\b|indebted|green bond|leverage", "Management report"),
    ("cfo", "Net cash from operating activities", "eur", {2023: 11_757_619, 2024: 9_759_808, 2025: 10_908_826}, r"operating cash|cash from operat|cash flow from operat|operating activities|cash flow", "Cash flow statement"),
    ("cfi", "Net cash from investing activities", "eur", {2023: -26_094_608, 2024: -39_954_301, 2025: -21_803_601}, r"investing (activities|cash)", "Cash flow statement"),
    ("cff", "Net cash from financing activities", "eur", {2023: 598_997, 2024: 28_405_165, 2025: -14_245_695}, r"financing (activities|cash)", "Cash flow statement"),
    ("capex", "Purchases / improvements of investment properties", "eur", {2023: 26_670_308, 2024: 33_203_301, 2025: 23_487_328}, r"capex|capital expenditure|improvements|development spend|acquisitions", "Cash flow statement"),
    ("div_paid", "Dividends paid to shareholders", "eur", {2023: 2_186_956, 2024: 3_158_134, 2025: 5_436_574}, r"dividends? paid|dividend|payout|distribut", "Cash flow statement"),
]
FIN_TRIGGER = (
    r"ltv|loan.to.value|gearing|quick ratio|\bnav\b|book value|earnings per share|\beps\b|ebitda|rental income|"
    r"revenue|turnover|profit|net income|operating (result|cash)|\bcash\b|equity|liabilit|borrowings?|\bdebt\b|green bond|"
    r"total assets|dividend|fair.value (gain|adjust)|revaluation|financial (report|statements?|results?|performance|position|"
    r"highlights|expenses|income|cost)|annual report|balance sheet|income statement|cash flow|funds from operations|\bffo\b|"
    r"personnel|payroll|portfolio value|total investments|capex|capital expenditure|the grid|\bjv\b|joint venture|"
    r"fy\s?20(24|25)|\b202[345]\b.*\b(results|figures|numbers)|share count|shares outstanding|own shares|share capital|"
    r"\btax(es|ation)? (paid|charge|expense)|income tax|segment|net (debt|borrowings)"
)

FIN_SEGMENTS = {  # investment property by business segment (balance sheet, euros)
    "Offices": {2024: 161_437_957, 2025: 210_030_087},
    "Retail": {2024: 209_181_109, 2025: 223_908_073},
    "Industrial": {2024: 43_057_789, 2025: 45_507_879},
    "Hospitality": {2024: 48_017_029, 2025: 48_798_965},
    "Other": {2024: 155_008_753, 2025: 129_343_050},
}
FIN_GEO = {  # (rental income, investment property) by geography
    "Greece": {"rent": {2024: 32_913_682, 2025: 37_481_281}, "ip": {2024: 609_773_361, 2025: 650_605_307}},
    "Bulgaria": {"rent": {2024: 503_164, 2025: 306_724}, "ip": {2024: 6_929_276, 2025: 6_982_746}},
}


def fin_fmt(unit: str, v: Optional[float]) -> str:
    if v is None or pd.isna(v):
        return "n/a"
    if unit == "pct":
        return f"{v:.1f}%"
    if unit == "x":
        return f"{v:.2f}x"
    if unit == "eps":
        return f"€{v:.2f}"
    sign = "-" if v < 0 else ""
    a = abs(v)
    return f"{sign}€{a / 1e6:,.1f}M" if a >= 1e6 else f"{sign}€{a / 1e3:,.0f}K"


def _fin_change(unit: str, a: Optional[float], b: Optional[float]) -> str:
    if a is None or b is None:
        return "–"
    if unit in ("pct", "x"):
        return f"{b - a:+.1f} pp" if unit == "pct" else f"{b - a:+.2f}x"
    if a == 0:
        return "–"
    return f"{(b - a) / abs(a) * 100:+.0f}%"


def _fin_table(metrics: list, years: list[int]) -> pd.DataFrame:
    rows = []
    for key, label, unit, vals, _, _ in metrics:
        row = {"Metric": label}
        for y in years:
            row[str(y)] = fin_fmt(unit, vals.get(y))
        if len(years) >= 2:
            row[f"Change {years[-2]}→{years[-1]}"] = _fin_change(unit, vals.get(years[-2]), vals.get(years[-1]))
        rows.append(row)
    return pd.DataFrame(rows)


FIN_SUMMARY_KEYS = ["rental", "ebitda", "profit", "eps", "assets", "equity", "nav", "debt", "ltv", "cash", "div_paid"]
FIN_FACTS = (
    "**Portfolio (31.12.2025):** 61 properties (60 valued by independent valuers; one is held 50% through THE GRID joint venture "
    "and accounted for by the equity method); one property is in Sofia, Bulgaria, the rest in Greece. The 2025 report states a "
    "total portfolio fair value of about €693.6M including the Company's share of THE GRID's property; the 'total investments' "
    "figure in the key-indicators footnote is €679.0M (2024: €648.3M).\n\n"
    "**Dividend:** the Board proposed (2 March 2026) €0.07 per share for FY2025, +63% on the FY2024 dividend. "
    "REICs must distribute at least 50% of distributable annual profit (Art. 55, Law 5193/2025).\n\n"
    "**Funding:** borrowings of €187.6M at end-2025 (bank €68.9M; Green Bond €118.7M), versus €195.9M at end-2024 "
    "(bank €77.6M; Green Bond €118.3M). The €120M Green Bond proceeds were fully allocated by 31.12.2025."
)


def finance_reply(text: str) -> Optional[Reply]:
    """Answer questions about the FY2024/FY2025 annual financial reports (English)."""
    if not re.search(FIN_TRIGGER, text):
        return None
    if re.search(r"polic|criteria|article 46", text) and not re.search(r"financial (report|statement|result)|annual report|fy\s?20", text):
        return None
    years = sorted({int(y) for y in re.findall(r"\b(202[345])\b", text)} | {int(y) for y in re.findall(r"\bfy\s?(?:20)?(2[345])\b", text, re.I) if False})
    years = [y for y in years if y in FIN_YEARS]
    src = f"\n\n_Source: Noval Property {FIN_LABEL} (company figures, individual IFRS statements)._"

    # segments / geography
    if re.search(r"segment|by (business )?(type|sector)|offices? (vs|versus)|bulgaria|greece|geograph", text) and \
            re.search(r"revenue|rent|investment propert|segment|assets|value|geograph", text):
        if re.search(r"bulgaria|greece|geograph", text):
            rows = []
            for g, d in FIN_GEO.items():
                rows.append({"Region": g, "Rental income 2024": fin_fmt("eur", d["rent"][2024]), "Rental income 2025": fin_fmt("eur", d["rent"][2025]),
                             "Investment property 2024": fin_fmt("eur", d["ip"][2024]), "Investment property 2025": fin_fmt("eur", d["ip"][2025])})
            return Reply("**Geographic split (company segment note)** – Greece generated almost all rental income; Bulgaria (one property in Sofia) "
                         "contributed €0.31M in 2025 (2024: €0.50M)." + src, table=pd.DataFrame(rows))
        rows = [{"Segment": k, "2024": fin_fmt("eur", v[2024]), "2025": fin_fmt("eur", v[2025]), "Change": _fin_change("eur", v[2024], v[2025])}
                for k, v in FIN_SEGMENTS.items()]
        chart = pd.Series({k: v[2025] for k, v in FIN_SEGMENTS.items()}).sort_values(ascending=False)
        return Reply("**Investment property by segment (balance sheet, 31 December)**" + src, table=pd.DataFrame(rows),
                     chart=chart, chart_title="Investment property by segment, 2025 (€)")

    if re.search(r"funds from operations|\bffo\b", text):
        return Reply("**Funds from operations (FY2025 report):** profit after tax excluding fair-value revaluation, sale results, depreciation, "
                     "impairment and financial-income effects was **€18.3M in 2025** (2024: €10.9M)." + src)

    if re.search(r"dividend|payout|distribut", text) and not re.search(r"cash flow", text):
        t = _fin_table([m for m in FIN_METRICS if m[0] == "div_paid"], FIN_YEARS)
        return Reply("**Dividends**\n\nThe Board proposed a dividend of **€0.07 per share for FY2025**, up 63% on the FY2024 dividend. "
                     "REICs must distribute at least 50% of distributable annual profit (Art. 55, Law 5193/2025). "
                     "Cash dividends paid to shareholders:" + src, table=t)

    if re.search(r"share capital|shares outstanding|share count|own shares|number of shares", text):
        return Reply("**Share capital:** €316,079,895, divided into 126,431,958 ordinary registered shares of €2.50 nominal value, listed on the Athens "
                     "Stock Exchange. In 2025 the Company bought own shares for €0.67M (none in 2024)." + src)

    hit = []
    for m in FIN_METRICS:
        if re.search(m[4], text) and m not in hit:
            hit.append(m)
            if m[0] in ("net_debt", "net_ltv", "ltv", "quick", "nav", "eps", "ebitda", "cfi", "cff", "pbt", "op_profit", "assets"):
                break  # specific metric matched first: stop
    if re.search(r"overview|summar|highlights|key (figures|numbers|metrics)|financial (report|statements?|results?|performance|position)|annual report", text) and not hit:
        hit = [m for m in FIN_METRICS if m[0] in FIN_SUMMARY_KEYS]
        hit = [next(x for x in FIN_METRICS if x[0] == k) for k in FIN_SUMMARY_KEYS]
        t = _fin_table(hit, years if len(years) >= 1 else [2024, 2025])
        return Reply("## Financial highlights – FY2024 vs FY2025\n\n" + FIN_FACTS + src, table=t)
    if not hit:
        hit = [next(x for x in FIN_METRICS if x[0] == k) for k in FIN_SUMMARY_KEYS]
        return Reply("## Financial highlights – FY2024 vs FY2025\n\n" + FIN_FACTS + src, table=_fin_table(hit, [2024, 2025]))
    hit = hit[:4]
    use_years = years if years else FIN_YEARS
    if years and len(years) == 1:
        use_years = years
    table = _fin_table(hit, use_years)
    first = hit[0]
    if len(hit) == 1 and len(use_years) == 1:
        v = first[3].get(use_years[0])
        return Reply(f"**{first[1]}, {use_years[0]}:** {fin_fmt(first[2], v)}." + src, table=table)
    # trend sentence + chart for a single metric
    avail = {y: v for y, v in first[3].items() if y in use_years and v is not None}
    chart, title = None, ""
    msg = f"**{first[1]}**" if len(hit) == 1 else "**Financial figures**"
    if len(hit) == 1 and len(avail) >= 2 and first[2] in ("eur", "eps"):
        chart = pd.Series({str(y): v for y, v in avail.items()})
        title = f"{first[1]} (€)"
    note = ""
    if len(hit) == 1 and len(avail) >= 2:
        ys = sorted(avail)
        note = (f"\n\n{fin_fmt(first[2], avail[ys[0]])} in {ys[0]} → {fin_fmt(first[2], avail[ys[-1]])} in {ys[-1]} "
                f"({_fin_change(first[2], avail[ys[0]], avail[ys[-1]])}).")
    if len(hit) == 1 and first[0] in ("ebitda", "ltv", "net_ltv", "quick", "debt"):
        note += "\n\n_Only FY2024 and FY2025 are available for this measure in the loaded reports._"
    if first[0] == "profit":
        note += ("\n\n_Profit includes non-cash fair-value revaluation gains (2025: €20.2M; 2024: €24.5M). "
                "Excluding fair-value, sale, depreciation, impairment and financial-income effects, profit was €18.3M in 2025 vs €10.9M in 2024._")
    return Reply(msg + note + src, table=table, chart=chart, chart_title=title)


# ------------------------------
# Investment policy knowledge base
# Source: «Επενδυτική Πολιτική» of NOVAL PROPERTY REIC (Greek original), version 1,
# approved by the Board of Directors on 29.07.2026. The content below is an English
# translation/summary of that document, organised by topic; section numbers refer to
# the original. Answers are always given in English.
# ------------------------------
POLICY_LABEL = "Investment Policy v1 (Board-approved 29.07.2026)"
POLICY_SUMMARY_PATTERN = (
    r"summar|overview of (the )?(investment )?polic|main points|key points|key takeaways|tl;?dr|policy overview|περίληψ|"
    r"(about|explain|describe) (the )?(investment )?polic(y|ies)\??\s*$|"
    r"what (is|does) (the )?(investment )?polic(y|ies)( say| cover| contain| include)?\??\s*$"
)

POLICY_ENTRIES = [
    {
        "id": "purpose", "section": "§1–2", "title": "Purpose and principles",
        "strong": [r"purpose|objectives?|principles?|\bgoals?\b|\baims?\b|mission|σκοπ"],
        "medium": [r"strategy|long.term|shareholders?|value creation|diversif"],
        "weak": [r"invest"],
        "text": (
            "**Purpose and principles**\n\n"
            "The policy aims to create long-term added value for shareholders by building and managing a "
            "diversified, high-specification property portfolio that is resilient to market fluctuations, "
            "follows sustainable-development principles and sound risk management, and is adequately "
            "diversified by use, geographic location and tenant characteristics.\n\n"
            "In particular, the Company seeks to:\n"
            "- build a portfolio with adequate diversification by use, location and tenant profile;\n"
            "- create value through active, effective management of its properties and through targeted, "
            "eligible new investments and developments;\n"
            "- generate stable, sustainable cash flows, with an emphasis on competitive returns;\n"
            "- keep a balance between targeted return and the investment risk taken, in line with its risk profile;\n"
            "- integrate environmental, social and governance (ESG) criteria at every stage – acquisition, "
            "development and management of properties."
        ),
    },
    {
        "id": "return_risk", "section": "§1–2", "title": "Return and risk approach",
        "strong": [r"risk profile|risk.return|volatility|resilien|active(ly)? manag|business plan|cash.?flows?|κίνδυν"],
        "medium": [r"returns?|risk|stable|diversified portfolio|απόδοσ"],
        "weak": [r"invest"],
        "text": (
            "**Return and risk approach**\n\n"
            "The policy targets a diversified portfolio of high-quality properties with low volatility, adequate "
            "diversification and resilience to market changes. The Company pursues competitive returns and "
            "value creation for shareholders through stable, sustainable cash flows and profitability, taking into "
            "account its investment profile and acceptable level of risk.\n\n"
            "It aims to maximise long-term returns through effective financial management, efficient use of "
            "available capital and active portfolio management, using the instruments the REIC legal framework "
            "permits within acceptable risk, for the best return/risk balance. The policy is implemented through "
            "the Company's business plan, which reflects market dynamics, economic conditions and macroeconomic data."
        ),
    },
    {
        "id": "permitted", "section": "§3.1", "title": "Permitted investments",
        "strong": [r"permitted|allowed to invest|can (noval|the company) invest|may invest|eligible|what.*invest in|"
                   r"investment scope|scope of (the )?invest|article 46|άρθρο 46"],
        "medium": [r"allow(ed|s)?\b|renewable|\bres\b|battery|storage|solar|photovoltaic|abroad|foreign|outside greece|overseas|"
                   r"third countr|eu member|subsidiar|shares|units|ανανεώσιμ|μπαταρ"],
        "weak": [r"invest"],
        "text": (
            "**Permitted investments**\n\n"
            "Within the range set by Article 46 of Law 5193/2025 (and subject to the specific terms and limits it sets "
            "for each category), the Company may invest in:\n"
            "- **real estate** located in Greece, in another EU/EEA member state or in a third country – directly, "
            "or indirectly through subsidiaries or participation in collective investment schemes;\n"
            "- **renewable-energy generation and storage plants** (combined with a battery system), solely for own "
            "consumption / self-consumption, with a maximum installed capacity not above the total contracted "
            "capacity of its properties' supply connections;\n"
            "- **shares or units of other companies** active in real-estate investment or providing services to the "
            "Company's (or its group's) property, excluding personal (partnership-type) companies.\n\n"
            "Commitments made in prospectuses about the use of funds raised on a regulated market also fall within "
            "this scope. The Company's investment activity covers both new investments and divestments."
        ),
    },
    {
        "id": "focus", "section": "§3.1", "title": "Investment focus areas",
        "strong": [r"focus|asset types?|property types?|asset class(es)?|sectors?|what (kind|type|sort)s? of (assets|properties|buildings)|"
                   r"ποι(ο|α) κατηγορ"],
        "medium": [r"strategy|target"],
        "weak": [r"invest"],
        "text": (
            "**Investment focus areas**\n\n"
            "The Company focuses its investments – without excluding other opportunities – on:\n"
            "- **Retail:** shopping centres with strong growth prospects thanks to their location;\n"
            "- **Offices:** modern, bioclimatically designed office buildings (non-retail);\n"
            "- **Logistics:** modern warehouse buildings;\n"
            "- **Land:** urban or non-urban plots with development prospects owing to their particular "
            "characteristics and location;\n"
            "- **Mixed-use:** modern residential-and-office buildings with growth prospects due to their location.\n\n"
            "_Note (not part of the policy text): hotels/hospitality are not named in this list, although the policy "
            "states that the list does not exclude other opportunities._"
        ),
    },
    {
        "id": "limits", "section": "§3.1.1 (Art. 46, Law 5193/2025)", "title": "Quantitative limits",
        "strong": [r"capex|capital expenditure|usufruct|bare ownership|concentration|1/3|one.third|κεφαλαιουχικ|επικαρπ|ψιλ"],
        "medium": [r"limits?|\bcaps?\b|threshold|ceiling|at least|70\s?%|40\s?%|20\s?%|single (property|asset|building)|"
                   r"per (property|asset|building)|exposure|restrictions?|constraints?|ποσοστ|όρια"],
        "weak": [r"invest"],
        "text": (
            "**Key quantitative limits**\n\n"
            "The policy summarises the main terms of Article 46 of Law 5193/2025 (see the table):"
        ),
        "table": (
            ["Limit", "Rule"],
            [
                ("Real estate share of total investments", "At least 70% of the Company's total investments"),
                ("Single property (at acquisition)", "Value no more than one third (1/3) of total investments"),
                ("Usufruct / bare-ownership properties (at acquisition)", "Combined value no more than 20% of total investments"),
                ("Development capex", "Total capex for developing real estate no more than 40% of the Company's real-estate investments"),
            ],
        ),
    },
    {
        "id": "valuation", "section": "§3.1.1", "title": "Valuation and acquisition safeguards",
        "strong": [r"independent (valuer|appraiser|valuation)|valuer|appraiser|valuation report|15\s?%|fifteen|premium|"
                   r"purchase price|sale price|εκτιμητ"],
        "medium": [r"valuation|pre.?agreements?|preliminary agreement|down.?payment|advance payment|50\s?%|notar|binding|προσύμφων"],
        "weak": [r"acqui|buy|purchase|sell|sale"],
        "text": (
            "**Valuation and acquisition safeguards**\n\n"
            "- Any real-estate transaction requires a prior valuation by an **independent valuer** appointed by the "
            "Ordinary General Meeting. The valuer issues a report before the Company signs the first binding "
            "agreement and again whenever the price changes; the valuation is binding on the Company when it "
            "takes the investment decision.\n"
            "- The price the Company **pays** for an acquisition may be up to **15% above** the independently "
            "determined value.\n"
            "- The price the Company **receives** on a disposal may be up to **15% below** that value.\n"
            "- Notarial **preliminary agreements** must secure at least: (a) the transaction price; (b) the date for "
            "signing the final contract; (c) an advance payment of no more than **50%** of the total price (lump sum "
            "or instalments); and (d) real or contractual security from the seller."
        ),
    },
    {
        "id": "criteria", "section": "§4", "title": "Investment criteria",
        "strong": [r"criteri(a|on)|κριτήρι"],
        "medium": [r"technical|building age|permit|floor.area|comparable|sworn|assessed|assessment|financial criteria|screening"],
        "weak": [r"invest"],
        "text": (
            "**Investment criteria**\n\n"
            "When applying the policy, the Company assesses:\n"
            "- **Technical, qualitative and economic parameters:** building specifications (e.g. age, building "
            "coefficient / floor-area ratio, building permit), quality characteristics (e.g. type of construction), "
            "and economic parameters such as each property's objective (tax-assessed) and market value, recent "
            "comparable transactions in the same area, and sworn valuers' reports.\n"
            "- **Location and geographic focus of the portfolio:** each property's location; the Company focuses "
            "on Greece and, selectively, on foreign markets.\n"
            "- **Environmental and energy performance:** the Company pursues and carries out energy and "
            "environmental upgrades of existing buildings and their certification under internationally "
            "recognised standards.\n"
            "- **Financial criteria:** return on investments, their financing, and the Company's capital structure.\n\n"
            "Leasability and tenant characteristics are also examined (ask about the lease criteria)."
        ),
    },
    {
        "id": "location", "section": "§3.1 and §4", "title": "Geographic focus",
        "strong": [r"geograph|γεωγραφ"],
        "medium": [r"abroad|overseas|outside greece|foreign|international|third countr|eu member|eea|αλλοδαπ|"
                   r"bulgaria|romania|cyprus|balkans?|europe"],
        "weak": [r"invest"],
        "text": (
            "**Geographic focus**\n\n"
            "- **Criteria (§4):** the Company focuses geographically on Greek territory and, selectively, on "
            "foreign markets.\n"
            "- **Permitted scope (§3.1):** real estate in Greece, in another EU/EEA member state or in a third "
            "country, held directly or through subsidiaries / collective investment schemes."
        ),
    },
    {
        "id": "lease", "section": "§4", "title": "Lease and tenant criteria",
        "strong": [r"leases?\b|leasing|tenants?|solvency|μισθ"],
        "medium": [r"rent|leasab|inflation|long.term (contract|lease)|due diligence|management cost|occupancy"],
        "weak": [r"criteri"],
        "text": (
            "**Lease and tenant criteria**\n\n"
            "Leasability and tenant characteristics (prospective and existing, including contractual obligations "
            "from leases signed before a development is completed) are examined. Case by case, the Company looks at:\n"
            "- a **reasonable rent** based on market conditions that protects the Company from inflation;\n"
            "- **lease duration**, seeking long-term contracts;\n"
            "- **tenant solvency**, with due-diligence measures when assessing prospective tenants and periodic "
            "checks during the lease;\n"
            "- **minimising the cost** of managing lease contracts.\n\n"
            "The aim is active financial and environmental management of the portfolio through a high occupancy "
            "rate of leasable space, continuous optimisation of operating costs, and improved energy performance "
            "and environmental footprint of the investments for the benefit of local communities."
        ),
    },
    {
        "id": "esg", "section": "§2 and §4", "title": "ESG and sustainability",
        "strong": [r"esg|sustainab|environment|energy (performance|efficiency)|certif|leed|breeam|βιώσιμ|περιβαλλοντ|ενεργειακ"],
        "medium": [r"green|carbon|climate|social|governance"],
        "weak": [r"invest"],
        "text": (
            "**ESG and sustainability**\n\n"
            "- The Company integrates environmental, social and corporate-governance criteria at every stage of "
            "its investment activity, including acquisition, development and management of properties (§2).\n"
            "- The energy and environmental performance of properties is an investment criterion; the Company "
            "pursues and carries out energy and environmental upgrades of existing buildings and their "
            "certification under internationally recognised standards (§4).\n"
            "- The portfolio management aims to improve energy performance and the environmental footprint of "
            "the investments for the benefit of local communities (§4)."
        ),
    },
    {
        "id": "governance", "section": "§3.1–3.2 and §7", "title": "Who decides",
        "strong": [r"committee|who (decides|approves|approve)|board|\bceo\b|chief executive|decision.?making|responsible bod|επιτροπ|διοικητικ"],
        "medium": [r"approv|decide|recommend|responsib|authori[sz]|αρμόδι"],
        "weak": [r"invest"],
        "text": (
            "**Who decides**\n\n"
            "- **Investments:** the **Investment Committee** weighs the investment criteria and makes "
            "recommendations to the **Board of Directors** on investment decisions, taking into account whether "
            "the timing is appropriate.\n"
            "- **Divestments:** the Investment Committee evaluates an existing investment's contribution and "
            "potential, and recommends to the Board on liquidating it, considering timing and alternative "
            "exploitation scenarios.\n"
            "- **CEO:** within their remit to shape and implement the investment policy, the CEO submits "
            "portfolio-management proposals to the Investment Committee and carries out the resulting "
            "decisions.\n"
            "- **The policy itself** is approved and updated by the Board of Directors (§7)."
        ),
    },
    {
        "id": "divest", "section": "§3.2", "title": "Divestment / sale of investments",
        "strong": [r"divest|disinvest|dispos|αποεπένδ|ρευστοποί"],
        "medium": [r"sell|selling|sale|sold|exit|liquidat|πώλησ"],
        "weak": [r"invest"],
        "text": (
            "**Divestment / sale of investments**\n\n"
            "The Investment Committee evaluates the contribution of existing investments (and the possibility of "
            "exploiting them) and recommends to the Board on liquidating investments, considering the timing and "
            "alternative scenarios. The CEO submits portfolio-management proposals to the Investment Committee "
            "and carries out the resulting decisions.\n\n"
            "On pricing, the price received on a disposal may be up to 15% below the independent valuer's value (§3.1.1)."
        ),
    },
    {
        "id": "deviations", "section": "§5", "title": "Deviations from the policy",
        "strong": [r"deviat|exception|derogat|waiver|παρεκκλ|αποκλίσ"],
        "medium": [r"breach|non.?compliance|variance|outside the policy|exempt"],
        "weak": [r"invest"],
        "text": (
            "**Deviations from the policy**\n\n"
            "The policy makes **no provision for deviations**. All investment decisions and their implementation "
            "are reviewed by the competent corporate bodies, and if deviations are found they are re-examined to "
            "ensure sound management and compliance with the legal and regulatory framework. Any deviation from the "
            "policy, or variance in implementing investment decisions, is handled through the approval procedure "
            "in the Company's Operating Regulation, as in force, for the case concerned."
        ),
    },
    {
        "id": "conflict", "section": "§6", "title": "Conflicts of interest",
        "strong": [r"conflicts? of interest|related.part|connected person|article 48|άρθρο 48|σύγκρουσ|συνδεδεμέν"],
        "medium": [r"conflict|related|connected"],
        "weak": [r"invest"],
        "text": (
            "**Conflicts of interest**\n\n"
            "The Company has a Conflict of Interest Policy built into its Operating Regulation, and applying this "
            "investment policy falls within its scope. When examining cases under the policy, the Company also "
            "checks whether the conditions for transactions with related persons involving Company property are "
            "met (Article 48 of Law 5193/2025)."
        ),
    },
    {
        "id": "meta", "section": "§1 and §7", "title": "Legal basis, approval and review",
        "strong": [r"review|revis|amend|updated?|version|edition|published|website|legal basis|5193|4548|4706|statutory|"
                   r"approval date|approved (on|by)|when (was|is).*approved|effective|έκδοση|νόμ"],
        "medium": [r"law|legal|annual|annually|how often|valid"],
        "weak": [r"invest"],
        "text": (
            "**Legal basis, approval and review**\n\n"
            "- **Version 1** (first edition), approved by the Board of Directors on **29.07.2026**.\n"
            "- Prepared under Articles 42, 46, 52 and 54 of Law 5193/2025, Law 4548/2018 (companies) and "
            "Law 4706/2020 (corporate governance), as in force.\n"
            "- Approved and updated by the Board; after approval and every update it is posted on the "
            "Company's website.\n"
            "- Reviewed **annually**, when the five-year business plan is prepared, and extraordinarily when "
            "special circumstances call for it, so it reflects market conditions, strategy and regulatory developments."
        ),
    },
]

POLICY_SUMMARY = (
    "## Investment policy – summary\n\n"
    "_NOVAL PROPERTY REIC · Version 1 · approved by the Board on 29.07.2026 (Greek original, summarised in English)_\n\n"
    "- **Purpose:** long-term value for shareholders through a diversified, resilient, high-specification portfolio, "
    "diversified by use, location and tenant profile, with ESG built into every stage.\n"
    "- **Focus areas:** retail centres, modern bioclimatic offices, modern logistics buildings, urban/non-urban land "
    "plots, and modern mixed-use (residential + office) buildings – without excluding other opportunities.\n"
    "- **Permitted scope:** real estate in Greece, the EU/EEA or third countries (directly or via subsidiaries / "
    "collective schemes); self-consumption RES + battery plants; shares in real-estate companies.\n"
    "- **Key limits:** at least 70% of investments in real estate; one property ≤ 1/3 of total investments at "
    "acquisition; usufruct/bare-ownership ≤ 20%; development capex ≤ 40% of real-estate investments.\n"
    "- **Safeguards:** independent valuation before transactions; price within ±15% of that value; advance "
    "payments ≤ 50% in preliminary agreements.\n"
    "- **Governance:** Investment Committee recommends, Board decides on the policy; no deviations allowed; "
    "reviewed annually.\n\n"
    "Ask about any topic: criteria, limits, valuation, lease criteria, geographic focus, ESG, who decides, "
    "divestments, deviations, conflicts of interest, or legal basis and review."
)


def _policy_score(entry: dict, text: str) -> int:
    score = 0
    for weight, key in ((3, "strong"), (2, "medium"), (1, "weak")):
        score += weight * sum(1 for pat in entry.get(key, []) if re.search(pat, text))
    return score


def _policy_dataset_note(entry_id: str, portfolio: pd.DataFrame) -> str:
    """Link policy answers to the embedded dataset where it adds something factual."""
    if entry_id in ("location", "permitted") and "country" in portfolio:
        abroad = portfolio[portfolio["country"].notna() & (portfolio["country"] != "Greece")]
        if abroad.empty:
            return f"\n\nIn the loaded dataset, all {len(portfolio)} buildings are in Greece."
        items = ", ".join(f"{r['name']} ({r['city']}, {r['country']})" for _, r in abroad.iterrows())
        verb = "is" if len(abroad) == 1 else "are"
        return f"\n\nIn the loaded dataset, {len(abroad)} of {len(portfolio)} buildings {verb} outside Greece: {items}."
    if entry_id == "focus" and "type" in portfolio:
        counts = portfolio["type"].value_counts()
        return "\n\nBuildings in the loaded dataset by type: " + " · ".join(f"{k} {v}" for k, v in counts.items()) + "."
    return ""


def _policy_render(entry: dict, portfolio: pd.DataFrame) -> tuple[str, Optional[pd.DataFrame]]:
    text = entry["text"] + _policy_dataset_note(entry["id"], portfolio)
    table = None
    if entry.get("table"):
        headers, rows = entry["table"]
        table = pd.DataFrame(rows, columns=headers)
    return text, table


def policy_reply(text: str, portfolio: pd.DataFrame) -> Optional[Reply]:
    """Answer questions about the investment policy (in English). None = not a policy question."""
    has_policy_word = bool(re.search(r"polic|πολιτικ", text))
    if has_policy_word and re.search(POLICY_SUMMARY_PATTERN, text):
        return Reply(POLICY_SUMMARY)

    scored = sorted(((_policy_score(e, text), e) for e in POLICY_ENTRIES), key=lambda x: -x[0])
    best_score, best = scored[0]
    if best_score < (2 if has_policy_word else 3):
        return Reply(POLICY_SUMMARY) if has_policy_word else None

    parts = [best]
    if len(scored) > 1 and scored[1][0] >= best_score and scored[1][0] >= 3:
        parts.append(scored[1][1])          # a tie on a strong match: answer both topics

    body, table = [], None
    for entry in parts:
        txt, tbl = _policy_render(entry, portfolio)
        body.append(txt)
        table = tbl if tbl is not None else table
    sections = " and ".join(e["section"] for e in parts)
    answer = "\n\n".join(body) + f"\n\n_Source: {POLICY_LABEL}, {sections}. Original in Greek; answered in English._"

    related = [e["title"] for s, e in scored if e not in parts and s >= 2][:3]
    if related:
        answer += "\n\nRelated policy topics: " + ", ".join(related) + "."
    return Reply(answer, table=table)


def generate_reply(user_message: str, portfolio: pd.DataFrame) -> Reply:
    text = user_message.lower().strip()
    if not text:
        return Reply("Please enter a question about the Noval portfolio.")

    if portfolio.empty or "name" not in portfolio:
        return Reply("The dataset has no building names to work with.")

    filters = detect_filters(text, portfolio)
    scoped = apply_filters(portfolio, filters)
    scope = describe_filters(filters)

    # 1. Greetings / help
    if re.search(r"\b(hi|hello|hey|good morning|good afternoon)\b", text) or "help" in text \
            or "what can you do" in text:
        return Reply(
            "I can answer questions about the Noval Properties portfolio:\n\n"
            "- **List** properties – “Provide a list of properties of Noval Properties”\n"
            "- **Filter** by type, country, city, region or status – “Show offices in Athens”\n"
            "- **Rank** – “Rank the properties in decreasing area”, “Top 5 buildings by GLA”\n"
            "- **Superlatives** – “Which is the largest building?”, “Which country has the most buildings?”\n"
            "- **Aggregate** – “What is the total GLA?”, “How many buildings are under development?”\n"
            "- **Chart** – “Chart GLA by city”, “Breakdown by type”\n"
            "- **Detail** – name a building to see its full record\n"
            "- **Overview** – “Give me a portfolio overview”\n"
            "- **Financials** – “How did rental income change from 2024 to 2025?”, “What is the LTV?”, “Show the financial highlights”\n"
            "- **Investment policy** – “Summarise the investment policy”, “What are the investment criteria?”, "
            "“What are the capex limits?”, “Who approves investments?”"
        )

    # 1a. Financial-report questions (FY2024 / FY2025, answered in English)
    fin = finance_reply(text)
    if fin is not None:
        return fin

    # 1b. Investment-policy questions (answered in English from the embedded policy)
    policy = policy_reply(text, portfolio)
    if policy is not None:
        return policy

    # 2. Single-property detail
    named = portfolio[portfolio["name"].fillna("").str.lower().apply(lambda n: bool(n) and n in text)]
    if len(named) == 1:
        record = named.iloc[0].dropna()
        detail = pd.DataFrame(
            {"Field": [COLUMN_LABELS.get(k, k) for k in record.index], "Value": [str(v) for v in record.values]}
        )
        return Reply(f"Details for **{record['name']}**:", table=detail)

    # 2b. Rankings / superlatives ("rank by area", "which is the highest value?")
    ranked_reply = rank_reply(text, scoped, scope)
    if ranked_reply is not None:
        return ranked_reply

    # 3. Charts / breakdowns
    wants_chart = any(w in text for w in ["chart", "graph", "plot", "breakdown", "distribution", "split"]) \
        or re.search(r"\bby (type|category|country|city|region|status)\b", text)
    if wants_chart:
        dim = next(
            (d for d, words in DIMENSION_WORDS.items()
             if d in scoped and any(re.search(rf"\b{w}\b", text) for w in words)),
            next((d for d in ["type", "country", "city", "status", "region"] if d in scoped), None),
        )
        if dim:
            use_value = "value" in text and "value_eur" in scoped
            use_area = bool(re.search(r"area|sqm|gla", text)) and "area_sqm" in scoped
            if use_value:
                series, label = scoped.groupby(dim)["value_eur"].sum(), "Portfolio value (€)"
            elif use_area:
                series, label = scoped.groupby(dim)["area_sqm"].sum(), "GLA (sqm)"
            else:
                series, label = scoped.groupby(dim).size(), "Number of buildings"
            series = series.sort_values(ascending=False)
            return Reply(
                f"**{label} by {dim}**{scope}:",
                table=series.rename(label).reset_index().rename(columns={dim: COLUMN_LABELS.get(dim, dim)}),
                chart=series,
                chart_title=f"{label} by {dim}",
            )

    # 4. Aggregates
    asks_count = re.search(r"\b(how many|count|number of)\b", text)
    asks_total = re.search(r"\b(total|sum|average|avg|worth|occupancy|income|rent|value|area|sqm|gla)\b", text)
    if (asks_count or asks_total) and not re.search(r"\b(list|show|which|provide)\b", text):
        if scoped.empty:
            return Reply(f"No buildings match that filter{scope}.")
        m = portfolio_metrics(scoped)
        wants_value = bool(re.search(r"value|worth|valuation", text))
        return Reply(f"Portfolio metrics{scope}:\n\n{metrics_text(m, company_note=wants_value and not filters)}")

    # 5. Overview
    if re.search(r"\b(overview|summary|summarise|summarize|snapshot|portfolio)\b", text) \
            and not re.search(r"\b(list|show|provide)\b", text):
        m = portfolio_metrics(scoped)
        reply = Reply(f"## Portfolio overview{scope}\n\n{metrics_text(m)}")
        if "type" in scoped and not scoped.empty:
            reply.chart = scoped.groupby("type").size().sort_values(ascending=False)
            reply.chart_title = "Properties by type"
        return reply

    # 6. Listing (explicit, or any filter was named)
    if re.search(r"\b(list|show|provide|give|display|which|what|all|propert\w*|assets?|buildings?)\b", text) or filters:
        if scoped.empty:
            return Reply(f"No buildings match that filter{scope}.")
        return Reply(
            (f"Here is the **1 building** " if len(scoped) == 1 else f"Here are the **{len(scoped)} buildings** ")
            + f"in the Noval Properties portfolio{scope}:",
            table=list_table(scoped),
        )

    return Reply(
        "I wasn't sure what you meant. Try “Provide a list of properties”, "
        "“Show retail properties in Athens”, or “Chart GLA by type”."
    )


# ------------------------------
# Rendering helpers
# ------------------------------
def render_table(df: pd.DataFrame) -> None:
    config = {}
    for col in df.columns:
        label = COLUMN_LABELS.get(col, col)
        if col in ("value_eur", "annual_income_eur", "value_per_sqm"):
            config[col] = st.column_config.NumberColumn(label, format="€%d")
        elif col == "yield_pct":
            config[col] = st.column_config.NumberColumn(label, format="%.1f%%")
        elif col in ("rank", "year_built"):
            config[col] = st.column_config.NumberColumn(label, format="%d")
        elif col == "area_sqm":
            config[col] = st.column_config.NumberColumn(label, format="%d")
        elif col == "occupancy_pct":
            config[col] = st.column_config.ProgressColumn(label, min_value=0, max_value=100, format="%d%%")
        else:
            config[col] = st.column_config.Column(label)
    st.dataframe(df, hide_index=True, use_container_width=True, column_config=config)


def render_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("chart") is not None:
            if message.get("chart_title"):
                st.caption(message["chart_title"])
            st.bar_chart(message["chart"], color="#2251FF")
        if message.get("table") is not None:
            render_table(message["table"])


# ------------------------------
# Session state
# ------------------------------
WELCOME = (
    "Welcome to the **Noval Properties Advisor**.\n\n"
    "Ask about the portfolio, for example: “Provide a list of properties of Noval Properties”, "
    "or about the investment policy, for example: “What are the investment criteria?”. Answers are in English."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# ------------------------------
# Sidebar
# ------------------------------
with st.sidebar:
    st.markdown("### Noval Properties Advisor")
    st.caption("Portfolio Q&A for the Viohalco digital transformation office.")

    st.markdown("#### Conversation")
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Conversation cleared. What would you like to know about the portfolio?"}
        ]
        st.rerun()

    st.markdown("#### Suggested prompts")
    for suggestion in [
        "Provide a list of properties of Noval Properties",
        "Give me a portfolio overview",
        "Rank the properties in decreasing area",
        "Compare 2025 vs 2024 financial reports",
        "Show offices in Marousi",
        "Chart GLA by type",
        "Show the financial highlights",
        "How did rental income change from 2024 to 2025?",
        "Summarise the investment policy",
        "What limits does the policy set on capex and single assets?",
    ]:
        if st.button(suggestion, use_container_width=True):
            st.session_state.pending_prompt = suggestion
            st.rerun()

# Embedded dataset
portfolio = load_portfolio()

with st.sidebar:
    st.caption(f"Data: {len(portfolio)} Noval buildings (embedded dataset).")
    st.caption(f"Policy: {POLICY_LABEL}. Greek original, English answers.")
    st.caption(f"Financials: {FIN_LABEL}.")

# ------------------------------
# Brand bar and hero
# ------------------------------
st.markdown(
    """
    <div class="brand-bar">
      <div class="brand-name">Noval Properties Advisor</div>
      <div class="brand-tag">Viohalco · Real estate intelligence</div>
    </div>
    <div class="hero">
      <div class="hero-eyebrow">Portfolio intelligence</div>
      <div class="hero-title">Ask anything about the Noval Properties portfolio.</div>
      <div class="hero-subtitle">
        List buildings, filter by type or location, get totals and charts, and ask about the financial reports and the Board-approved investment policy.
      </div>
      <div class="hero-rule"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# KPI cards (computed from the data)
# ------------------------------
metrics = portfolio_metrics(portfolio)
n_dev = int(portfolio["status"].str.contains("development", case=False, na=False).sum())
cards = [
    ("Buildings", f"{metrics['count']}", "In the dataset"),
    ("Total GLA", f"{metrics['area']:,.0f} sqm" if "area" in metrics else "n/a", "Gross leasable area"),
    ("Locations", f"{portfolio['city'].nunique()} cities", f"{portfolio['country'].nunique()} countries"),
    ("Under development", f"{n_dev}", "Buildings in the pipeline"),
]
for col, (label, value, note) in zip(st.columns(4), cards):
    with col:
        st.markdown(
            f"""
            <div class="card">
              <div class="card-label">{label}</div>
              <div class="card-value">{value}</div>
              <div class="card-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

# ------------------------------
# Chat interface
# ------------------------------
st.markdown(
    """
    <div class="section-title">Portfolio conversation</div>
    <div class="section-subtitle">Ask for lists, totals, rankings, details of a building, the financial results, or what the investment policy says.</div>
    """,
    unsafe_allow_html=True,
)

# Answers are rendered directly in the page (no scrolling box); the page itself grows.
for message in st.session_state.messages:
    render_message(message)

if st.session_state.pop("scroll_to_end", False):
    # After a new answer, scroll the page down so the latest reply is in view.
    components.html(
        """
        <script>
          const doc = window.parent.document;
          const main = doc.querySelector('section.main') || doc.querySelector('[data-testid="stMain"]')
                       || doc.querySelector('[data-testid="stAppViewContainer"]');
          if (main) { setTimeout(() => main.scrollTo({top: main.scrollHeight, behavior: 'smooth'}), 150); }
        </script>
        """,
        height=0,
    )

pending_prompt = st.session_state.pending_prompt
st.session_state.pending_prompt = None

user_prompt = st.chat_input("Ask about the Noval portfolio…", key="portfolio_chat_input")
if pending_prompt:
    user_prompt = pending_prompt

if user_prompt:
    st.session_state.scroll_to_end = True
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    reply = generate_reply(user_prompt, portfolio)
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply.text,
            "table": reply.table,
            "chart": reply.chart,
            "chart_title": reply.chart_title,
        }
    )
    st.rerun()
