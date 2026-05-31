# ============================================================
#  components/weather.py — Module météo (OpenWeatherMap)
# ============================================================

import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz

from config import COLOR_UP, COLOR_DOWN, ACCENT, CHART_COLORS
import streamlit as st
from utils.helpers import kpi_card, section_header

BASE_URL    = "https://api.openweathermap.org/data/2.5"
GEO_URL     = "https://api.openweathermap.org/geo/1.0"
ICON_URL    = "https://openweathermap.org/img/wn/{code}@2x.png"

# Codes météo → emoji
WX_EMOJI = {
    range(200, 300): "⛈️",
    range(300, 400): "🌧️",
    range(500, 600): "🌧️",
    range(600, 700): "❄️",
    range(700, 800): "🌫️",
    range(800, 801): "☀️",
    range(801, 900): "☁️",
}


def wx_emoji(code: int) -> str:
    for rng, icon in WX_EMOJI.items():
        if code in rng:
            return icon
    return "🌡️"


# ── Récupération ─────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
@st.cache_data(ttl=600, show_spinner=False)
def fetch_current_weather(city: str, units: str = "metric") -> Optional[dict]:
    """Météo actuelle d'une ville."""
    api_key = st.secrets.get("OPENWEATHER_KEY", "")
    if not api_key:
        return _mock_weather(city)
    try:
        r = requests.get(f"{BASE_URL}/weather", params={
            "q": city, "appid": OPENWEATHER_API_KEY,
            "units": units, "lang": "fr",
        }, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"Météo {city}: {e}")
        return _mock_weather(city)


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_forecast(city: str, units: str = "metric") -> Optional[dict]:
    """Prévisions 5 jours / 3h."""
    if OPENWEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY":
        return _mock_forecast(city)
    try:
        r = requests.get(f"{BASE_URL}/forecast", params={
            "q": city, "appid": OPENWEATHER_API_KEY,
            "units": units, "lang": "fr", "cnt": 40,
        }, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return _mock_forecast(city)


# ── Données simulées (mode démo sans clé API) ────────────────

def _mock_weather(city: str) -> dict:
    """Données météo simulées réalistes par ville."""
    temps = {
        "Rabat": (22, 65, 12), "Paris": (15, 72, 8),
        "London": (13, 80, 10), "New York": (18, 60, 15),
        "Dubai": (36, 40, 5), "Tokyo": (20, 70, 12),
        "Sydney": (25, 55, 18),
    }
    temp, hum, wind = temps.get(city, (20, 65, 10))
    codes = {"Rabat": 800, "Paris": 803, "London": 804,
             "New York": 801, "Dubai": 800, "Tokyo": 802, "Sydney": 800}
    code = codes.get(city, 800)
    return {
        "name":  city,
        "main":  {"temp": temp, "feels_like": temp - 2, "humidity": hum,
                   "pressure": 1013, "temp_min": temp - 3, "temp_max": temp + 4},
        "weather": [{"id": code, "description": "partiellement nuageux", "icon": "02d"}],
        "wind":  {"speed": wind / 3.6},
        "visibility": 10000,
        "sys":   {"country": "" },
        "_demo": True,
    }


def _mock_forecast(city: str) -> dict:
    """Prévisions simulées pour démo."""
    import random
    random.seed(hash(city) % 1000)
    base_temp = {"Rabat": 22, "Paris": 15, "London": 13,
                 "New York": 18, "Dubai": 36}.get(city, 20)
    items = []
    now = datetime.utcnow()
    for i in range(40):
        dt  = now + timedelta(hours=i * 3)
        tmp = base_temp + random.uniform(-4, 4)
        items.append({
            "dt_txt":  dt.strftime("%Y-%m-%d %H:%M:%S"),
            "main":    {"temp": tmp, "humidity": random.randint(50, 85)},
            "weather": [{"id": 800, "description": "clair", "icon": "01d"}],
            "wind":    {"speed": random.uniform(2, 8)},
        })
    return {"list": items, "_demo": True}


# ── Parsing ──────────────────────────────────────────────────

def parse_forecast_df(forecast_data: dict) -> pd.DataFrame:
    """Convertit les prévisions en DataFrame propre."""
    if not forecast_data or "list" not in forecast_data:
        return pd.DataFrame()
    rows = []
    for item in forecast_data["list"]:
        rows.append({
            "datetime":    pd.to_datetime(item["dt_txt"]),
            "temp":        item["main"]["temp"],
            "humidity":    item["main"]["humidity"],
            "wind_speed":  item["wind"]["speed"] * 3.6,  # m/s → km/h
            "description": item["weather"][0]["description"],
            "icon":        item["weather"][0]["icon"],
            "wx_code":     item["weather"][0]["id"],
        })
    return pd.DataFrame(rows)


# ── Graphiques ───────────────────────────────────────────────

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(showgrid=False, zeroline=False, color="#64748b"),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
               zeroline=False, color="#64748b"),
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="#334155",
                    font=dict(color="#e2e8f0")),
)


