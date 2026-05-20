from __future__ import annotations

import streamlit as st


def apply_accessible_theme() -> None:
    """Apply UI polish that stays readable in Streamlit light and dark themes.

    The CSS relies on Streamlit theme variables such as --background-color,
    --secondary-background-color, --text-color, and --primary-color so the app
    follows the selected Streamlit theme instead of forcing one fixed palette.
    """
    st.markdown(
        """
        <style>
        :root {
            --ptn-border-fallback: rgba(128, 128, 128, 0.28);
            --ptn-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
            --ptn-radius: 16px;
        }

        html, body, [data-testid="stAppViewContainer"], .stApp {
            color: var(--text-color) !important;
            background-color: var(--background-color) !important;
        }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.6rem;
        }

        h1, h2, h3, h4, h5, h6,
        p, li, label, span, small,
        .stMarkdown, .stCaptionContainer, .stText,
        [data-testid="stMarkdownContainer"] {
            color: var(--text-color);
        }

        [data-testid="stSidebar"] {
            background-color: var(--secondary-background-color);
            border-right: 1px solid var(--ptn-border-fallback);
            border-right: 1px solid color-mix(in srgb, var(--text-color) 14%, transparent);
        }

        [data-testid="stSidebar"] * {
            color: var(--text-color);
        }

        .ptn-card,
        .ptn-step-card,
        .ptn-footer-card {
            background: var(--secondary-background-color);
            color: var(--text-color);
            border: 1px solid var(--ptn-border-fallback);
            border: 1px solid color-mix(in srgb, var(--text-color) 14%, transparent);
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
            color: var(--background-color);
            background: var(--primary-color);
            margin-bottom: 0.2rem;
        }

        .ptn-card-title {
            font-size: 1rem;
            font-weight: 800;
            line-height: 1.35;
            color: var(--text-color);
        }

        .ptn-card-body {
            font-size: 0.88rem;
            line-height: 1.5;
            color: var(--text-color);
            opacity: 0.88;
        }

        .ptn-card-meta {
            margin-top: auto;
            font-size: 0.78rem;
            line-height: 1.35;
            color: var(--text-color);
            opacity: 0.72;
        }

        .ptn-footer-card {
            text-align: center;
            font-size: 0.9rem;
            opacity: 0.86;
            padding: 0.8rem 1rem;
            margin-top: 0.75rem;
        }

        div[data-testid="stMetric"] {
            background: var(--secondary-background-color);
            border: 1px solid var(--ptn-border-fallback);
            border: 1px solid color-mix(in srgb, var(--text-color) 12%, transparent);
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.045);
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
            color: var(--text-color) !important;
        }

        div[data-testid="stChatMessage"] {
            background-color: var(--secondary-background-color);
            border: 1px solid var(--ptn-border-fallback);
            border: 1px solid color-mix(in srgb, var(--text-color) 12%, transparent);
            border-radius: 16px;
            padding: 0.65rem 0.75rem;
        }

        div[data-testid="stExpander"] {
            border-color: var(--ptn-border-fallback) !important;
            border-color: color-mix(in srgb, var(--text-color) 14%, transparent) !important;
            background-color: color-mix(in srgb, var(--secondary-background-color) 88%, transparent);
            border-radius: 14px;
        }

        button, [role="button"], .stButton > button, .stDownloadButton > button {
            border-radius: 12px !important;
            font-weight: 650 !important;
        }

        .stButton > button, .stDownloadButton > button {
            border: 1px solid var(--ptn-border-fallback) !important;
            border: 1px solid color-mix(in srgb, var(--text-color) 14%, transparent) !important;
            color: var(--text-color) !important;
            background-color: var(--secondary-background-color) !important;
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: var(--primary-color) !important;
            color: var(--primary-color) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.4rem;
            flex-wrap: wrap;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 0.45rem 0.9rem;
            background-color: var(--secondary-background-color);
            border: 1px solid var(--ptn-border-fallback);
            border: 1px solid color-mix(in srgb, var(--text-color) 12%, transparent);
        }

        .stTabs [aria-selected="true"] {
            border-color: var(--primary-color) !important;
            color: var(--primary-color) !important;
        }

        input, textarea, select,
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            color: var(--text-color) !important;
            background-color: var(--background-color) !important;
            border-color: var(--ptn-border-fallback) !important;
            border-color: color-mix(in srgb, var(--text-color) 18%, transparent) !important;
        }

        [data-testid="stDataFrame"], .stDataFrame, .stTable {
            color: var(--text-color) !important;
        }

        hr {
            border-color: var(--ptn-border-fallback) !important;
            border-color: color-mix(in srgb, var(--text-color) 14%, transparent) !important;
        }

        a {
            color: var(--primary-color) !important;
            font-weight: 650;
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
