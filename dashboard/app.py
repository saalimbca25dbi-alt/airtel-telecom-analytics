from __future__ import annotations

import base64
import json
import os
import sqlite3
import tempfile
import zipfile
from datetime import date, datetime
from html import escape
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# ============================================================
# AIRTEL TELECOM ANALYTICS | GROUP 2 | DOMAIN B - REVENUE
# File: project_root/dashboard/app.py
# Run:  streamlit run dashboard/app.py
# Data: project_root/data/airtel_dashboard_slim.db (fallback: data/raw/airtel.db)
# NOTE: all SQL / data logic is unchanged. Only the look, the chart
#       types and the animations were redesigned.
# ============================================================

st.set_page_config(
    page_title="Airtel Telecom Analytics | Revenue",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
# Prefer the slim dashboard DB in data/; fall back to raw/airtel.db when needed.
DB_CANDIDATES = [
    DATA_DIR / "airtel_dashboard_slim.db",
    DATA_DIR / "raw" / "airtel.db",
    DATA_DIR / "airtel.db",
]
RED, DARK_RED, PINK = "#E0002B", "#97001E", "#F5A3B1"
NAVY, INDIGO, TEAL, AMBER = "#2B2F5E", "#3D5AFE", "#00A878", "#FFB400"
INK, GRID = "#20242B", "#ECEDF1"
PALETTE = [RED, INDIGO, "#FF9F1C", TEAL, "#8E24AA"]

_AIRTEL_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <path fill="#E40000" fill-rule="evenodd" d="M35.5 7C21.2 7 9.5 16.5 9.5 29.8c0 9.6 5.9 18.2 15.6 22.8 1.6.8 3.3-.6 2.8-2.3-1.4-4.8-.6-9.8 2.4-13.5 3.6-4.5 9.8-6.4 15.1-4.3 4.3 1.7 6.8 5.8 5.6 10.1-.8 2.8-2.8 5.2-5.7 6.5-2.1 1-1.3 4.2 1 4.1 6.7-.3 12.2-6.5 12.2-15.4C58.5 19.7 48.8 7 35.5 7zm2.2 18.5c-5.4 0-10 3.7-11.1 8.8-.3 1.4 1 2.6 2.3 2 3.1-1.5 6.8-1.5 9.7-.1 2.7 1.3 4.2 3.9 3.6 6.6-.4 1.8 1.4 3.2 3 2.3 3.7-2 5.9-5.8 5.9-10 0-5.4-5.9-9.6-13.4-9.6z"/>
</svg>
""".strip()
AIRTEL_LOGO_URI = "data:image/svg+xml;base64," + base64.b64encode(_AIRTEL_SVG.encode("utf-8")).decode("ascii")

# --------------------------- THEME ---------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ---------- base + subtle animated background colour ---------- */
    :root {color-scheme: light; --chart-h: clamp(220px, calc((100vh - 360px) / 2), 330px);}
    html, body, [class*="css"] {font-family:Inter,Arial,sans-serif;}
    .stApp {
        isolation:isolate;
        background:linear-gradient(135deg,#F6F2F6 0%,#F0F3FA 48%,#F7F2F4 100%);
        color:#20242B;
    }
    .stApp::before {
        content:"";position:fixed;inset:-15%;z-index:-1;pointer-events:none;
        background:
          radial-gradient(560px 440px at 10% 15%, rgba(224,0,43,.14), transparent 62%),
          radial-gradient(600px 480px at 90% 14%, rgba(61,90,254,.14), transparent 62%),
          radial-gradient(620px 480px at 80% 90%, rgba(255,159,28,.12), transparent 62%),
          radial-gradient(540px 440px at 12% 88%, rgba(0,168,120,.11), transparent 62%);
        animation:auroraDrift 18s ease-in-out infinite alternate;
    }
    .stApp::after {
        content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
        background:
          linear-gradient(120deg, rgba(224,0,43,.04) 0%, rgba(61,90,254,.05) 50%, rgba(0,168,120,.04) 100%);
        background-size:200% 200%;
        animation:bgShift 14s ease-in-out infinite alternate;
    }
    [data-testid="stHeader"] {background:transparent!important;height:0!important;min-height:0!important;overflow:visible!important;}
    [data-testid="stToolbar"], [data-testid="stDecoration"], .stAppDeployButton {display:none!important;}
    #MainMenu, footer {visibility:hidden;}
    .block-container {padding:0.35rem 0.9rem 0.25rem!important;max-width:100%!important;}
    /* Streamlit 1.67 puts margin-bottom:-1rem on stMarkdownContainer; reset it so custom HTML blocks never overlap */
    [data-testid="stMarkdownContainer"] {margin-bottom:0!important;}
    [data-testid="stMarkdownContainer"] > p:last-child {margin-bottom:0!important;}
    [data-testid="stMain"] [data-testid="stVerticalBlock"] {gap:0.28rem!important;}
    [class*="st-key-card_"] [data-testid="stVerticalBlock"] {gap:0.22rem!important;}
    iframe[height="0"] {display:none;}
    /* keep everything fully visible while Streamlit is re-running (no grey "faded" look) */
    [data-stale="true"], .stale-element {opacity:1!important;transition:none!important;}

    /* ---------- mouse glow that follows the cursor ---------- */
    #airtel-orb {
        position:fixed;left:-400px;top:-400px;width:380px;height:380px;border-radius:50%;pointer-events:none;
        background:radial-gradient(circle,rgba(224,0,43,.15),rgba(61,90,254,.05) 45%,transparent 68%);
        transform:translate(-50%,-50%);z-index:999;mix-blend-mode:multiply;
        transition:left .14s ease-out,top .14s ease-out;
    }

    /* ---------- sidebar ---------- */
    [data-testid="stSidebar"] {
        background:
          radial-gradient(460px 340px at 50% 122%, #E0002B 0%, transparent 70%),
          linear-gradient(180deg,#272B37,#12151C);
        border-right:1px solid #3B404B;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {padding-top:0.75rem!important;padding-bottom:0.5rem!important;}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:0.42rem!important;}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label p, [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] [data-testid="stButton"] button,
    [data-testid="stSidebar"] [data-testid="stButton"] button * {color:#fff!important;}
    [data-testid="stSidebar"] h2 {font-size:15px;font-weight:800;margin:2px 0 0;}
    [data-testid="stSidebar"] label p {font-size:11.5px;font-weight:700;opacity:1;}
    /* filter boxes: solid white with crisp black text (compatible with Streamlit 1.67+ and older BaseWeb) */
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div:has(> input),
    [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"],
    [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="base-input"],
    [data-testid="stSidebar"] [data-testid="stDateInputField"] {
        background:#FFFFFF!important;border:1px solid #000000!important;border-radius:9px!important;
        min-height:34px!important;height:34px!important;transition:all .2s ease;opacity:1!important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] input,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div:has(> input),
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div:has(> input) *,
    [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"] *,
    [data-testid="stSidebar"] [data-testid="stDateInput"] input,
    [data-testid="stSidebar"] [data-testid="stDateInputField"],
    [data-testid="stSidebar"] [data-testid="stDateInputField"] *,
    [data-testid="stSidebar"] [data-testid="stDateInputField"] [role="spinbutton"] {
        color:#111827!important;-webkit-text-fill-color:#111827!important;font-weight:700!important;opacity:1!important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] svg,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] button svg,
    [data-testid="stSidebar"] [data-testid="stDateInput"] svg,
    [data-testid="stSidebar"] [data-testid="stDateInputField"] svg {fill:#C8102E!important;color:#C8102E!important;}
    [data-testid="stSidebar"] [data-baseweb="select"] > div:hover,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div:has(> input):hover,
    [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"]:hover,
    [data-testid="stSidebar"] [data-testid="stDateInputField"]:hover {
        box-shadow:0 0 0 3px rgba(255,76,106,.6);transform:translateY(-1px);
    }
    [data-testid="stSidebar"] hr {border-color:rgba(255,255,255,.16);margin:4px 0!important;}
    [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {opacity:.8;font-size:10.5px;line-height:1.25;}
    .side-brand {display:flex;align-items:center;gap:8px;font-size:28px;font-weight:800;letter-spacing:-1.2px;color:#FF3355!important;line-height:1;}
    .side-brand img {width:26px;height:26px;border-radius:7px;background:#fff;padding:2px;box-shadow:0 3px 8px rgba(0,0,0,.25);}
    .side-sub {font-size:8.5px;letter-spacing:1.8px;color:#fff!important;opacity:.85;margin-top:3px;}
    .sel-card {
        background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.22);border-radius:12px;
        padding:9px 12px;margin-top:2px;backdrop-filter:blur(4px);transition:all .25s ease;color:#fff!important;
    }
    .sel-card:hover {background:rgba(255,255,255,.18);transform:translateY(-2px);box-shadow:0 10px 20px rgba(0,0,0,.30);}
    .sel-head {font-size:10px;font-weight:700;letter-spacing:.5px;color:#fff!important;opacity:.85;}
    .sel-text {font-size:13px;font-weight:800;color:#FF8CA0!important;margin:3px 0 5px;line-height:1.2;}
    .sel-num {font-size:21px;font-weight:800;color:#fff!important;line-height:1;}
    .sel-lbl {font-size:10px;color:#fff!important;opacity:.85;margin-top:2px;}

    /* dropdown menus (they open in a portal, outside the sidebar) */
    [data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="popover"] div[role="listbox"],
    [data-testid="stSelectboxVirtualDropdown"], [data-testid="stSelectboxVirtualDropdown"] [role="listbox"] {
        background:#fff!important;color:#20242B!important;
    }
    [data-baseweb="popover"] li:hover,
    [data-testid="stSelectboxVirtualDropdown"] [role="option"][data-hovered] {background:#FDE6EA!important;}
    [data-baseweb="popover"] *, [data-testid="stSelectboxVirtualDropdown"] * {color:#20242B!important;}

    /* ---------- banner ---------- */
    .airtel-banner {
        position:relative;display:flex;align-items:center;justify-content:space-between;gap:12px;
        background:linear-gradient(105deg,#7A0018 0%,#D2002A 50%,#FF3D5A 100%);background-size:180% 100%;
        color:#fff;border-radius:13px;padding:7px 18px;
        box-shadow:0 6px 16px rgba(160,0,30,.24);margin-bottom:0;overflow:hidden;
        animation:bannerFlow 9s ease-in-out infinite alternate;
    }
    .airtel-banner::before {
        content:"";position:absolute;top:0;left:-60%;width:40%;height:100%;
        background:linear-gradient(100deg,transparent,rgba(255,255,255,.26),transparent);
        transform:skewX(-20deg);animation:shine 6s ease-in-out infinite;
    }
    .airtel-banner::after {
        content:"";position:absolute;right:-70px;top:-90px;width:240px;height:240px;border-radius:50%;
        background:radial-gradient(circle,rgba(255,255,255,.22),transparent 68%);
    }
    .brand-left {display:flex;align-items:center;gap:12px;position:relative;z-index:1;}
    .brand-logo {
        display:flex;align-items:center;gap:7px;background:#FFFFFF;color:#E0002B;
        border-radius:10px;padding:4px 11px 4px 7px;font-size:20px;font-weight:800;letter-spacing:-0.8px;line-height:1;
        box-shadow:0 4px 12px rgba(0,0,0,.18);
    }
    .brand-logo img {width:24px;height:24px;display:block;}
    .airtel-title {font-size:17px;font-weight:800;line-height:1.1;}
    .airtel-sub {font-size:10.5px;font-weight:500;opacity:.93;margin-top:1px;}
    .banner-right {display:flex;gap:8px;align-items:center;position:relative;z-index:1;flex-wrap:wrap;justify-content:flex-end;}
    .chip {background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.4);border-radius:999px;
           padding:4px 11px;font-size:11px;font-weight:650;backdrop-filter:blur(4px);transition:all .25s ease;cursor:default;}
    .chip:hover {background:rgba(255,255,255,.34);transform:translateY(-2px) scale(1.03);}
    .live-dot {display:inline-block;width:7px;height:7px;border-radius:50%;background:#5CFF9D;margin-right:6px;
               box-shadow:0 0 0 0 rgba(92,255,157,.7);animation:pulse 1.8s infinite;}
    .reader {color:#5E6671;font-size:10.5px;margin:1px 0 2px 3px;line-height:1.2;}

    /* ---------- section labels ---------- */
    .section-label {color:#B60027;font-size:14px;font-weight:800;margin:0 0 2px;display:flex;align-items:center;gap:7px;line-height:1.2;}
    .section-label::before {content:"";width:5px;height:16px;border-radius:3px;background:linear-gradient(180deg,#FF4C6A,#B60027);}
    .detail-sub {color:#5E6671;font-size:10.5px;margin:0 0 2px 12px;line-height:1.2;}

    /* ---------- KPI cards (accent colour set per card) ---------- */
    .kpi-card {
        --acc:#E0002B;--acc-soft:#FFE3E8;--mx:50%;--my:50%;
        position:relative;background:rgba(255,255,255,.92);backdrop-filter:blur(10px);border:1px solid rgba(230,231,236,.95);border-radius:12px;
        padding:6px 12px 6px 52px;min-height:54px;overflow:hidden;
        box-shadow:0 3px 10px rgba(30,30,50,.06);
        transition:transform .18s ease-out,box-shadow .28s ease,border-color .28s ease;
        animation:fadeIn .55s ease-out both;will-change:transform;
    }
    .kpi-card::before {content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--acc);}
    .kpi-card::after {
        content:"";position:absolute;inset:0;pointer-events:none;opacity:0;transition:opacity .3s ease;
        background:radial-gradient(220px circle at var(--mx) var(--my),var(--acc-soft),transparent 65%);
    }
    .kpi-card:hover {box-shadow:0 12px 24px rgba(30,30,60,.16);border-color:var(--acc);}
    .kpi-card:hover::after {opacity:1;}
    .kpi-icon {
        position:absolute;left:11px;top:50%;transform:translateY(-50%);width:33px;height:33px;border-radius:9px;
        display:flex;align-items:center;justify-content:center;font-size:16px;z-index:1;
        background:var(--acc-soft);transition:transform .35s ease;
    }
    .kpi-card:hover .kpi-icon {transform:translateY(-50%) rotate(-10deg) scale(1.12);}
    .kpi-label {color:#626A75;font-size:9.5px;font-weight:700;letter-spacing:.3px;position:relative;z-index:1;line-height:1.1;}
    .kpi-value {color:var(--acc);font-size:19px;font-weight:800;margin-top:1px;line-height:1.1;position:relative;z-index:1;}
    .kpi-value.muted {color:#20242B;}
    .kpi-note {color:#7B828C;font-size:9.5px;margin-top:1px;line-height:1.2;position:relative;z-index:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}

    /* ---------- chart cards (each chart + its filters live in one card) ---------- */
    [class*="st-key-card_"] {
        --mx:50%;--my:-30%;
        position:relative;background:rgba(255,255,255,.92);backdrop-filter:blur(10px);border:1px solid rgba(230,231,236,.95);border-top:3px solid #E0002B;border-radius:12px;
        padding:6px 10px 4px;overflow:hidden;
        box-shadow:0 3px 10px rgba(30,30,50,.06);
        transition:transform .25s cubic-bezier(.2,.8,.2,1),box-shadow .25s ease,border-color .25s ease;
    }
    [class*="st-key-card_"]::before {
        content:"";position:absolute;inset:0;pointer-events:none;opacity:0;transition:opacity .3s ease;
        background:radial-gradient(300px circle at var(--mx) var(--my),rgba(224,0,43,.10),transparent 65%);
    }
    [class*="st-key-card_"]:hover {transform:translateY(-2px);box-shadow:0 12px 24px rgba(200,16,46,.15);border-top-color:#3D5AFE;}
    [class*="st-key-card_"]:hover::before {opacity:1;}
    .chart-title {
        background:linear-gradient(90deg,#B00024,#E0002B 70%,#FF4C6A);color:#fff;border-radius:8px;
        padding:4px 10px;font-size:11.5px;font-weight:750;margin:0 0 2px;
        display:flex;align-items:center;gap:7px;box-shadow:0 3px 8px rgba(200,16,46,.18);line-height:1.2;
    }
    .chart-note {font-size:9px;color:#5E6671;margin:0 0 0 2px;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
    div[data-testid="stPlotlyChart"],
    div[data-testid="stPlotlyChart"] > div,
    div[data-testid="stPlotlyChart"] .js-plotly-plot,
    div[data-testid="stPlotlyChart"] .plot-container,
    div[data-testid="stPlotlyChart"] .svg-container {
        width:100%!important;height:var(--chart-h)!important;min-height:220px!important;
    }
    div[data-testid="stPlotlyChart"] {
        background:transparent;border:none;padding:0;margin:0!important;overflow:hidden;
    }

    /* ---------- tabs as pills (Streamlit 1.67 React Aria + BaseWeb fallback) ---------- */
    [data-baseweb="tab-list"], [data-testid="stTabs"] [role="tablist"] {
        gap:8px!important;border-bottom:none!important;margin-bottom:4px!important;overflow:visible!important;padding:2px 0!important;
    }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"],
    [data-testid="stTabs"] [role="tablist"]::after,
    [data-testid="stTab"] .react-aria-SelectionIndicator {display:none!important;}
    button[data-baseweb="tab"], [data-testid="stTab"] {
        background:#fff!important;border:1px solid #E0E2E8!important;border-radius:9px!important;padding:5px 16px!important;
        box-shadow:0 2px 6px rgba(0,0,0,.05);transition:all .2s ease;height:auto!important;min-height:0!important;
    }
    button[data-baseweb="tab"] p, [data-testid="stTab"] p {font-size:12.5px!important;font-weight:750!important;color:#3A404A!important;line-height:1.2;margin:0!important;}
    button[data-baseweb="tab"]:hover, [data-testid="stTab"]:hover {transform:translateY(-1px);box-shadow:0 6px 12px rgba(200,16,46,.18);border-color:#F2A0AE!important;}
    button[data-baseweb="tab"][aria-selected="true"],
    [data-testid="stTab"][aria-selected="true"],
    [data-testid="stTab"][data-selected="true"] {
        background:linear-gradient(105deg,#B00024,#E0002B 70%,#FF4C6A)!important;border-color:#C8102E!important;
        box-shadow:0 6px 14px rgba(200,16,46,.30);
    }
    button[data-baseweb="tab"][aria-selected="true"] p,
    [data-testid="stTab"][aria-selected="true"] p,
    [data-testid="stTab"][data-selected="true"] p {color:#fff!important;}

    /* ---------- main-area widgets ---------- */
    [data-testid="stMain"] [data-testid="stSelectbox"] label {margin-bottom:1px!important;min-height:0!important;}
    [data-testid="stMain"] [data-testid="stSelectbox"] label p {font-size:9px;font-weight:700;color:#4F5661!important;line-height:1.1;}
    [data-testid="stMain"] [data-baseweb="select"] > div,
    [data-testid="stMain"] [data-testid="stSelectbox"] div:has(> input) {
        background:#F8F9FB!important;color:#20242B!important;border:1px solid #E0E2E8!important;border-radius:7px!important;
        min-height:25px!important;height:25px!important;transition:all .2s ease;
    }
    [data-testid="stMain"] [data-baseweb="select"] > div *,
    [data-testid="stMain"] [data-testid="stSelectbox"] input {color:#20242B!important;-webkit-text-fill-color:#20242B!important;font-size:11px!important;}
    [data-testid="stMain"] [data-baseweb="select"] svg,
    [data-testid="stMain"] [data-testid="stSelectbox"] button svg {fill:#C8102E!important;color:#C8102E!important;width:13px;height:13px;}
    [data-testid="stMain"] [data-baseweb="select"] > div:hover,
    [data-testid="stMain"] [data-testid="stSelectbox"] div:has(> input):hover {border-color:#E0002B!important;background:#fff!important;box-shadow:0 0 0 2px rgba(224,0,43,.14);}
    div[data-testid="stSelectbox"] {margin-bottom:0!important;}
    div[data-testid="stButton"] button {
        border:1px solid #FF3355;background:rgba(255,255,255,.08);font-weight:700;border-radius:9px;
        padding:0.25rem 0.6rem!important;min-height:32px!important;transition:all .25s ease;
    }
    div[data-testid="stButton"] button:hover {background:#E0002B;transform:translateY(-2px);box-shadow:0 8px 16px rgba(224,0,43,.45);}

    /* ---------- key takeaways + overall insight ---------- */
    .take-card {
        --mx:50%;--my:0%;position:relative;overflow:hidden;
        background:linear-gradient(180deg,#FFF1F3,#FFFFFF);border:1px solid #F4C3CC;border-top:3px solid #3D5AFE;border-radius:12px;
        padding:8px 11px;box-shadow:0 3px 10px rgba(30,30,50,.06);height:100%;
        transition:transform .25s ease,box-shadow .25s ease;animation:fadeIn .6s ease-out both;
    }
    .take-card::before {content:"";position:absolute;inset:0;pointer-events:none;opacity:0;transition:opacity .3s ease;
        background:radial-gradient(300px circle at var(--mx) var(--my),rgba(61,90,254,.10),transparent 65%);}
    .take-card:hover {transform:translateY(-2px);box-shadow:0 12px 24px rgba(61,90,254,.16);}
    .take-card:hover::before {opacity:1;}
    .take-title {font-size:12.5px;font-weight:800;color:#B60027;margin-bottom:4px;position:relative;}
    .take-item {position:relative;display:flex;gap:7px;font-size:11px;line-height:1.3;color:#2B3038;margin:4px 0;padding:4px 6px;border-radius:8px;transition:background .2s ease,transform .2s ease;}
    .take-item:hover {background:#FDE3E8;transform:translateX(3px);}
    .take-dot {flex:0 0 18px;height:18px;border-radius:50%;background:#E0002B;color:#fff;font-size:10px;font-weight:800;
               display:flex;align-items:center;justify-content:center;margin-top:1px;box-shadow:0 0 0 2px #FBD0D8;}
    .insight-bar {
        margin-top:2px;background:linear-gradient(100deg,#1D2029,#2B2F5E);color:#fff;border-radius:10px;padding:6px 14px;
        font-size:11.5px;line-height:1.35;box-shadow:0 6px 14px rgba(30,30,60,.22);transition:transform .25s ease,box-shadow .25s ease;
        animation:fadeIn .7s ease-out both;
    }
    .insight-bar:hover {transform:translateY(-2px);box-shadow:0 12px 22px rgba(30,30,60,.30);}
    .insight-bar b {color:#FF8CA0;}

    /* ---------- footer ---------- */
    .foot {border-top:1px solid #D9DBE2;padding-top:3px;margin-top:2px;color:#5E6671;font-size:9.5px;line-height:1.3;
           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}

    /* ---------- animations ---------- */
    @keyframes fadeIn {from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
    @keyframes shine {0%{left:-60%}55%,100%{left:140%}}
    @keyframes bannerFlow {from{background-position:0% 50%}to{background-position:100% 50%}}
    @keyframes auroraDrift {
        0%{transform:translate3d(-2%,-2%,0) scale(1)}
        50%{transform:translate3d(2%,2%,0) scale(1.07)}
        100%{transform:translate3d(-1%,2%,0) scale(1.03)}
    }
    @keyframes bgShift {
        0%{background-position:0% 50%}
        100%{background-position:100% 50%}
    }
    @keyframes pulse {0%{box-shadow:0 0 0 0 rgba(92,255,157,.7)}70%{box-shadow:0 0 0 9px rgba(92,255,157,0)}100%{box-shadow:0 0 0 0 rgba(92,255,157,0)}}
    @media (prefers-reduced-motion: reduce) {* {animation:none!important;transition:none!important;} #airtel-orb{display:none!important;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------- DATABASE CONNECTION ----------------------
REQUIRED_TABLES = {"customer_features"}
DB_LOAD_ERROR: str | None = None


def _is_complete_db(candidate: Path) -> bool:
    """Check that a file is a readable project database without modifying it."""
    if not candidate.is_file():
        return False
    try:
        uri = candidate.resolve().as_uri() + "?mode=ro"
        test = sqlite3.connect(uri, uri=True)
        try:
            names = {r[0] for r in test.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
        finally:
            test.close()
        return REQUIRED_TABLES.issubset(names)
    except (OSError, sqlite3.Error, ValueError):
        return False


@st.cache_resource(show_spinner="Loading the private Airtel database…")
def _download_private_db() -> Path | None:
    """Download the database from private Drive or S3 when no local copy exists."""
    global DB_LOAD_ERROR

    try:
        cfg = st.secrets["database"]
    except (KeyError, FileNotFoundError):
        DB_LOAD_ERROR = (
            "Streamlit Cloud Secrets are not configured. Add the private Google Drive "
            "settings shown below, then save and reboot the app."
        )
        return None

    # Keep the downloaded copy outside the app repository and replace it only
    # after a complete transfer, so a failed download cannot leave a partial DB.
    temporary: Path | None = None
    try:
        cache_dir = Path(tempfile.gettempdir()) / "airtel-telecom-analytics"
        cache_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            os.chmod(cache_dir, 0o700)
        except OSError:
            pass
        destination = cache_dir / "airtel.db"
        if _is_complete_db(destination):
            DB_LOAD_ERROR = None
            return destination

        temporary = cache_dir / "airtel.db.download"
        file_id = str(cfg.get("google_drive_file_id", "")).strip()
        service_account_json = str(cfg.get("google_service_account_json", "")).strip()
        if file_id:
            if not service_account_json:
                DB_LOAD_ERROR = (
                    "The Google Drive file ID is set, but the service-account credential "
                    "is missing from Streamlit Secrets."
                )
                return None
            from google.auth.transport.requests import AuthorizedSession
            from google.oauth2 import service_account

            account_info = json.loads(service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                account_info,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            archive_path = cache_dir / "airtel_database.zip.download"
            try:
                with AuthorizedSession(credentials) as session:
                    response = session.get(
                        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
                        stream=True,
                        timeout=(15, 180),
                    )
                    if response.status_code in (401, 403):
                        DB_LOAD_ERROR = (
                            "Google Drive denied access. Share the ZIP with the service-account "
                            "email as a Viewer, and confirm the Drive API is enabled."
                        )
                        return None
                    response.raise_for_status()
                    with archive_path.open("wb") as output:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                output.write(chunk)
                with zipfile.ZipFile(archive_path) as archive:
                    members = [info for info in archive.infolist() if Path(info.filename).name == "airtel.db"]
                    if len(members) != 1 or members[0].file_size > 1024 * 1024 * 1024:
                        DB_LOAD_ERROR = "The Drive ZIP must contain one Airtel database file smaller than 1 GB."
                        return None
                    with archive.open(members[0]) as source, temporary.open("wb") as output:
                        while chunk := source.read(1024 * 1024):
                            output.write(chunk)
            finally:
                archive_path.unlink(missing_ok=True)
        else:
            bucket, key = str(cfg.get("s3_bucket", "")).strip(), str(cfg.get("s3_key", "")).strip()
            region = str(cfg.get("aws_region", "ap-south-1")).strip()
            access_key = str(cfg.get("aws_access_key_id", "")).strip()
            secret_key = str(cfg.get("aws_secret_access_key", "")).strip()
            session_token = cfg.get("aws_session_token")
            if not all((bucket, key, region, access_key, secret_key)):
                DB_LOAD_ERROR = (
                    "Add either the private Google Drive settings or complete S3 settings "
                    "to Streamlit Secrets."
                )
                return None
            import boto3

            client = boto3.client(
                "s3",
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=str(session_token) if session_token else None,
            )
            client.download_file(bucket, key, str(temporary))
        if not _is_complete_db(temporary):
            temporary.unlink(missing_ok=True)
            DB_LOAD_ERROR = (
                "The downloaded file is not a valid Airtel analysis database. Check that "
                "the Drive ZIP contains airtel.db or that the S3 key points to the raw database."
            )
            return None
        os.replace(temporary, destination)
        try:
            os.chmod(destination, 0o600)
        except OSError:
            pass
        DB_LOAD_ERROR = None
        return destination
    except Exception as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        response = getattr(exc, "response", {})
        error_code = response.get("Error", {}).get("Code") if isinstance(response, dict) else None
        http_status = getattr(response, "status_code", None)
        if isinstance(exc, json.JSONDecodeError):
            DB_LOAD_ERROR = "The Google service-account JSON in Secrets is invalid. Paste the complete downloaded JSON file."
        elif http_status == 404:
            DB_LOAD_ERROR = "Google Drive could not find that file. Check the file ID in Secrets."
        elif error_code == "AccessDenied":
            DB_LOAD_ERROR = "AWS denied access. Allow this key to read the configured S3 object."
        elif error_code in {"NoSuchBucket", "NoSuchKey", "404"}:
            DB_LOAD_ERROR = "The configured S3 bucket or object key was not found. Check both values in Secrets."
        elif error_code in {"InvalidAccessKeyId", "SignatureDoesNotMatch", "ExpiredToken"}:
            DB_LOAD_ERROR = "The AWS credentials in Secrets are invalid or expired. Update them and reboot the app."
        else:
            DB_LOAD_ERROR = (
                "The private database could not be downloaded. Verify the source settings, "
                "read permission, and credentials; see Streamlit Cloud logs for details. "
                f"Error type: {type(exc).__name__}."
            )
        return None


def find_valid_db() -> Path | None:
    """Choose the database that actually contains both project analysis tables."""
    for candidate in DB_CANDIDATES:
        if _is_complete_db(candidate):
            return candidate
    private_db = _download_private_db()
    if private_db is not None:
        return private_db
    return None


DB_PATH = find_valid_db()
if DB_PATH is None:
    st.error(
        "The Airtel analysis database was not found. For local use, place it at "
        "data/airtel_dashboard_slim.db (or data/raw/airtel.db). In Streamlit Cloud, "
        "configure private Google Drive access credentials in app Secrets."
    )
    if DB_LOAD_ERROR:
        st.warning(DB_LOAD_ERROR)
    st.code(
        '[database]\n'
        'google_drive_file_id = "1EBviAsS6ebKOwJaMCoAWkzGN1CY5YBJN"\n'
        "google_service_account_json = '''PASTE_THE_COMPLETE_SERVICE_ACCOUNT_JSON_HERE'''"
    )
    st.stop()


@st.cache_resource
def get_connection(db_file: str):
    uri = Path(db_file).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True, check_same_thread=False)


con = get_connection(str(DB_PATH))


@st.cache_data(show_spinner=False, ttl=3600)
def _run_query(db_file: str, sql: str, params: tuple) -> pd.DataFrame:
    """Same SQL as before; results are cached so the dashboard re-draws instantly."""
    return pd.read_sql_query(sql, get_connection(db_file), params=params)


def q(sql: str, params=()) -> pd.DataFrame:
    """Execute dashboard aggregations in SQLite SQL."""
    return _run_query(str(DB_PATH), sql, tuple(params))


def money(value) -> str:
    if value is None or pd.isna(value):
        return "Not available"
    return f"₹{float(value):,.2f}"


# ---------------------- SMALL COLOUR / UI HELPERS ----------------------
ACCENTS = {
    "red": ("#E0002B", "#FFE3E8"),
    "indigo": ("#3D5AFE", "#E4E9FF"),
    "teal": ("#00A878", "#D9F6EC"),
    "amber": ("#F08A00", "#FFF0D6"),
}


def hex_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def rgba(h: str, a: float) -> str:
    r, g, b = hex_rgb(h)
    return f"rgba({r},{g},{b},{a})"


def tint(h: str, amt: float) -> str:
    r, g, b = hex_rgb(h)
    return "#%02X%02X%02X" % tuple(round(c + (255 - c) * amt) for c in (r, g, b))


def shade(i: int, n: int, c0=(151, 0, 30), c1=(240, 98, 124)) -> str:
    t = i / max(1, n - 1)
    return "rgb(%d,%d,%d)" % tuple(round(a + (b - a) * t) for a, b in zip(c0, c1))


def render_kpi(label: str, value: str, note: str, icon: str = "📊", muted: bool = False, accent: str = "red"):
    acc, soft = ACCENTS.get(accent, ACCENTS["red"])
    cls = "kpi-value muted" if muted else "kpi-value"
    st.markdown(
        f'<div class="kpi-card" style="--acc:{acc};--acc-soft:{soft}"><div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="{cls}">{value}</div><div class="kpi-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def card(key: str):
    """One white card per chart (title + filters + chart). Falls back to a plain container on old Streamlit."""
    try:
        return st.container(key=f"card_{key}")
    except TypeError:
        return st.container()


def render_chart_title(title: str, icon: str = "📈"):
    st.markdown(f'<div class="chart-title"><span>{icon}</span><span>{title}</span></div>', unsafe_allow_html=True)


def render_chart(fig, height: int = 240, margin: dict | None = None):
    existing_margin = fig.layout.margin.to_plotly_json() if fig.layout.margin else {}
    resolved_margin = margin or existing_margin or dict(l=24, r=12, t=16, b=24)
    fig.update_layout(
        template="plotly_white", autosize=True, height=None,
        margin=resolved_margin,
        paper_bgcolor="rgba(255,255,255,0)", plot_bgcolor="#FFFFFF",
        font=dict(family="Inter", size=10, color=INK),
        transition_duration=500,
        hoverlabel=dict(bgcolor="#fff", font_size=11, font_color=INK, bordercolor=RED),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=9.5, color=INK)),
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zerolinecolor="#B8BDC5", automargin=True,
                     tickfont=dict(color=INK, size=9), title_font=dict(color=INK, size=9.5))
    fig.update_yaxes(showgrid=False, zerolinecolor="#B8BDC5", automargin=True,
                     tickfont=dict(color=INK, size=9), title_font=dict(color=INK, size=9.5))
    try:
        st.plotly_chart(
            fig, width="stretch", height="stretch",
            config={"displayModeBar": False, "responsive": True},
        )
    except TypeError:
        fig.update_layout(height=height)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "responsive": True})


# ---------------------- VERIFY DATABASE SCHEMA ----------------------
DB_SOURCE_LABEL = DB_PATH.relative_to(ROOT).as_posix() if DB_PATH.is_relative_to(ROOT) else DB_PATH.name

tables = set(q(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
)["name"].tolist())
required_tables = {"customer_features"}
if not required_tables.issubset(tables):
    st.error("The selected database does not contain the Airtel analysis tables.")
    st.write("Tables found:", sorted(tables))
    st.stop()

feature_cols = set(q("PRAGMA table_info(customer_features)")["name"].tolist())
required_feature_cols = {
    "customer_id", "region", "plan_name", "connection_type",
    "actual_arpu_6m", "stated_arpu", "recharge_total_6m"
}
if not required_feature_cols.issubset(feature_cols):
    st.error("The database schema differs from the Airtel revenue-analysis schema.")
    st.write("customer_features columns:", sorted(feature_cols))
    st.stop()

required_recharge_cols = {"customer_id", "recharge_date", "amount_inr", "channel", "txn_type"}
recharge_cols = set(q("PRAGMA table_info(recharges)")["name"].tolist()) if "recharges" in tables else set()
HAS_RECHARGES = "recharges" in tables and required_recharge_cols.issubset(recharge_cols)

# ---------------------- OPTIONS AND DATE LIMITS ----------------------
def get_options(sql: str) -> List[str]:
    return ["All"] + q(sql)["value"].dropna().astype(str).tolist()


CONNECTIONS = get_options("SELECT DISTINCT connection_type AS value FROM customer_features WHERE connection_type IS NOT NULL ORDER BY value")
REGIONS = get_options("SELECT DISTINCT region AS value FROM customer_features WHERE region IS NOT NULL ORDER BY value")
PLANS = get_options("SELECT DISTINCT plan_name AS value FROM customer_features WHERE plan_name IS NOT NULL ORDER BY value")
CIRCLES = get_options("SELECT DISTINCT circle_name AS value FROM customer_features WHERE circle_name IS NOT NULL ORDER BY value")
DEVICES = get_options("SELECT DISTINCT device_type AS value FROM customer_features WHERE device_type IS NOT NULL ORDER BY value")
AGE_BANDS = get_options("SELECT DISTINCT age_band AS value FROM customer_features WHERE age_band IS NOT NULL ORDER BY value")
ACQ_CHANNELS = get_options("SELECT DISTINCT acquisition_channel AS value FROM customer_features WHERE acquisition_channel IS NOT NULL ORDER BY value")
RECHARGE_CHANNELS = (
    get_options("SELECT DISTINCT channel AS value FROM recharges WHERE channel IS NOT NULL ORDER BY value")
    if HAS_RECHARGES else ["All"]
)
TXN_TYPES = (
    get_options("SELECT DISTINCT txn_type AS value FROM recharges WHERE txn_type IS NOT NULL ORDER BY value")
    if HAS_RECHARGES else ["All"]
)
STATUS_OPTIONS = ["All", "Active only", "Churned only"]

if HAS_RECHARGES:
    limits = q("SELECT MIN(date(recharge_date)) AS mn, MAX(date(recharge_date)) AS mx FROM recharges").iloc[0]
    MIN_DATE = pd.to_datetime(limits["mn"]).date()
    MAX_DATE = pd.to_datetime(limits["mx"]).date()
else:
    MIN_DATE, MAX_DATE = date(2025, 1, 1), date(2025, 6, 30)
DEFAULT_START = max(MIN_DATE, date(2025, 1, 1))
DEFAULT_END = min(MAX_DATE, date(2025, 6, 30))
if DEFAULT_START > DEFAULT_END:
    DEFAULT_START, DEFAULT_END = MIN_DATE, MAX_DATE


def months_in_period(start: date, end: date) -> int:
    return max(1, (end.year - start.year) * 12 + end.month - start.month + 1)


def where_for(filters: Dict[str, str], alias: str = "cp") -> Tuple[str, List]:
    clauses, params = ["1=1"], []
    mapping = {
        "plan": "plan_name",
        "connection": "connection_type",
        "region": "region",
        "circle": "circle_name",
        "device": "device_type",
        "age": "age_band",
        "acq": "acquisition_channel",
    }
    for key, column in mapping.items():
        value = filters.get(key, "All")
        if value != "All":
            clauses.append(f"{alias}.{column} = ?")
            params.append(value)
    status = filters.get("status", "All")
    if status == "Active only":
        clauses.append(f"{alias}.is_churned = 0")
    elif status == "Churned only":
        clauses.append(f"{alias}.is_churned = 1")
    return " AND ".join(clauses), params


def customer_period_cte(start: date, end: date) -> str:
    if not HAS_RECHARGES:
        return """
        WITH customer_period AS (
            SELECT cf.*,
                   COALESCE(cf.recharge_total_6m, 0) AS received_revenue,
                   COALESCE(cf.recharge_count, 0) AS recharge_transactions,
                   COALESCE(cf.actual_arpu_6m, COALESCE(cf.recharge_total_6m, 0) * 1.0 / 6) AS actual_arpu_period
            FROM customer_features cf
        )
        """
    months = months_in_period(start, end)
    return f"""
    WITH revenue_by_customer AS (
        SELECT customer_id, SUM(amount_inr) AS received_revenue,
               COUNT(*) AS recharge_transactions
        FROM recharges
        WHERE date(recharge_date) >= date('{start.isoformat()}')
          AND date(recharge_date) <= date('{end.isoformat()}')
        GROUP BY customer_id
    ), customer_period AS (
        SELECT cf.*,
               COALESCE(r.received_revenue,0) AS received_revenue,
               COALESCE(r.recharge_transactions,0) AS recharge_transactions,
               COALESCE(r.received_revenue,0) * 1.0 / {months} AS actual_arpu_period
        FROM customer_features cf
        LEFT JOIN revenue_by_customer r ON r.customer_id = cf.customer_id
    )
    """


def customer_query(select_sql: str, filters: Dict[str, str], start: date, end: date, group_sql: str = "") -> pd.DataFrame:
    where_sql, params = where_for(filters, "cp")
    sql = customer_period_cte(start, end) + f" SELECT {select_sql} FROM customer_period cp WHERE {where_sql} {group_sql}"
    return q(sql, params)


def chart_filter_ui(
    key: str,
    dimensions: Tuple[str, ...],
    main_filters: Dict[str, str],
    extras: Dict[str, Tuple[str, List[str]]] | None = None,
) -> Dict[str, str]:
    """Each chart gets tailored independent filters; global dimensions support 'Use sidebar'."""
    labels = {
        "plan": "Plan",
        "connection": "Connection",
        "region": "Region",
        "circle": "Circle",
        "device": "Device",
        "age": "Age band",
        "acq": "Acquisition",
        "status": "Subscriber status",
        "channel": "Recharge channel",
        "txn_type": "Txn type",
    }
    values = {
        "plan": PLANS,
        "connection": CONNECTIONS,
        "region": REGIONS,
        "circle": CIRCLES,
        "device": DEVICES,
        "age": AGE_BANDS,
        "acq": ACQ_CHANNELS,
        "status": STATUS_OPTIONS,
        "channel": RECHARGE_CHANNELS,
        "txn_type": TXN_TYPES,
    }
    global_dims = {"plan", "connection", "region"}
    selected = dict(main_filters)
    extras = extras or {}
    total_cols = len(dimensions) + len(extras)
    widgets = st.columns(total_cols, gap="small")

    for widget, dimension in zip(widgets[:len(dimensions)], dimensions):
        with widget:
            if dimension in global_dims:
                choices = ["Use sidebar", "All"] + [v for v in values[dimension] if v != "All"]
                picked = st.selectbox(labels[dimension], choices, key=f"{key}_{dimension}")
                if picked == "All":
                    selected[dimension] = "All"
                elif picked != "Use sidebar":
                    selected[dimension] = picked
            else:
                picked = st.selectbox(labels[dimension], values[dimension], key=f"{key}_{dimension}")
                selected[dimension] = picked

    for widget, (extra_key, (extra_label, extra_choices)) in zip(widgets[len(dimensions):], extras.items()):
        with widget:
            selected[extra_key] = st.selectbox(extra_label, extra_choices, key=f"{key}_{extra_key}")

    return selected


def recharge_where(filters: Dict[str, str], start: date, end: date, alias: str = "cf") -> Tuple[str, List]:
    cf_sql, params = where_for(filters, alias)
    clauses = ["date(r.recharge_date) >= date(?)", "date(r.recharge_date) <= date(?)", cf_sql]
    full_params: List = [str(start), str(end)] + params
    if filters.get("channel", "All") != "All":
        clauses.append("r.channel = ?")
        full_params.append(filters["channel"])
    if filters.get("txn_type", "All") != "All":
        clauses.append("r.txn_type = ?")
        full_params.append(filters["txn_type"])
    return " AND ".join(clauses), full_params

# ---------------------- SIDEBAR (MAIN FILTERS) ----------------------
with st.sidebar:
    st.markdown(f'<div class="side-brand"><img src="{AIRTEL_LOGO_URI}" alt="Airtel logo"><span>airtel</span></div>'
                '<div class="side-sub">TELECOM ANALYTICS • GROUP 2</div>',
                unsafe_allow_html=True)
    st.markdown("## 🎛️ Main Filters")
    date_range = st.date_input(
        "📅 Date range", value=(DEFAULT_START, DEFAULT_END),
        min_value=MIN_DATE, max_value=MAX_DATE, key="main_date_range"
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        MAIN_START, MAIN_END = date_range
    else:
        MAIN_START, MAIN_END = DEFAULT_START, DEFAULT_END
    main_plan = st.selectbox("📦 Plan", PLANS, key="main_plan")
    main_connection = st.selectbox("📶 Connection type", CONNECTIONS, key="main_connection")
    main_region = st.selectbox("📍 Region / circle", REGIONS, key="main_region")
    st.markdown("---")
    if st.button("↻ Reset filters", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith(("main_", "ov_", "detail_", "dt_")):
                del st.session_state[key]
        st.rerun()

    # Current selection summary (real subscriber count for the chosen filters)
    _sel_where, _sel_params = where_for({"plan": main_plan, "connection": main_connection, "region": main_region}, "cf")
    _sel_count = int(q(f"SELECT COUNT(*) AS n FROM customer_features cf WHERE {_sel_where}", _sel_params).iloc[0]["n"])
    _sel_text = " • ".join(v for v in (main_plan, main_connection, main_region) if v != "All") or "All plans • All connections • All regions"
    st.markdown(
        f'<div class="sel-card"><div class="sel-head">ⓘ CURRENT SELECTION</div>'
        f'<div class="sel-text">{escape(_sel_text)}</div>'
        f'<div class="sel-num">{_sel_count:,}</div><div class="sel-lbl">Subscribers in selection</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption(f"Source: {DB_SOURCE_LABEL}")
    st.caption("Customer analysis table: 22,000 subscribers")

MAIN_FILTERS = {"plan": main_plan, "connection": main_connection, "region": main_region}

# ---------------------- HEADER ----------------------
st.markdown(
    '<div class="airtel-banner">'
    f'<div class="brand-left"><div class="brand-logo"><img src="{AIRTEL_LOGO_URI}" alt="Airtel logo"><span>airtel</span></div>'
    '<div><div class="airtel-title">Airtel Telecom Analytics</div>'
    '<div class="airtel-sub">Revenue Performance Dashboard &nbsp;|&nbsp; Group 2 &nbsp;|&nbsp; Domain B</div></div></div>'
    '<div class="banner-right">'
    f'<div class="chip">📅 {MAIN_START:%d %b %Y} – {MAIN_END:%d %b %Y}</div>'
    f'<div class="chip"><span class="live-dot"></span>Last updated: {datetime.now():%d %b %Y, %H:%M}</div>'
    '</div></div>'
    '<div class="reader">Revenue performance, subscriber contribution and plan-level analysis.</div>',
    unsafe_allow_html=True,
)

# ---------------------- TWO DASHBOARD PAGES ----------------------
page_overview, page_detail = st.tabs(["▥  Revenue Overview", "⌖  Revenue Detail"])

# ============================================================
# PAGE 1 — REVENUE OVERVIEW
# ============================================================
with page_overview:
    st.markdown('<div class="section-label">Revenue Overview</div>', unsafe_allow_html=True)

    # The project fixed KPI: received recharge amount from Jan–Jun 2025; independent of filters.
    if HAS_RECHARGES:
        fixed_total = q("""
            SELECT SUM(amount_inr) AS total
            FROM recharges
            WHERE date(recharge_date) >= '2025-01-01'
              AND date(recharge_date) < '2025-07-01'
        """).iloc[0]["total"]
    else:
        fixed_total = q("SELECT SUM(recharge_total_6m) AS total FROM customer_features").iloc[0]["total"]

    # Statistical validation notebook supplied in the project has no completed T5 output.
    # Keep this honest rather than displaying an invented p-value.
    t5_display = "Not validated"
    t5_note = "Add the approved T5 result and one-tailed p-value after statistical validation"

    arpu_result = customer_query(
        "AVG(cp.actual_arpu_period) AS actual_arpu, AVG(cp.stated_arpu) AS stated_arpu, COUNT(*) AS customers",
        MAIN_FILTERS, MAIN_START, MAIN_END,
    ).iloc[0]

    card1, card2, card3 = st.columns(3, gap="small")
    with card1:
        render_kpi("TOTAL RECEIVED REVENUE", money(fixed_total),
                   "January–June 2025 • Fixed validation period • Ignores filters", "💰", accent="red")
    with card2:
        render_kpi("STATISTICAL TEST (T5)", t5_display, t5_note, "🧪", muted=True, accent="indigo")
    with card3:
        render_kpi("RECEIVED / SUBSCRIBER / MONTH", money(arpu_result["actual_arpu"]),
                   f"Average actual monthly ARPU • {months_in_period(MAIN_START, MAIN_END)}-month period", "👥", accent="teal")

    left, right = st.columns(2, gap="small")

    # Chart 1 — DUMBBELL: stated ARPU vs actual received ARPU for every plan (same data as the old gap bars).
    gap = pd.DataFrame()
    with left:
        with card("ov_gap"):
            render_chart_title("1. Plan-wise received-minus-stated ARPU gap", "🎯")
            local = chart_filter_ui(
                "ov_gap",
                ("connection", "region", "status"),
                MAIN_FILTERS,
                extras={"gap_view": ("Gap filter", ["All plans", "Shortfall only (< 0)", "Surplus only (>= 0)"])},
            )
            gap = customer_query(
                "cp.plan_name AS plan, COUNT(*) AS subscribers, "
                "AVG(cp.actual_arpu_period) AS received_arpu, AVG(cp.stated_arpu) AS stated_arpu, "
                "AVG(cp.actual_arpu_period - cp.stated_arpu) AS gap_per_subscriber",
                local, MAIN_START, MAIN_END,
                "GROUP BY cp.plan_name ORDER BY gap_per_subscriber ASC",
            )
            if not gap.empty:
                if local["gap_view"] == "Shortfall only (< 0)":
                    gap = gap[gap["gap_per_subscriber"] < 0]
                elif local["gap_view"] == "Surplus only (>= 0)":
                    gap = gap[gap["gap_per_subscriber"] >= 0]
            if not gap.empty:
                fig = go.Figure()
                for _, row in gap.iterrows():
                    below = row["gap_per_subscriber"] < 0
                    fig.add_trace(go.Scatter(
                        x=[row["stated_arpu"], row["received_arpu"]], y=[row["plan"], row["plan"]],
                        mode="lines", line=dict(color=RED if below else TEAL, width=4),
                        showlegend=False, hoverinfo="skip",
                    ))
                fig.add_trace(go.Scatter(
                    x=gap["stated_arpu"], y=gap["plan"], mode="markers", name="Stated ARPU",
                    marker=dict(size=9, color=NAVY, line=dict(width=1.5, color="#fff")),
                    customdata=gap[["subscribers", "received_arpu"]].to_numpy(),
                    hovertemplate="%{y}<br>Stated ARPU: ₹%{x:,.2f}<br>Received ARPU: ₹%{customdata[1]:,.2f}"
                                  "<br>Subscribers: %{customdata[0]:,.0f}<extra></extra>",
                ))
                fig.add_trace(go.Scatter(
                    x=gap["received_arpu"], y=gap["plan"], mode="markers+text", name="Received ARPU",
                    marker=dict(size=9, color=[RED if g < 0 else TEAL for g in gap["gap_per_subscriber"]],
                                line=dict(width=1.5, color="#fff")),
                    text=[f"{'−' if g < 0 else '+'}₹{abs(g):,.0f}" for g in gap["gap_per_subscriber"]],
                    textposition=["middle left" if g < 0 else "middle right" for g in gap["gap_per_subscriber"]],
                    textfont=dict(size=8.5, color=INK),
                    customdata=gap[["subscribers", "stated_arpu"]].to_numpy(),
                    hovertemplate="%{y}<br>Received ARPU: ₹%{x:,.2f}<br>Stated ARPU: ₹%{customdata[1]:,.2f}"
                                  "<br>Subscribers: %{customdata[0]:,.0f}<extra></extra>",
                ))
                fig.update_layout(xaxis_title="ARPU (₹ / subscriber / month)", yaxis_title="Plan")
                fig.update_yaxes(categoryorder="array", categoryarray=list(gap["plan"])[::-1], tickfont=dict(size=8.5, color=INK))
                render_chart(fig, 240, margin=dict(l=8, r=16, t=18, b=22))
                st.markdown('<div class="chart-note">Navy dot = stated ARPU. Coloured dot = received ARPU (red = below stated, green = above). Filter by connection, region, churn status, or gap direction.</div>', unsafe_allow_html=True)
            else:
                st.info("No records match these chart filters.")

    # Chart 2 — NESTED DONUT: subscriber share (inner ring) vs received-revenue share (outer ring).
    share = pd.DataFrame()
    share_dim_label = "connection type"
    with right:
        with card("ov_share"):
            render_chart_title("2. Subscriber share vs received-revenue share", "🍩")
            dim_map = {
                "Connection type": "cp.connection_type",
                "Region": "cp.region",
                "Device type": "cp.device_type",
                "Age band": "cp.age_band",
                "Acquisition channel": "cp.acquisition_channel",
            }
            local = chart_filter_ui(
                "ov_share",
                ("region", "device", "status"),
                MAIN_FILTERS,
                extras={"share_dim": ("Compare by", list(dim_map.keys()))},
            )
            dim_col = dim_map[local["share_dim"]]
            share_dim_label = local["share_dim"].lower()
            share = customer_query(
                f"{dim_col} AS segment, COUNT(DISTINCT cp.customer_id) AS subscribers, "
                "SUM(cp.received_revenue) AS received_revenue, "
                "100.0 * COUNT(DISTINCT cp.customer_id) / NULLIF(SUM(COUNT(DISTINCT cp.customer_id)) OVER(),0) AS subscriber_share, "
                "100.0 * SUM(cp.received_revenue) / NULLIF(SUM(SUM(cp.received_revenue)) OVER(),0) AS revenue_share",
                local, MAIN_START, MAIN_END,
                f"GROUP BY {dim_col} ORDER BY revenue_share DESC",
            )
            if not share.empty:
                names = share["segment"].astype(str).tolist()
                colors = [PALETTE[i % len(PALETTE)] for i in range(len(names))]
                fig = go.Figure()
                fig.add_trace(go.Pie(   # outer ring = revenue share
                    labels=names, values=share["revenue_share"].fillna(0), hole=0.58, sort=False,
                    domain=dict(x=[0.0, 1.0], y=[0.0, 1.0]), name="Revenue share",
                    marker=dict(colors=colors, line=dict(color="#fff", width=2)),
                    textinfo="percent", textfont=dict(size=10.5, color="#fff"),
                    customdata=share[["received_revenue"]].fillna(0).to_numpy(),
                    hovertemplate="%{label}<br>Revenue share: %{value:.1f}%<br>Received revenue: ₹%{customdata[0]:,.0f}<extra>Outer ring</extra>",
                ))
                fig.add_trace(go.Pie(   # inner ring = subscriber share
                    labels=names, values=share["subscriber_share"].fillna(0), hole=0.38, sort=False,
                    domain=dict(x=[0.24, 0.76], y=[0.24, 0.76]), name="Subscriber share", showlegend=False,
                    marker=dict(colors=colors, line=dict(color="#fff", width=2)), opacity=0.62,
                    textinfo="percent", textfont=dict(size=9.5, color="#fff"),
                    customdata=share[["subscribers"]].fillna(0).to_numpy(),
                    hovertemplate="%{label}<br>Subscriber share: %{value:.1f}%<br>Subscribers: %{customdata[0]:,.0f}<extra>Inner ring</extra>",
                ))
                fig.update_layout(
                    annotations=[dict(text="Inner: subs<br>Outer: rev", x=0.5, y=0.5,
                                      showarrow=False, font=dict(size=8, color="#5E6671"))],
                    legend=dict(orientation="h", y=1.10, x=0),
                )
                render_chart(fig, 240, margin=dict(l=8, r=8, t=22, b=4))
                st.markdown(f'<div class="chart-note">Comparing {escape(share_dim_label)} segments: if the outer ring exceeds the inner ring, that segment earns more than its subscriber share.</div>', unsafe_allow_html=True)
            else:
                st.info("No segment records match these chart filters.")

    # Chart 3 — REVENUE FUNNEL across the SQL NTILE(10) deciles.
    deciles = pd.DataFrame()
    chart3_col, take_col = st.columns([2.2, 1], gap="small")
    with chart3_col:
        with card("ov_decile"):
            render_chart_title("3. Revenue contribution across subscriber deciles", "🔻")
            metric_map = {
                "Period ARPU": "cp.actual_arpu_period",
                "Received revenue": "cp.received_revenue",
                "6M recharge total": "cp.recharge_total_6m",
            }
            local = chart_filter_ui(
                "ov_decile",
                ("plan", "connection", "region"),
                MAIN_FILTERS,
                extras={
                    "decile_slice": ("Decile focus", ["All 10 deciles", "Top 5 (1–5)", "Bottom 5 (6–10)"]),
                    "decile_metric": ("Rank deciles by", list(metric_map.keys())),
                },
            )
            rank_expr = metric_map[local["decile_metric"]]
            decile_where, decile_params = where_for(local, "cp")
            decile_sql = customer_period_cte(MAIN_START, MAIN_END) + f"""
                , ranked AS (
                    SELECT cp.customer_id, cp.received_revenue, cp.actual_arpu_period,
                           NTILE(10) OVER (ORDER BY {rank_expr} DESC, cp.customer_id) AS decile
                    FROM customer_period cp WHERE {decile_where}
                ), grouped AS (
                    SELECT decile, COUNT(*) AS subscribers, SUM(received_revenue) AS received_revenue
                    FROM ranked GROUP BY decile
                )
                SELECT decile, subscribers, received_revenue,
                       100.0 * received_revenue / NULLIF(SUM(received_revenue) OVER(),0) AS revenue_share
                FROM grouped ORDER BY decile
            """
            deciles = q(decile_sql, [*decile_params])
            if not deciles.empty:
                d = deciles.fillna(0)
                if local["decile_slice"] == "Top 5 (1–5)":
                    d = d[d["decile"] <= 5]
                elif local["decile_slice"] == "Bottom 5 (6–10)":
                    d = d[d["decile"] >= 6]
                n = len(d)
                fig = go.Figure(go.Funnel(
                    y=[f"Decile {int(v)}" for v in d["decile"]],
                    x=d["revenue_share"],
                    text=[f"{v:.1f}%" for v in d["revenue_share"]], textinfo="text",
                    textposition="auto", insidetextfont=dict(size=10, color="#fff"), outsidetextfont=dict(size=9.5, color=INK),
                    marker=dict(color=[shade(i, n) for i in range(n)], line=dict(width=1, color="#fff")),
                    connector=dict(line=dict(color="#F5C1CA", width=1), fillcolor="rgba(245,193,202,.35)"),
                    customdata=d[["subscribers", "received_revenue"]].to_numpy(),
                    hovertemplate="%{y}<br>Revenue share: %{x:.1f}%<br>Subscribers: %{customdata[0]:,.0f}"
                                  "<br>Received revenue: ₹%{customdata[1]:,.0f}<extra></extra>",
                ))
                render_chart(fig, 240, margin=dict(l=12, r=12, t=4, b=4))
                st.markdown(f'<div class="chart-note">Deciles are calculated in SQL with NTILE(10), ranked by {escape(local["decile_metric"].lower())} from highest to lowest.</div>', unsafe_allow_html=True)
            else:
                st.info("No subscriber records match the decile chart filters.")

    # Key takeaways — every line is computed from the charts' own data (nothing invented).
    facts: List[Tuple[str, str]] = []   # (html, plain text)
    if not gap.empty:
        worst, best = gap.iloc[0], gap.iloc[-1]
        word = "below" if worst["gap_per_subscriber"] < 0 else "above"
        facts.append((
            f"<b>{escape(str(worst['plan']))}</b> has the widest shortfall: received ARPU is "
            f"₹{abs(worst['gap_per_subscriber']):,.0f} {word} the stated ARPU.",
            f"{worst['plan']} has the widest ARPU shortfall (₹{abs(worst['gap_per_subscriber']):,.0f} {word} stated).",
        ))
        if len(gap) > 1:
            facts.append((
                f"<b>{escape(str(best['plan']))}</b> is closest to its stated ARPU (gap ₹{best['gap_per_subscriber']:,.0f}).",
                f"{best['plan']} is closest to its stated ARPU.",
            ))
    if not deciles.empty and pd.notna(deciles["revenue_share"]).any():
        top1 = deciles.iloc[0]["revenue_share"]
        top3 = deciles.head(3)["revenue_share"].sum()
        facts.append((
            f"The top decile of subscribers brings <b>{top1:.1f}%</b> of received revenue; the top 3 deciles bring <b>{top3:.1f}%</b>.",
            f"The top 3 subscriber deciles bring {top3:.1f}% of received revenue.",
        ))
    if not share.empty and pd.notna(share["revenue_share"]).any():
        lead = share.sort_values("revenue_share", ascending=False).iloc[0]
        facts.append((
            f"<b>{escape(str(lead['segment']))}</b> contributes {lead['revenue_share']:.1f}% of revenue "
            f"from {lead['subscriber_share']:.1f}% of subscribers.",
            f"{lead['segment']} contributes {lead['revenue_share']:.1f}% of revenue from {lead['subscriber_share']:.1f}% of subscribers.",
        ))

    with take_col:
        if not facts:
            facts = [("Adjust the filters to see insights for this selection.", "")]
        body = "".join(
            f'<div class="take-item"><div class="take-dot">{i}</div><div>{html_text}</div></div>'
            for i, (html_text, _) in enumerate(facts, start=1)
        )
        st.markdown(
            f'<div class="take-card"><div class="take-title">🎯 Key Takeaways</div>{body}</div>',
            unsafe_allow_html=True,
        )

    plain = [p for _, p in facts if p]
    if plain:
        st.markdown(
            f'<div class="insight-bar">📊 <b>Overall Insight:</b> {escape(" ".join(plain[:3]))}</div>',
            unsafe_allow_html=True,
        )

# ============================================================
# PAGE 2 — REVENUE DETAIL
# ============================================================
with page_detail:
    main_where, main_params = where_for(MAIN_FILTERS, "cf")
    plan_df = q(
        f"SELECT DISTINCT cf.plan_name AS value FROM customer_features cf WHERE {main_where} ORDER BY value",
        main_params,
    )
    available_plans = plan_df["value"].dropna().astype(str).tolist()

    if not available_plans:
        st.markdown('<div class="section-label">Revenue Detail</div>', unsafe_allow_html=True)
        st.info("No plans match the main sidebar filters.")
    else:
        hdr_col, selector_col = st.columns([2.2, 1], gap="small")
        with hdr_col:
            st.markdown(
                '<div class="section-label">Revenue Detail</div>'
                '<div class="detail-sub">Select a plan to inspect its revenue, circle performance, connection contribution and segment breakdown.</div>',
                unsafe_allow_html=True,
            )
        with selector_col:
            default_index = available_plans.index(main_plan) if main_plan in available_plans else 0
            selected_plan = st.selectbox("Plan selector", available_plans, index=default_index, key="detail_plan_selector")

        detail_filters = {"plan": selected_plan, "connection": main_connection, "region": main_region}
        summary = customer_query(
            "COUNT(*) AS subscribers, SUM(cp.received_revenue) AS revenue, "
            "AVG(cp.actual_arpu_period) AS actual_arpu, AVG(cp.stated_arpu) AS stated_arpu",
            detail_filters, MAIN_START, MAIN_END,
        ).iloc[0]

        k1, k2, k3 = st.columns(3, gap="small")
        with k1:
            render_kpi("PLAN SUBSCRIBERS", f"{int(summary['subscribers']):,}", "Customer-level records in selected plan", "👥", accent="indigo")
        with k2:
            render_kpi("RECEIVED REVENUE", money(summary["revenue"]), f"{MAIN_START} to {MAIN_END}", "💰", accent="red")
        with k3:
            render_kpi("ACTUAL MONTHLY ARPU", money(summary["actual_arpu"]), f"Stated ARPU reference: {money(summary['stated_arpu'])}", "📈", accent="teal")

        left, right = st.columns(2, gap="small")

        # Detail chart 1 — SUNBURST: plan family (Prepaid / Postpaid) → plan, sized by received revenue.
        with left:
            with card("dt_compare"):
                render_chart_title("1. Plan-wise received-revenue comparison", "☀️")
                local = chart_filter_ui("detail_compare", ("connection", "region", "circle", "status"), MAIN_FILTERS)
                compare_filters = {
                    "plan": "All",
                    "connection": local["connection"],
                    "region": local["region"],
                    "circle": local["circle"],
                    "status": local["status"],
                }
                comparison = customer_query(
                    "cp.plan_name AS plan, SUM(cp.received_revenue) AS revenue, "
                    "COUNT(*) AS subscribers, AVG(cp.actual_arpu_period) AS actual_arpu",
                    compare_filters, MAIN_START, MAIN_END,
                    "GROUP BY cp.plan_name ORDER BY revenue",
                )
                comparison = comparison[comparison["revenue"].fillna(0) > 0] if not comparison.empty else comparison
                if not comparison.empty:
                    comparison = comparison.assign(
                        family=comparison["plan"].astype(str).str.split().str[0].fillna("Other")
                    )
                    fam_totals = comparison.groupby("family")["revenue"].sum()
                    fam_colors = {f: [DARK_RED, INDIGO, TEAL, "#F08A00"][i % 4] for i, f in enumerate(sorted(fam_totals.index))}
                    ids, labels, parents, values, colors = [], [], [], [], []
                    for fam, total in fam_totals.items():
                        ids.append(fam); labels.append(fam); parents.append(""); values.append(float(total)); colors.append(fam_colors[fam])
                    for _, row in comparison.iterrows():
                        ids.append(f"{row['family']}|{row['plan']}"); labels.append(str(row["plan"]))
                        parents.append(row["family"]); values.append(float(row["revenue"]))
                        colors.append(AMBER if row["plan"] == selected_plan else tint(fam_colors[row["family"]], 0.55))
                    fig = go.Figure(go.Sunburst(
                        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total",
                        marker=dict(colors=colors, line=dict(color="#fff", width=1.5)),
                        insidetextorientation="radial", textfont=dict(size=10, color=INK),
                        hovertemplate="%{label}<br>Received revenue: ₹%{value:,.0f}<br>%{percentParent:.1%} of its group<extra></extra>",
                    ))
                    render_chart(fig, 240, margin=dict(l=4, r=4, t=4, b=4))
                    st.markdown('<div class="chart-note">Inner ring = plan family, outer ring = plans (size = received revenue). Selected plan is gold; filter by connection, region, circle, or churn status.</div>', unsafe_allow_html=True)
                else:
                    st.info("No plan comparison data for these filters.")

        # Detail chart 2 — BUBBLE QUADRANT: 22 Airtel circles (Churn rate % vs Actual ARPU ₹, sized by Received revenue).
        with right:
            with card("dt_quadrant"):
                render_chart_title("2. Circle ARPU vs churn quadrant", "🧭")
                local = chart_filter_ui(
                    "detail_quadrant",
                    ("connection", "device"),
                    MAIN_FILTERS,
                    extras={
                        "plan_scope": ("Plan scope", ["All plans", "Selected plan"]),
                        "labels_mode": ("Circle labels", ["Key outliers", "All circles"]),
                    },
                )
                quad_filters = {
                    "plan": selected_plan if local["plan_scope"] == "Selected plan" else "All",
                    "connection": local["connection"],
                    "region": main_region,
                    "device": local["device"],
                }
                quad = customer_query(
                    "cp.circle_name AS circle, cp.region AS region, "
                    "COUNT(*) AS subscribers, SUM(cp.received_revenue) AS revenue, "
                    "AVG(cp.actual_arpu_period) AS arpu, 100.0 * AVG(cp.is_churned) AS churn_pct",
                    quad_filters, MAIN_START, MAIN_END,
                    "GROUP BY cp.circle_name, cp.region HAVING COUNT(*) > 0 ORDER BY revenue DESC",
                )
                if not quad.empty:
                    qdf = quad.fillna(0).copy()
                    max_rev = max(float(qdf["revenue"].max()), 1.0)
                    avg_churn = float(qdf["churn_pct"].mean())
                    avg_arpu = float(qdf["arpu"].mean())
                    y_min, y_max = float(qdf["arpu"].min()), float(qdf["arpu"].max())
                    y_pad = max(14.0, (y_max - y_min) * 0.25)
                    region_colors = {"North": INDIGO, "South": TEAL, "East": "#FF9F1C", "West": RED}
                    key_circles = set()
                    if len(qdf) > 0:
                        key_circles.add(qdf.nlargest(1, "arpu").iloc[0]["circle"])
                        key_circles.add(qdf.nlargest(1, "churn_pct").iloc[0]["circle"])
                        key_circles.add(qdf.nsmallest(1, "churn_pct").iloc[0]["circle"])
                        key_circles.add(qdf.nlargest(1, "revenue").iloc[0]["circle"])
                    fig = go.Figure()
                    for reg, grp in qdf.groupby("region", sort=True):
                        col = region_colors.get(str(reg), NAVY)
                        sizes = (11 + 22 * (grp["revenue"] / max_rev) ** 0.5).tolist()
                        labels, pos_list = [], []
                        for _, r_row in grp.iterrows():
                            cname = str(r_row["circle"])
                            show = local["labels_mode"] == "All circles" or cname in key_circles
                            labels.append(cname if show else "")
                            pos_list.append("bottom center" if float(r_row["arpu"]) < avg_arpu else "top center")
                        fig.add_trace(go.Scatter(
                            x=grp["churn_pct"], y=grp["arpu"],
                            mode="markers+text", name=str(reg),
                            text=labels, textposition=pos_list,
                            textfont=dict(size=8.5, color=INK),
                            marker=dict(size=sizes, color=col, opacity=0.84, line=dict(width=1.4, color="#fff")),
                            customdata=grp[["circle", "subscribers", "revenue"]].to_numpy(),
                            hovertemplate="<b>%{customdata[0]}</b> (" + escape(str(reg)) + ")"
                                          "<br>Actual ARPU: ₹%{y:,.1f}/mo<br>Churn rate: %{x:.1f}%"
                                          "<br>Received revenue: ₹%{customdata[2]:,.0f}"
                                          "<br>Subscribers: %{customdata[1]:,.0f}<extra></extra>",
                        ))
                    fig.add_vline(x=avg_churn, line_dash="dot", line_color="#8C939E", line_width=1.2)
                    fig.add_hline(y=avg_arpu, line_dash="dot", line_color="#8C939E", line_width=1.2)
                    fig.update_layout(xaxis_title="Churn rate (%)", yaxis_title="Actual ARPU (₹/mo)")
                    fig.update_yaxes(showgrid=True, gridcolor=GRID, range=[y_min - y_pad * 0.7, y_max + y_pad])
                    render_chart(fig, 240, margin=dict(l=32, r=14, t=26, b=24))
                    st.markdown('<div class="chart-note">Each bubble = an Airtel circle (size = received revenue, colour = region). Dashed crosshairs mark circle averages: top-left = high ARPU &amp; low churn.</div>', unsafe_allow_html=True)
                else:
                    st.info("No circle records match these quadrant filters.")

        left2, right2 = st.columns(2, gap="small")

        # Detail chart 3 — GAUGES: share of received revenue for each connection type.
        with left2:
            with card("dt_connection"):
                render_chart_title("3. Connection-wise received revenue", "⏱️")
                conn_dims = ("region", "circle", "channel", "device") if HAS_RECHARGES else ("region", "circle", "device")
                local = chart_filter_ui("detail_connection", conn_dims, MAIN_FILTERS)
                conn_filters = {
                    "plan": "All",
                    "connection": "All",
                    "region": local["region"],
                    "circle": local["circle"],
                    "channel": local.get("channel", "All"),
                    "device": local["device"],
                }
                if HAS_RECHARGES:
                    conn_where, conn_params = recharge_where(conn_filters, MAIN_START, MAIN_END, "cf")
                    connection_revenue = q(
                        f"""
                        SELECT cf.connection_type, SUM(r.amount_inr) AS revenue,
                               COUNT(DISTINCT r.customer_id) AS subscribers
                        FROM recharges r JOIN customer_features cf ON cf.customer_id = r.customer_id
                        WHERE {conn_where}
                        GROUP BY cf.connection_type ORDER BY revenue DESC
                        """,
                        conn_params,
                    )
                else:
                    conn_where, conn_params = where_for(conn_filters, "cf")
                    connection_revenue = q(
                        f"""
                        SELECT cf.connection_type, SUM(cf.recharge_total_6m) AS revenue,
                               COUNT(*) AS subscribers
                        FROM customer_features cf
                        WHERE {conn_where}
                        GROUP BY cf.connection_type ORDER BY revenue DESC
                        """,
                        conn_params,
                    )
                if not connection_revenue.empty:
                    conn = connection_revenue.fillna(0).reset_index(drop=True)
                    total_rev = float(conn["revenue"].sum()) or 1.0
                    n_g = len(conn)
                    fig = go.Figure()
                    for i, row in conn.iterrows():
                        pct = 100.0 * float(row["revenue"]) / total_rev
                        col = PALETTE[i % len(PALETTE)]
                        fig.add_trace(go.Indicator(
                            mode="gauge+number", value=pct,
                            number={"suffix": "%", "valueformat": ".1f", "font": {"size": 21, "color": INK}},
                            title={"font": {"size": 11},
                                   "text": f"<b>{escape(str(row['connection_type']))}</b><br>"
                                           f"<span style='font-size:9.5px;color:#5E6671'>₹{row['revenue']:,.0f} • {int(row['subscribers']):,} subs</span>"},
                            domain={"x": [i / n_g + 0.03, (i + 1) / n_g - 0.03], "y": [0.06, 0.72]},
                            gauge={
                                "axis": {"range": [0, 100], "tickfont": {"size": 8.5, "color": "#5E6671"}},
                                "bar": {"color": col, "thickness": 0.75},
                                "bgcolor": "#fff", "borderwidth": 0,
                                "steps": [{"range": [0, 100], "color": rgba(col, 0.14)}],
                                "threshold": {"line": {"color": NAVY, "width": 2.5}, "thickness": 0.8, "value": pct},
                            },
                        ))
                    render_chart(fig, 240, margin=dict(l=12, r=12, t=24, b=6))
                    st.markdown(f'<div class="chart-note">Each gauge = share of total received revenue (₹{total_rev:,.0f}) across connection types by region, circle,{" channel," if HAS_RECHARGES else ""} and device.</div>', unsafe_allow_html=True)
                else:
                    st.info("No connection-wise revenue for these filters.")

        # Detail chart 4 — ANNOTATED HEATMAP: cross-segment ARPU, revenue, churn, or data usage matrix.
        with right2:
            with card("dt_heatmap"):
                render_chart_title("4. Segment performance heatmap", "🔥")
                dim_cols = {
                    "Region": "cp.region",
                    "Age band": "cp.age_band",
                    "Device type": "cp.device_type",
                    "Acquisition": "cp.acquisition_channel",
                }
                heat_metrics = {
                    "Actual ARPU (₹)": ("AVG(cp.actual_arpu_period)", "₹{:,.0f}"),
                    "Received revenue (₹)": ("SUM(cp.received_revenue)", "₹{:,.0f}"),
                    "Churn rate (%)": ("100.0 * AVG(cp.is_churned)", "{:.1f}%"),
                    "Avg data (GB)": ("AVG(cp.total_data_mb) / 1024.0", "{:.1f} GB"),
                }
                local = chart_filter_ui(
                    "detail_heatmap",
                    ("connection",),
                    MAIN_FILTERS,
                    extras={
                        "heat_metric": ("Metric", list(heat_metrics.keys())),
                        "heat_row": ("Rows", ["Region", "Acquisition", "Device type"]),
                        "heat_col": ("Columns", ["Age band", "Device type", "Acquisition"]),
                    },
                )
                row_dim, col_dim = dim_cols[local["heat_row"]], dim_cols[local["heat_col"]]
                if row_dim == col_dim:
                    col_dim = dim_cols["Age band"] if local["heat_row"] != "Age band" else dim_cols["Device type"]
                metric_sql, metric_fmt = heat_metrics[local["heat_metric"]]
                heat_filters = {
                    "plan": main_plan,
                    "connection": local["connection"],
                    "region": main_region,
                }
                heat_df = customer_query(
                    f"{row_dim} AS row_lbl, {col_dim} AS col_lbl, {metric_sql} AS val",
                    heat_filters, MAIN_START, MAIN_END,
                    f"GROUP BY {row_dim}, {col_dim}",
                )
                if not heat_df.empty:
                    pivot = heat_df.pivot(index="row_lbl", columns="col_lbl", values="val").fillna(0)
                    text_vals = []
                    for r_idx in range(len(pivot.index)):
                        row_txt = []
                        for c_idx in range(len(pivot.columns)):
                            val = float(pivot.iloc[r_idx, c_idx])
                            row_txt.append(f"₹{val/1e5:,.1f}L" if local["heat_metric"] == "Received revenue (₹)" and val >= 1e5 else metric_fmt.format(val))
                        text_vals.append(row_txt)
                    fig = go.Figure(go.Heatmap(
                        z=pivot.to_numpy(),
                        x=[str(c) for c in pivot.columns],
                        y=[str(r) for r in pivot.index],
                        text=text_vals,
                        texttemplate="%{text}",
                        textfont=dict(size=10, color=INK),
                        colorscale=[[0.0, "#FFF5F7"], [0.45, "#FFD0D9"], [0.8, "#FF8EA3"], [1.0, "#FF4D6D"]],
                        showscale=False,
                        xgap=3, ygap=3,
                        hovertemplate="%{y} × %{x}<br>" + escape(local["heat_metric"]) + ": <b>%{text}</b><extra></extra>",
                    ))
                    fig.update_layout(xaxis_title=local["heat_col"], yaxis_title=local["heat_row"])
                    fig.update_xaxes(side="top", showgrid=False)
                    fig.update_yaxes(autorange="reversed", showgrid=False)
                    render_chart(fig, 240, margin=dict(l=28, r=10, t=34, b=14))
                    st.markdown('<div class="chart-note">Switch metric (ARPU, revenue, churn %, data GB) and axes to spot high-value demographic or acquisition hot spots.</div>', unsafe_allow_html=True)
                else:
                    st.info("No segment records match these heatmap filters.")

# --------------------------- FOOTER ---------------------------
st.markdown(
    '<div class="foot">'
    '<b>AIRTEL TELECOM ANALYTICS • GROUP 2 • DOMAIN B — REVENUE.</b> '
    'Received revenue is recorded recharge/payment value, not billed revenue. '
    'Fixed Jan–Jun 2025 KPI ignores filters. T5 remains unavailable until the validated test result is supplied.'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------- MOUSE EFFECTS (cursor glow, spotlight, 3D tilt, number count-up) ----------------------
components.html(
    r"""
    <script>
    (function () {
      const w = window.parent, doc = w.document;
      // Clean up any older full-screen overlay elements if present
      const oldAurora = doc.getElementById('airtel-aurora');
      if (oldAurora) oldAurora.remove();
      const oldCanvas = doc.getElementById('airtel-bg-canvas');
      if (oldCanvas) oldCanvas.remove();

      if (w.__airtelFx) return;           // install only once
      w.__airtelFx = true;

      const orb = doc.createElement('div');
      orb.id = 'airtel-orb';
      doc.body.appendChild(orb);

      const SEL = '.kpi-card, .take-card, [class*="st-key-card_"]';
      doc.addEventListener('mousemove', function (e) {
        orb.style.left = e.clientX + 'px';
        orb.style.top = e.clientY + 'px';
        const t = e.target.closest ? e.target.closest(SEL) : null;
        if (!t) return;
        const r = t.getBoundingClientRect();
        t.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        t.style.setProperty('--my', (e.clientY - r.top) + 'px');
        if (t.classList.contains('kpi-card')) {
          const px = (e.clientX - r.left) / r.width - 0.5;
          const py = (e.clientY - r.top) / r.height - 0.5;
          t.style.transform = 'perspective(700px) rotateX(' + (-py * 9) + 'deg) rotateY(' + (px * 9) + 'deg) translateY(-5px)';
        }
      });
      doc.addEventListener('mouseout', function (e) {
        const t = e.target.closest ? e.target.closest('.kpi-card') : null;
        if (t && !t.contains(e.relatedTarget)) t.style.transform = '';
      });

      // count-up animation for KPI numbers
      function countUp(el) {
        const txt = el.textContent.trim();
        const m = txt.match(/^(\D*)([\d,]+)(\.\d+)?$/);
        el.dataset.done = '1';
        if (!m) return;
        const prefix = m[1], target = parseFloat(m[2].replace(/,/g, '') + (m[3] || ''));
        const dec = m[3] ? m[3].length - 1 : 0;
        const t0 = performance.now(), dur = 900;
        (function tick(now) {
          const p = Math.min(1, (now - t0) / dur), eased = 1 - Math.pow(1 - p, 3);
          el.textContent = prefix + (target * eased).toLocaleString('en-IN', {minimumFractionDigits: dec, maximumFractionDigits: dec});
          if (p < 1) requestAnimationFrame(tick); else el.textContent = txt;
        })(t0);
      }
      setInterval(function () {
        doc.querySelectorAll('.kpi-value:not([data-done])').forEach(countUp);
      }, 500);

      // Dynamically size chart containers + Plotly SVGs so charts stay crisp and fit cleanly
      let fitRaf = 0;
      function syncPlotlyHeights(panel, targetH) {
        if (!w.Plotly || !panel) return;
        panel.querySelectorAll('[data-testid="stPlotlyChart"] .js-plotly-plot').forEach(function (plotEl) {
          const fl = plotEl._fullLayout;
          const wrap = plotEl.closest('[data-testid="stPlotlyChart"]');
          const h = Math.round((wrap ? wrap.getBoundingClientRect().height : 0) || targetH || 235);
          if (h < 120) return;
          if (!fl || Math.abs((fl.height || 0) - h) >= 2) {
            try { w.Plotly.relayout(plotEl, { height: h }); } catch (e) {}
          }
        });
      }

      function fitChartsToViewport() {
        if (fitRaf) w.cancelAnimationFrame(fitRaf);
        fitRaf = w.requestAnimationFrame(function () {
          const main = doc.querySelector('[data-testid="stMain"]');
          const block = main ? main.querySelector('.block-container') : null;
          if (!main || !block) return;
          const panel = main.querySelector('[role="tabpanel"]:not([hidden])') || main;
          const charts = panel.querySelectorAll('[data-testid="stPlotlyChart"]');
          if (!charts.length) return;
          const vh = w.innerHeight || doc.documentElement.clientHeight;
          const cur = charts[0].getBoundingClientRect().height;
          if (cur < 50) return;
          const topSet = new Set();
          charts.forEach(function (c) { topSet.add(Math.round(c.getBoundingClientRect().top / 60)); });
          const rowCount = Math.max(1, topSet.size);
          const blockH = block.getBoundingClientRect().height;
          const nonChartH = Math.max(240, blockH - (rowCount * cur));
          const perRowTarget = Math.floor((vh - nonChartH - 14) / Math.min(2, rowCount));
          const next = Math.max(220, Math.min(320, perRowTarget));
          if (Math.abs(next - cur) >= 2) {
            doc.documentElement.style.setProperty('--chart-h', next + 'px');
            w.dispatchEvent(new Event('resize'));
          }
          syncPlotlyHeights(panel, next);
        });
      }
      w.addEventListener('resize', fitChartsToViewport);
      doc.addEventListener('click', function (e) {
        if (e.target.closest && e.target.closest('[data-baseweb="tab"], [data-testid="stTab"]')) {
          setTimeout(fitChartsToViewport, 80);
          setTimeout(fitChartsToViewport, 350);
          setTimeout(fitChartsToViewport, 750);
        }
      });
      if (w.MutationObserver) {
        const obs = new w.MutationObserver(function () { fitChartsToViewport(); });
        const mainNode = doc.querySelector('[data-testid="stMain"]') || doc.body;
        obs.observe(mainNode, { childList: true, subtree: true });
      }
      setInterval(fitChartsToViewport, 700);
      setTimeout(fitChartsToViewport, 120);
      setTimeout(fitChartsToViewport, 450);
      setTimeout(fitChartsToViewport, 900);
    })();
    </script>
    """,
    height=0,
)
