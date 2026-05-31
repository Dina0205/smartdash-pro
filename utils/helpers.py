# ============================================================
#  utils/helpers.py — Fonctions utilitaires partagées
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import pytz


# ── Formatage ───────────────────────────────────────────────

def fmt_currency(value: float, symbol: str = "$", decimals: int = 2) -> str:
    """Formate un nombre en devise lisible."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    if abs(value) >= 1_000_000_000:
        return f"{symbol}{value/1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{symbol}{value/1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{symbol}{value/1_000:.2f}K"
    return f"{symbol}{value:,.{decimals}f}"


def fmt_pct(value: float) -> str:
    """Formate un flottant en pourcentage avec signe."""
    if value is None or np.isnan(value):
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def fmt_volume(vol: float) -> str:
    """Formate un volume de trading."""
    if vol >= 1_000_000_000:
        return f"{vol/1_000_000_000:.1f}B"
    if vol >= 1_000_000:
        return f"{vol/1_000_000:.1f}M"
    if vol >= 1_000:
        return f"{vol/1_000:.0f}K"
    return str(int(vol))


def color_delta(value: float) -> str:
    """Retourne la couleur CSS selon la variation."""
    if value > 0:
        return "#00d4ff"
    elif value < 0:
        return "#ff4d6d"
    return "#94a3b8"


def arrow_delta(value: float) -> str:
    """Retourne une flèche selon la variation."""
    if value > 0:
        return "▲"
    elif value < 0:
        return "▼"
    return "●"


# ── Temps ───────────────────────────────────────────────────

def now_morocco() -> datetime:
    """Retourne l'heure actuelle au Maroc (UTC+1)."""
    tz = pytz.timezone("Africa/Casablanca")
    return datetime.now(tz)


def market_status() -> dict:
    """Indique si les marchés principaux sont ouverts."""
    utc = datetime.utcnow()
    statuses = {}

    # NYSE/NASDAQ : 14h30–21h00 UTC (lun–ven)
    nyse_open  = utc.replace(hour=14, minute=30, second=0, microsecond=0)
    nyse_close = utc.replace(hour=21, minute=0,  second=0, microsecond=0)
    is_weekday = utc.weekday() < 5
    statuses["🇺🇸 NYSE/NASDAQ"] = is_weekday and nyse_open <= utc <= nyse_close

    # LSE : 08h00–16h30 UTC (lun–ven)
    lse_open  = utc.replace(hour=8,  minute=0,  second=0, microsecond=0)
    lse_close = utc.replace(hour=16, minute=30, second=0, microsecond=0)
    statuses["🇬🇧 LSE"] = is_weekday and lse_open <= utc <= lse_close

    # Crypto : 24/7
    statuses["🪙 Crypto"] = True

    return statuses


# ── Indicateurs techniques ───────────────────────────────────

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calcule le RSI (Relative Strength Index)."""
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_macd(series: pd.Series,
                 fast: int = 12, slow: int = 26, signal: int = 9):
    """Calcule MACD, Signal et Histogramme."""
    ema_fast   = series.ewm(span=fast,   adjust=False).mean()
    ema_slow   = series.ewm(span=slow,   adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    """Calcule les Bandes de Bollinger."""
    rolling_mean = series.rolling(window=window).mean()
    rolling_std  = series.rolling(window=window).std()
    upper = rolling_mean + (rolling_std * num_std)
    lower = rolling_mean - (rolling_std * num_std)
    return upper, rolling_mean, lower


def compute_returns(series: pd.Series) -> pd.Series:
    """Rendements journaliers logarithmiques."""
    return np.log(series / series.shift(1))


def compute_sharpe(returns: pd.Series, risk_free: float = 0.05) -> float:
    """Calcule le ratio de Sharpe annualisé."""
    excess = returns - risk_free / 252
    if returns.std() == 0:
        return 0.0
    return float((excess.mean() / returns.std()) * np.sqrt(252))


def compute_max_drawdown(series: pd.Series) -> float:
    """Calcule le drawdown maximum en %."""
    roll_max = series.cummax()
    drawdown = (series - roll_max) / roll_max
    return float(drawdown.min() * 100)


def compute_volatility(returns: pd.Series) -> float:
    """Volatilité annualisée en %."""
    return float(returns.std() * np.sqrt(252) * 100)


# ── Carte KPI Streamlit ──────────────────────────────────────

def kpi_card(label: str, value: str, delta: Optional[str] = None,
             delta_color: str = "#94a3b8", icon: str = "") -> None:
    """Affiche une carte KPI stylisée avec HTML."""
    delta_html = ""
    if delta:
        delta_html = f'<p style="margin:4px 0 0 0; font-size:0.85rem; color:{delta_color}; font-weight:600;">{delta}</p>'
    
    st.markdown(f"""
    <div style="
        background: rgba(17,24,39,0.9);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 18px 20px;
        height: 100%;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    ">
        <p style="margin:0; font-size:0.78rem; color:#64748b; text-transform:uppercase;
                  letter-spacing:0.1em; font-weight:600;">{icon} {label}</p>
        <p style="margin:8px 0 0 0; font-size:1.6rem; font-weight:700;
                  color:#e2e8f0; line-height:1;">{value}</p>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "") -> None:
    """En-tête de section stylisée."""
    st.markdown(f"""
    <div style="margin: 2rem 0 1rem 0; padding-bottom: 0.75rem;
                border-bottom: 1px solid rgba(255,255,255,0.07);">
        <h3 style="margin:0; font-size:1.1rem; font-weight:700; color:#e2e8f0;">{title}</h3>
        {"<p style='margin:4px 0 0 0; font-size:0.82rem; color:#64748b;'>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)
