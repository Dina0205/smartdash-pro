# ============================================================
#  components/finance.py — Module finance (yfinance)
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings("ignore")

from config import (
    COLOR_UP, COLOR_DOWN, COLOR_NEUT, ACCENT, CHART_COLORS, BG_CARD
)
from utils.helpers import (
    fmt_currency, fmt_pct, fmt_volume, color_delta, arrow_delta,
    compute_rsi, compute_macd, compute_bollinger,
    compute_returns, compute_sharpe, compute_max_drawdown,
    compute_volatility, kpi_card, section_header
)


# ── Récupération données ─────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def fetch_quote(ticker: str) -> dict:
    """Récupère le dernier cours + méta d'un ticker."""
    try:
        t    = yf.Ticker(ticker)
        info = t.fast_info
        hist = t.history(period="2d", interval="1d")

        if hist.empty:
            return {}

        price      = float(info.last_price) if hasattr(info, "last_price") else float(hist["Close"].iloc[-1])
        prev       = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
        change     = price - prev
        change_pct = (change / prev * 100) if prev else 0

        return {
            "ticker":     ticker,
            "price":      price,
            "prev_close": prev,
            "change":     change,
            "change_pct": change_pct,
            "volume":     float(hist["Volume"].iloc[-1]) if "Volume" in hist else 0,
            "market_cap": getattr(info, "market_cap", None),
            "currency":   getattr(info, "currency", "USD"),
        }
    except Exception as e:
        st.warning(f"⚠️ Impossible de récupérer {ticker} : {e}")
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(ticker: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    """Récupère l'historique OHLCV d'un ticker."""
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval)
        hist.index = pd.to_datetime(hist.index)
        if hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)
        return hist
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_multi(tickers: List[str], period: str = "1mo") -> pd.DataFrame:
    """Récupère les cours de clôture de plusieurs tickers."""
    try:
        # ── CAS 1 SEUL TICKER : pas de MultiIndex ────────────
        if len(tickers) == 1:
            t    = yf.Ticker(tickers[0])
            hist = t.history(period=period, interval="1d", auto_adjust=True)
            if hist.empty:
                return pd.DataFrame()
            idx = hist.index
            if idx.tz is not None:
                idx = idx.tz_localize(None)
            return pd.DataFrame({tickers[0]: hist["Close"].values}, index=idx)

        # ── CAS MULTI TICKERS ────────────────────────────────
        raw = yf.download(
            tickers, period=period, interval="1d",
            group_by="ticker", auto_adjust=True, progress=False,
        )
        closes = {}
        for t in tickers:
            try:
                closes[t] = raw[t]["Close"]
            except KeyError:
                pass
        return pd.DataFrame(closes).dropna(how="all")
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_batch_quotes(tickers: List[str]) -> List[dict]:
    """Récupère les quotes de plusieurs tickers."""
    results = []
    for t in tickers:
        q = fetch_quote(t)
        if q:
            results.append(q)
    return results


# ── Graphiques ───────────────────────────────────────────────

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(showgrid=False, zeroline=False, showline=False,
               color="#64748b"),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
               zeroline=False, showline=False, color="#64748b"),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                font=dict(color="#94a3b8", size=10)),
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="#334155",
                    font=dict(color="#e2e8f0")),
)


def chart_candlestick(df: pd.DataFrame, ticker: str,
                      show_volume: bool = True,
                      show_bollinger: bool = False) -> go.Figure:
    """Graphique chandeliers japonais avec volume optionnel."""
    rows    = 2 if show_volume else 1
    heights = [0.75, 0.25] if show_volume else [1.0]

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02, row_heights=heights)

    # Chandeliers
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name=ticker,
        increasing_line_color=COLOR_UP,   increasing_fillcolor=COLOR_UP,
        decreasing_line_color=COLOR_DOWN, decreasing_fillcolor=COLOR_DOWN,
        line_width=1,
    ), row=1, col=1)

    # Bollinger
    if show_bollinger and len(df) >= 20:
        upper, mid, lower = compute_bollinger(df["Close"])
        for band, name, dash in [(upper, "BB Upper", "dot"),
                                  (mid,   "BB Mid",   "solid"),
                                  (lower, "BB Lower", "dot")]:
            fig.add_trace(go.Scatter(
                x=df.index, y=band, name=name, mode="lines",
                line=dict(color=ACCENT, width=1, dash=dash),
                opacity=0.7,
            ), row=1, col=1)

    # Volume
    if show_volume and "Volume" in df:
        colors = [COLOR_UP if c >= o else COLOR_DOWN
                  for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"], name="Volume",
            marker_color=colors, opacity=0.5,
        ), row=2, col=1)
        fig.update_yaxes(title_text="Vol", row=2, col=1,
                         title_font=dict(size=9))

    layout = {**CHART_LAYOUT, "title": {"text": f"<b>{ticker}</b> — Chandeliers",
                                         "font": {"color": "#e2e8f0", "size": 14}}}
    fig.update_layout(**layout, height=480, showlegend=False,
                      xaxis_rangeslider_visible=False)
    return fig