def chart_temp_forecast(df: pd.DataFrame, city: str) -> go.Figure:
    """Courbe de température + humidité (5 jours)."""
    fig = go.Figure()

    # Aire température
    fig.add_trace(go.Scatter(
        x=df["datetime"], y=df["temp"],
        name="Température (°C)", mode="lines",
        fill="tozeroy", fillcolor="rgba(0,212,255,0.08)",
        line=dict(color=COLOR_UP, width=2.5),
        hovertemplate="<b>%{y:.1f}°C</b><br>%{x}<extra></extra>",
    ))

    # Humidité (axe secondaire)
    fig.add_trace(go.Scatter(
        x=df["datetime"], y=df["humidity"],
        name="Humidité (%)", mode="lines",
        line=dict(color=ACCENT, width=1.5, dash="dot"),
        yaxis="y2",
        hovertemplate="<b>%{y}%%</b><br>%{x}<extra></extra>",
    ))

    layout = {**CHART_LAYOUT,
               "title":  {"text": f"Prévisions 5 jours — {city}",
                           "font": {"color": "#e2e8f0", "size": 13}},
               "yaxis2": {"overlaying": "y", "side": "right",
                           "showgrid": False, "color": "#64748b",
                           "title": "Hum. (%)", "range": [0, 120]},
               "yaxis":  {**CHART_LAYOUT["yaxis"], "title": "Temp (°C)"},
               "legend": {"bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
                           "font": {"color": "#94a3b8", "size": 10}},
               "hovermode": "x unified"}
    fig.update_layout(**layout, height=300)
    return fig


def chart_wind_speed(df: pd.DataFrame, city: str) -> go.Figure:
    """Graphique vitesse du vent."""
    # Agréger par jour
    daily = df.groupby(df["datetime"].dt.date)["wind_speed"].mean().reset_index()
    daily.columns = ["date", "wind_speed"]

    fig = go.Figure(go.Bar(
        x=daily["date"], y=daily["wind_speed"],
        marker_color=COLOR_UP, opacity=0.8,
        hovertemplate="<b>%{y:.1f} km/h</b><br>%{x}<extra></extra>",
        name="Vent moy.",
    ))
    layout = {**CHART_LAYOUT,
               "title": {"text": f"Vent moyen — {city}",
                          "font": {"color": "#e2e8f0", "size": 13}},
               "yaxis": {**CHART_LAYOUT["yaxis"], "title": "km/h"}}
    fig.update_layout(**layout, height=250)
    return fig


# ── Composants UI ────────────────────────────────────────────

def render_weather_card(data: dict) -> None:
    """Carte météo actuelle stylisée."""
    if not data:
        st.warning("Données météo indisponibles.")
        return

    main    = data["main"]
    weather = data["weather"][0]
    wind    = data["wind"]
    demo    = data.get("_demo", False)
    emoji   = wx_emoji(weather["id"])

    demo_badge = """
    <span style="background:rgba(245,158,11,0.15); color:#f59e0b;
                 padding:2px 8px; border-radius:8px; font-size:0.68rem;
                 font-weight:700; letter-spacing:0.05em; margin-left:6px;">
        DÉMO
    </span>""" if demo else ""

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(17,24,39,0.95), rgba(30,41,59,0.8));
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 20px 22px;
        text-align: center;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    ">
        <p style="margin:0; font-size:0.75rem; color:#64748b; letter-spacing:0.1em;
                   text-transform:uppercase; font-weight:600;">
            {data['name']}, {data['sys']['country']}{demo_badge}
        </p>
        <div style="font-size:3.5rem; margin:8px 0 4px;">{emoji}</div>
        <p style="margin:0; font-size:3rem; font-weight:800; color:#e2e8f0; line-height:1;">
            {main['temp']:.0f}°<span style="font-size:1.4rem; color:#64748b;">C</span>
        </p>
        <p style="margin:8px 0 0; font-size:0.85rem; color:#94a3b8; text-transform:capitalize;">
            {weather['description']}
        </p>
        <p style="margin:4px 0 0; font-size:0.78rem; color:#475569;">
            Ressenti {main['feels_like']:.0f}°C
        </p>
        <div style="display:flex; justify-content:space-around; margin-top:16px;
                    padding-top:14px; border-top:1px solid rgba(255,255,255,0.06);">
            <div style="text-align:center;">
                <p style="margin:0; font-size:0.68rem; color:#64748b;">Humidité</p>
                <p style="margin:2px 0 0; font-size:0.95rem; color:#e2e8f0; font-weight:600;">
                    {main['humidity']}%
                </p>
            </div>
            <div style="text-align:center;">
                <p style="margin:0; font-size:0.68rem; color:#64748b;">Vent</p>
                <p style="margin:2px 0 0; font-size:0.95rem; color:#e2e8f0; font-weight:600;">
                    {wind['speed']*3.6:.0f} km/h
                </p>
            </div>
            <div style="text-align:center;">
                <p style="margin:0; font-size:0.68rem; color:#64748b;">Pression</p>
                <p style="margin:2px 0 0; font-size:0.95rem; color:#e2e8f0; font-weight:600;">
                    {main['pressure']} hPa
                </p>
            </div>
            <div style="text-align:center;">
                <p style="margin:0; font-size:0.68rem; color:#64748b;">Visibilité</p>
                <p style="margin:2px 0 0; font-size:0.95rem; color:#e2e8f0; font-weight:600;">
                    {data.get('visibility', 10000)//1000} km
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_multi_city_weather(cities: List[str]) -> None:
    """Affiche un tableau comparatif multi-villes."""
    cols = st.columns(len(cities))
    for i, city in enumerate(cities):
        with cols[i]:
            data = fetch_current_weather(city)
            if data:
                render_weather_card(data)
