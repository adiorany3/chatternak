from __future__ import annotations

import streamlit as st


def apply_accessible_theme() -> None:
    """Force a clean light UI for consistent readability on Streamlit Cloud.

    Streamlit users can have browser/app preferences set to dark mode. This app is
    intentionally forced to a high-contrast light palette so forms, cards, tables,
    warnings, and exported-report areas stay readable for all peternak.
    """
    st.markdown(
        """
        <style>
        :root {
            color-scheme: light !important;
            --background-color: #ffffff !important;
            --secondary-background-color: #f8fafc !important;
            --text-color: #0f172a !important;
            --primary-color: #2e7d32 !important;
            --ptn-muted-text: #475569;
            --ptn-border: #d7dee8;
            --ptn-soft-border: #e2e8f0;
            --ptn-card: #ffffff;
            --ptn-card-soft: #f8fafc;
            --ptn-success-bg: #ecfdf5;
            --ptn-success-border: #86efac;
            --ptn-warning-bg: #fffbeb;
            --ptn-warning-border: #facc15;
            --ptn-error-bg: #fef2f2;
            --ptn-error-border: #fca5a5;
            --ptn-info-bg: #eff6ff;
            --ptn-info-border: #93c5fd;
            --ptn-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
            --ptn-radius: 16px;
        }

        html, body, [data-testid="stAppViewContainer"], .stApp,
        [data-testid="stHeader"], [data-testid="stToolbar"] {
            color: #0f172a !important;
            background-color: #ffffff !important;
        }

        [data-testid="stAppViewContainer"] > .main,
        section.main, .main .block-container {
            background-color: #ffffff !important;
        }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.6rem;
        }

        h1, h2, h3, h4, h5, h6,
        p, li, label, span, small, strong, em,
        .stMarkdown, .stCaptionContainer, .stText,
        [data-testid="stMarkdownContainer"] {
            color: #0f172a !important;
        }

        .stCaptionContainer, small, .ptn-card-meta, .ptn-card-body {
            color: #475569 !important;
        }

        [data-testid="stSidebar"] {
            background-color: #f8fafc !important;
            border-right: 1px solid #d7dee8 !important;
        }

        [data-testid="stSidebar"] *,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #0f172a !important;
        }

        .ptn-card,
        .ptn-step-card,
        .ptn-footer-card {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #d7dee8 !important;
            border-radius: var(--ptn-radius);
            padding: 1rem;
            box-shadow: var(--ptn-shadow);
        }

        .ptn-step-card {
            min-height: 190px;
            display: flex;
            flex-direction: column;
            gap: 0.42rem;
        }

        .ptn-step-number {
            width: 2.35rem;
            height: 2.35rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            font-size: 1.1rem;
            font-weight: 800;
            color: #ffffff !important;
            background: #2e7d32 !important;
            margin-bottom: 0.2rem;
        }

        .ptn-card-title {
            font-size: 1rem;
            font-weight: 800;
            line-height: 1.35;
            color: #0f172a !important;
        }

        .ptn-card-body {
            font-size: 0.88rem;
            line-height: 1.5;
        }

        .ptn-card-meta {
            margin-top: auto;
            font-size: 0.78rem;
            line-height: 1.35;
        }

        .ptn-footer-card {
            text-align: center;
            font-size: 0.9rem;
            padding: 0.8rem 1rem;
            margin-top: 0.75rem;
        }

        div[data-testid="stMetric"] {
            background: #ffffff !important;
            border: 1px solid #d7dee8 !important;
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
            color: #0f172a !important;
        }

        div[data-testid="stChatMessage"] {
            background-color: #f8fafc !important;
            border: 1px solid #d7dee8 !important;
            border-radius: 16px;
            padding: 0.65rem 0.75rem;
        }

        div[data-testid="stExpander"] {
            border-color: #d7dee8 !important;
            background-color: #ffffff !important;
            border-radius: 14px;
        }

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary * {
            color: #0f172a !important;
            background-color: #ffffff !important;
        }

        .stAlert,
        div[data-testid="stAlert"] {
            color: #0f172a !important;
            border-radius: 14px !important;
            border: 1px solid #d7dee8 !important;
        }

        button, [role="button"], .stButton > button, .stDownloadButton > button {
            border-radius: 12px !important;
            font-weight: 650 !important;
        }

        .stButton > button, .stDownloadButton > button {
            border: 1px solid #cbd5e1 !important;
            color: #0f172a !important;
            background-color: #ffffff !important;
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: #2e7d32 !important;
            color: #2e7d32 !important;
            background-color: #f0fdf4 !important;
        }

        .stButton > button:disabled,
        .stDownloadButton > button:disabled {
            color: #94a3b8 !important;
            background-color: #f1f5f9 !important;
            border-color: #e2e8f0 !important;
            opacity: 1 !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.4rem;
            flex-wrap: wrap;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.45rem 0.9rem;
            background-color: #ffffff !important;
            border: 1px solid #d7dee8 !important;
            color: #0f172a !important;
        }

        .stTabs [aria-selected="true"] {
            border-color: #2e7d32 !important;
            color: #2e7d32 !important;
            background-color: #f0fdf4 !important;
        }

        input, textarea, select,
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="base-input"] > div,
        div[data-baseweb="select"] span,
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {
            color: #0f172a !important;
            background-color: #ffffff !important;
            border-color: #cbd5e1 !important;
        }

        input::placeholder, textarea::placeholder {
            color: #64748b !important;
        }

        div[data-testid="stDataFrame"], .stDataFrame, .stTable,
        div[data-testid="stDataFrame"] *, .stTable * {
            color: #0f172a !important;
        }

        div[data-testid="stDataFrame"], .stTable {
            border: 1px solid #d7dee8 !important;
            border-radius: 12px !important;
            background: #ffffff !important;
        }

        hr {
            border-color: #d7dee8 !important;
        }

        a {
            color: #166534 !important;
            font-weight: 650;
        }

        pre, code {
            color: #0f172a !important;
            background-color: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
        }

        .streamlit-expanderContent,
        [data-testid="stVerticalBlock"],
        [data-testid="column"] {
            color: #0f172a !important;
        }

        @media (max-width: 768px) {
            .ptn-step-card {
                min-height: auto;
            }
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