def chart_line_comparison(df: pd.DataFrame, normalize: bool = True) -> go.Figure:
    """Comparaison multi-actifs (base 100 ou valeur brute)."""
    fig = go.Figure()

    data = df.copy().dropna(how="all")
    if normalize and not data.empty:
        first = data.iloc[0].replace(0, np.nan)
        data  = (data / first * 100)

    for i, col in enumerate(data.columns):
        color  = CHART_COLORS[i % len(CHART_COLORS)]
        series = data[col].dropna()
        fig.add_trace(go.Scatter(
            x=series.index, y=series, name=col,
            mode="lines", line=dict(color=color, width=2),
            hovertemplate=f"<b>{col}</b><br>%{{y:.2f}}<br>%{{x}}<extra></extra>",
        ))

    title  = "Performance relative (base 100)" if normalize else "Cours de clôture"
    layout = {**CHART_LAYOUT,
               "title": {"text": title, "font": {"color": "#e2e8f0", "size": 13}}}
    fig.update_layout(**layout, height=380, hovermode="x unified")
    return fig


def chart_rsi(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Graphique RSI avec zones de surachat/survente."""
    rsi = compute_rsi(df["Close"]).dropna()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rsi.index, y=rsi, name="RSI (14)",
        mode="lines", line=dict(color=COLOR_UP, width=2),
    ))
    for level, label in [(70, "Surachat"), (30, "Survente")]:
        fig.add_hline(y=level, line_dash="dash",
                      line_color=COLOR_DOWN if level == 70 else COLOR_UP,
                      line_width=1, opacity=0.6,
                      annotation_text=label,
                      annotation_font_color="#94a3b8",
                      annotation_font_size=9)

    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,77,109,0.06)", line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,212,255,0.06)",  line_width=0)

    layout = {**CHART_LAYOUT,
               "title": {"text": f"RSI(14) — {ticker}",
                          "font": {"color": "#e2e8f0", "size": 13}}}
    fig.update_layout(**layout, height=260, yaxis_range=[0, 100])
    return fig


def chart_macd(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Graphique MACD avec histogramme."""
    macd, signal, hist_macd = compute_macd(df["Close"])

    fig        = make_subplots(rows=1, cols=1)
    bar_colors = [COLOR_UP if v >= 0 else COLOR_DOWN for v in hist_macd]

    fig.add_trace(go.Bar(
        x=df.index, y=hist_macd, name="Histogramme",
        marker_color=bar_colors, opacity=0.7,
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=macd, name="MACD",
        mode="lines", line=dict(color=COLOR_UP, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=signal, name="Signal",
        mode="lines", line=dict(color=ACCENT, width=2, dash="dash"),
    ))

    layout = {**CHART_LAYOUT,
               "title": {"text": f"MACD — {ticker}",
                          "font": {"color": "#e2e8f0", "size": 13}}}
    fig.update_layout(**layout, height=260)
    return fig


def chart_returns_dist(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Distribution des rendements avec courbe normale."""
    returns = compute_returns(df["Close"]).dropna() * 100

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=returns, name="Rendements",
        marker_color=COLOR_UP, opacity=0.7,
        histnorm="probability density", nbinsx=50,
    ))

    mu, sigma = returns.mean(), returns.std()
    x_range   = np.linspace(returns.min(), returns.max(), 200)
    normal    = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(
                    -0.5 * ((x_range - mu) / sigma) ** 2)
    fig.add_trace(go.Scatter(
        x=x_range, y=normal, mode="lines",
        line=dict(color=ACCENT, width=2), name="Normal",
    ))

    layout = {**CHART_LAYOUT,
               "title": {"text": f"Distribution des rendements — {ticker}",
                          "font": {"color": "#e2e8f0", "size": 13}}}
    fig.update_layout(**layout, height=300, yaxis_title="Densité")
    return fig


def chart_heatmap_correlation(df: pd.DataFrame) -> go.Figure:
    """Matrice de corrélation entre actifs."""
    returns = df.pct_change().dropna()
    corr    = returns.corr()

    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale=[[0, COLOR_DOWN], [0.5, "#1e293b"], [1, COLOR_UP]],
        zmin=-1, zmax=1,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=10, color="#e2e8f0"),
        hoverongaps=False,
    ))

    layout = {**CHART_LAYOUT,
               "title": {"text": "Matrice de corrélation",
                          "font": {"color": "#e2e8f0", "size": 13}}}
    fig.update_layout(**layout, height=400)
    return fig


# ── Composants UI ────────────────────────────────────────────

def render_ticker_cards(quotes: List[dict], cols_count: int = 4) -> None:
    """Affiche les cards de cours en grille."""
    cols = st.columns(cols_count)
    for i, q in enumerate(quotes):
        with cols[i % cols_count]:
            pct   = q.get("change_pct", 0)
            c     = color_delta(pct)
            arrow = arrow_delta(pct)
            st.markdown(f"""
            <div style="
                background: rgba(17,24,39,0.9);
                border: 1px solid rgba(255,255,255,0.07);
                border-left: 3px solid {c};
                border-radius: 10px;
                padding: 14px 16px;
                margin-bottom: 10px;
            ">
                <p style="margin:0; font-size:0.72rem; color:#64748b;
                           font-weight:700; letter-spacing:0.08em;">
                    {q['ticker']}
                </p>
                <p style="margin:6px 0 0; font-size:1.35rem; font-weight:700;
                           color:#e2e8f0; line-height:1.1;">
                    {fmt_currency(q['price'], '$', 2)}
                </p>
                <p style="margin:4px 0 0; font-size:0.82rem; color:{c}; font-weight:600;">
                    {arrow} {fmt_pct(pct)}&nbsp;&nbsp;
                    <span style="color:#475569;">
                        {fmt_currency(q['change'], '+$' if q['change'] >= 0 else '-$', 2).replace('--','-')}
                    </span>
                </p>
                <p style="margin:4px 0 0; font-size:0.7rem; color:#475569;">
                    Vol: {fmt_volume(q.get('volume', 0))}
                </p>
            </div>
            """, unsafe_allow_html=True)


def render_market_summary(quotes: List[dict]) -> None:
    """KPIs globaux du portefeuille sélectionné."""
    if not quotes:
        return

    gainers = [q for q in quotes if q.get("change_pct", 0) > 0]
    losers  = [q for q in quotes if q.get("change_pct", 0) < 0]
    avg_chg = np.mean([q.get("change_pct", 0) for q in quotes])
    best    = max(quotes, key=lambda q: q.get("change_pct", -999))
    worst   = min(quotes, key=lambda q: q.get("change_pct",  999))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Actifs suivis", str(len(quotes)), icon="📊")
    with c2:
        kpi_card("Variation moy.", fmt_pct(avg_chg),
                 delta_color=color_delta(avg_chg), icon="📈")
    with c3:
        kpi_card("Meilleur",
                 f"{best['ticker']} {fmt_pct(best['change_pct'])}",
                 delta_color=COLOR_UP, icon="🏆")
    with c4:
        kpi_card("Pire",
                 f"{worst['ticker']} {fmt_pct(worst['change_pct'])}",
                 delta_color=COLOR_DOWN, icon="📉")

    st.markdown(f"""
    <div style="display:flex; gap:8px; margin-top:10px;">
        <span style="background:rgba(0,212,255,0.1); color:{COLOR_UP};
                     padding:4px 12px; border-radius:20px; font-size:0.78rem; font-weight:600;">
            ▲ {len(gainers)} en hausse
        </span>
        <span style="background:rgba(255,77,109,0.1); color:{COLOR_DOWN};
                     padding:4px 12px; border-radius:20px; font-size:0.78rem; font-weight:600;">
            ▼ {len(losers)} en baisse
        </span>
    </div>
    """, unsafe_allow_html=True)


def render_stats_panel(df: pd.DataFrame, ticker: str) -> None:
    """Statistiques avancées d'un actif."""
    if df.empty or "Close" not in df:
        st.warning("Données insuffisantes.")
        return

    returns  = compute_returns(df["Close"]).dropna()
    sharpe   = compute_sharpe(returns)
    mdd      = compute_max_drawdown(df["Close"])
    vol      = compute_volatility(returns)
    last_rsi = compute_rsi(df["Close"]).iloc[-1] if len(df) >= 14 else None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Sharpe Ratio", f"{sharpe:.2f}",
                 delta_color=COLOR_UP if sharpe > 1 else COLOR_DOWN, icon="⚖️")
    with col2:
        kpi_card("Volatilité", f"{vol:.1f}%", icon="〰️")
    with col3:
        kpi_card("Max Drawdown", f"{mdd:.1f}%",
                 delta_color=COLOR_DOWN, icon="🔻")
    with col4:
        if last_rsi is not None:
            rsi_color = (COLOR_DOWN if last_rsi > 70
                         else COLOR_UP if last_rsi < 30
                         else COLOR_NEUT)
            rsi_label = ("Surachat" if last_rsi > 70
                         else "Survente" if last_rsi < 30
                         else "Neutre")
            kpi_card("RSI (14)", f"{last_rsi:.1f}",
                     delta=rsi_label, delta_color=rsi_color, icon="📡")