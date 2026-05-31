# ============================================================
#  app.py — SmartDash Pro · Tableau de bord temps réel
#  Stack : Streamlit + yfinance + OpenWeatherMap
# ============================================================

import streamlit as st
import time
from datetime import datetime

# ── Config page (doit être le 1er appel Streamlit) ──────────
st.set_page_config(
    page_title="SmartDash Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports internes ─────────────────────────────────────────
from config import (
    DEFAULT_TICKERS, ALL_TICKERS, DEFAULT_CITIES,
    REFRESH_INTERVALS, HIST_PERIODS, OHLC_INTERVALS,
)
from utils.helpers import (
    now_morocco, market_status, section_header,
)
from components.finance import (
    fetch_quote, fetch_history, fetch_multi, fetch_batch_quotes,
    render_ticker_cards, render_market_summary, render_stats_panel,
    chart_candlestick, chart_line_comparison, chart_rsi,
    chart_macd, chart_returns_dist, chart_heatmap_correlation,
)
from components.weather import (
    fetch_current_weather, fetch_forecast,
    parse_forecast_df, render_weather_card, render_multi_city_weather,
    chart_temp_forecast, chart_wind_speed,
)


# ════════════════════════════════════════════════════════════
#  CSS GLOBAL — thème dark premium
# ════════════════════════════════════════════════════════════

st.markdown("""
<style>
:root {
    --bg:      #0a0f1e;
    --card:    rgba(17,24,39,0.9);
    --border:  rgba(255,255,255,0.07);
    --accent:  #00d4ff;
    --purple:  #7c3aed;
    --text:    #e2e8f0;
    --muted:   #64748b;
}
[data-testid="stSidebar"] {
    background: rgba(10,15,30,0.98) !important;
    border-right: 1px solid var(--border) !important;
}
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: #0a0f1e; }
.block-container { padding: 1.5rem 2rem 2rem !important; }
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid var(--border) !important;
    gap: 4px;
}
[data-testid="stTabs"] button[role="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 8px 18px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    border: none !important;
    transition: all .2s;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: rgba(0,212,255,0.05) !important;
}
[data-testid="stSelectbox"] div,
[data-testid="stMultiSelect"] div {
    background: rgba(17,24,39,0.8) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
}
hr { border-color: var(--border) !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
.js-plotly-plot .plotly .bg { fill: transparent !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="padding: 8px 0 20px 0; text-align:center;">
        <p style="margin:0; font-size:1.5rem; font-weight:900; color:#e2e8f0;
                   letter-spacing:-0.03em;">
            📊 Smart<span style="color:#00d4ff;">Dash</span> Pro
        </p>
        <p style="margin:4px 0 0; font-size:0.72rem; color:#64748b; letter-spacing:0.08em;">
            TABLEAU DE BORD TEMPS RÉEL
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Statut marchés ──────────────────────────────────────
    st.markdown("**🌍 Statut des marchés**")
    for market, is_open in market_status().items():
        dot   = "🟢" if is_open else "🔴"
        label = "Ouvert" if is_open else "Fermé"
        st.markdown(
            f"<small style='color:#94a3b8;'>{dot} {market} — {label}</small>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Sélection groupe tickers ────────────────────────────
    st.markdown("**📈 Univers actions**")
    selected_group = st.selectbox(
        "Groupe", list(DEFAULT_TICKERS.keys()), label_visibility="collapsed"
    )
    default_tickers_for_group = DEFAULT_TICKERS[selected_group]

    selected_tickers = st.multiselect(
        "Tickers", ALL_TICKERS,
        default=default_tickers_for_group[:3],
        help="Sélectionnez jusqu'à 8 actifs",
    )
    if len(selected_tickers) > 8:
        st.warning("⚠️ Maximum 8 actifs recommandé.")
        selected_tickers = selected_tickers[:8]

    custom_ticker = st.text_input(
        "➕ Ajouter un ticker", placeholder="ex: LVMH.PA, MC.PA…"
    )
    if custom_ticker:
        ticker_clean = custom_ticker.strip().upper()
        if ticker_clean not in selected_tickers:
            selected_tickers.append(ticker_clean)

    st.divider()

    # ── Ticker principal ────────────────────────────────────
    st.markdown("**🔍 Analyse principale**")
    main_ticker = st.selectbox(
        "Ticker", selected_tickers or ["AAPL"],
        label_visibility="collapsed",
    )

    period_label   = st.select_slider(
        "Période", list(HIST_PERIODS.keys()), value="3 mois"
    )
    interval_label = st.selectbox(
        "Intervalle", list(OHLC_INTERVALS.keys()), index=1
    )
    period_code   = HIST_PERIODS[period_label]
    interval_code = OHLC_INTERVALS[interval_label]

    st.divider()

    # ── Météo ───────────────────────────────────────────────
    st.markdown("**🌤️ Villes météo**")
    selected_cities = st.multiselect(
        "Villes", DEFAULT_CITIES + ["Casablanca", "Marrakech", "Fès", "Tanger", "Agadir"],
        default=DEFAULT_CITIES[:3],
        label_visibility="collapsed",
    )

    st.divider()

    # ── Auto-refresh ────────────────────────────────────────
    st.markdown("**⏱️ Actualisation auto**")
    auto_refresh  = st.toggle("Activer", value=False)
    refresh_label = st.select_slider(
        "Intervalle", list(REFRESH_INTERVALS.keys()), value="30 s",
        disabled=not auto_refresh,
    )
    refresh_seconds = REFRESH_INTERVALS[refresh_label]

    st.divider()

    # ── Options graphiques ──────────────────────────────────
    st.markdown("**⚙️ Options graphiques**")
    show_volume    = st.checkbox("Volume",    value=True)
    show_bollinger = st.checkbox("Bollinger", value=False)
    normalize_cmp  = st.checkbox("Base 100",  value=True,
                                  help="Normaliser la comparaison multi-actifs")

    st.divider()

    now = now_morocco()
    st.markdown(        
        f"<small style='color:#475569;'>🕐 {now.strftime('%d/%m/%Y %H:%M:%S')} (Rabat)</small>",
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════
#  EN-TÊTE PRINCIPAL
# ════════════════════════════════════════════════════════════

col_title, col_refresh = st.columns([5, 1])
with col_title:
    st.markdown("""
    <h1 style="margin:0; font-size:1.8rem; font-weight:900; color:#e2e8f0;">
        📊 Smart<span style="color:#00d4ff;">Dash</span> Pro
        <span style="font-size:0.9rem; font-weight:400; color:#64748b;
                      letter-spacing:0.04em; margin-left:12px;">
            Marchés financiers & Météo — Temps réel
        </span>
    </h1>
    """, unsafe_allow_html=True)

with col_refresh:
    if st.button("🔄 Actualiser", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  CHARGEMENT DONNÉES
# ════════════════════════════════════════════════════════════

tickers_to_load = selected_tickers if selected_tickers else ["AAPL", "MSFT", "GOOGL"]

with st.spinner("⏳ Chargement des données…"):
    all_quotes = fetch_batch_quotes(tickers_to_load)
    main_hist  = fetch_history(main_ticker, period_code, interval_code)
    multi_data = fetch_multi(tickers_to_load, period_code)


# ════════════════════════════════════════════════════════════
#  ONGLETS PRINCIPAUX
# ════════════════════════════════════════════════════════════

tab_market, tab_analyse, tab_compare, tab_weather, tab_about = st.tabs([
    "🏦 Marché",
    "📈 Analyse technique",
    "⚖️ Comparaison",
    "🌤️ Météo",
    "ℹ️ À propos",
])


# ════════════════════════════════════════════════════════════
#  ONGLET 1 — MARCHÉ
# ════════════════════════════════════════════════════════════

with tab_market:

    section_header("📊 Résumé du marché",
                   f"Portefeuille : {', '.join(tickers_to_load)}")
    render_market_summary(all_quotes)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    section_header("💹 Cours en temps réel")
    if all_quotes:
        render_ticker_cards(all_quotes, cols_count=min(4, len(all_quotes)))
    else:
        st.warning("Aucune donnée disponible. Vérifiez votre connexion.")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    section_header("📋 Tableau récapitulatif")
    if all_quotes:
        import pandas as pd
        from utils.helpers import fmt_currency, fmt_pct, fmt_volume

        df_table = pd.DataFrame([{
            "Ticker":   q["ticker"],
            "Prix ($)": round(q["price"], 2),
            "Var. ($)": round(q["change"], 2),
            "Var. (%)": round(q["change_pct"], 2),
            "Volume":   fmt_volume(q.get("volume", 0)),
            "Mkt Cap":  fmt_currency(q.get("market_cap") or 0),
        } for q in all_quotes])

        def style_row(row):
            color = "color: #00d4ff" if row["Var. (%)"] > 0 else "color: #ff4d6d"
            return ["", "", color, color, "", ""]

        st.dataframe(
            df_table.style.apply(style_row, axis=1),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_header(f"📉 Graphique principal — {main_ticker}")

    if not main_hist.empty:
        fig = chart_candlestick(main_hist, main_ticker,
                                show_volume, show_bollinger)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Impossible de charger l'historique pour {main_ticker}.")


# ════════════════════════════════════════════════════════════
#  ONGLET 2 — ANALYSE TECHNIQUE
# ════════════════════════════════════════════════════════════

with tab_analyse:

    section_header(f"📡 Analyse technique — {main_ticker}",
                   f"Période : {period_label} | Intervalle : {interval_label}")

    if main_hist.empty:
        st.error("Données insuffisantes pour l'analyse technique.")
    else:
        render_stats_panel(main_hist, main_ticker)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        col_rsi, col_macd = st.columns(2)
        with col_rsi:
            if len(main_hist) >= 14:
                st.plotly_chart(chart_rsi(main_hist, main_ticker),
                                use_container_width=True)
            else:
                st.info("Données insuffisantes pour le RSI (min. 14 périodes).")

        with col_macd:
            if len(main_hist) >= 26:
                st.plotly_chart(chart_macd(main_hist, main_ticker),
                                use_container_width=True)
            else:
                st.info("Données insuffisantes pour le MACD (min. 26 périodes).")

        section_header("📊 Distribution des rendements journaliers")
        if len(main_hist) >= 30:
            st.plotly_chart(chart_returns_dist(main_hist, main_ticker),
                            use_container_width=True)

        section_header("📋 Données OHLCV récentes")
        ohlcv = main_hist[["Open", "High", "Low", "Close", "Volume"]].tail(20).copy()
        # ── CORRECTION BUG 2 : tz_localize avant strftime ───
        if ohlcv.index.tz is not None:
            ohlcv.index = ohlcv.index.tz_localize(None)
        ohlcv.index = ohlcv.index.strftime("%Y-%m-%d %H:%M")
        ohlcv = ohlcv.round(2)
        st.dataframe(ohlcv, use_container_width=True)


# ════════════════════════════════════════════════════════════
#  ONGLET 3 — COMPARAISON
# ════════════════════════════════════════════════════════════

with tab_compare:

    section_header("⚖️ Comparaison multi-actifs",
                   f"Période : {period_label} — {len(tickers_to_load)} actifs")

    if len(tickers_to_load) < 2:
        st.info("Sélectionnez au moins 2 actifs dans la barre latérale.")
    elif multi_data.empty:
        st.error("Données de comparaison indisponibles.")
    else:
        fig_cmp = chart_line_comparison(multi_data, normalize=normalize_cmp)
        st.plotly_chart(fig_cmp, use_container_width=True)

        if len(tickers_to_load) >= 2:
            section_header("🔗 Corrélations")
            col_heat, col_info = st.columns([3, 1])
            with col_heat:
                fig_corr = chart_heatmap_correlation(multi_data)
                st.plotly_chart(fig_corr, use_container_width=True)
            with col_info:
                st.markdown("""
                <div style="background:rgba(17,24,39,0.8);
                             border:1px solid rgba(255,255,255,0.07);
                             border-radius:12px; padding:16px;
                             font-size:0.82rem; color:#94a3b8;">
                    <p style="margin:0 0 12px; color:#e2e8f0; font-weight:700;">
                        📖 Lecture
                    </p>
                    <p style="margin:0 0 8px;">
                        <span style="color:#00d4ff; font-weight:700;">+1</span>
                        → Actifs parfaitement corrélés
                    </p>
                    <p style="margin:0 0 8px;">
                        <span style="color:#94a3b8; font-weight:700;">0</span>
                        → Aucune corrélation
                    </p>
                    <p style="margin:0;">
                        <span style="color:#ff4d6d; font-weight:700;">-1</span>
                        → Corrélation inverse
                    </p>
                    <hr style="border-color:rgba(255,255,255,0.07); margin:12px 0;">
                    <p style="margin:0; font-size:0.75rem; color:#475569;">
                        Calculé sur les rendements journaliers.
                    </p>
                </div>
                """, unsafe_allow_html=True)

        section_header("📈 Performance cumulée (%)")
        import pandas as pd
        import numpy as np
        from utils.helpers import (compute_returns, compute_sharpe,
                                   compute_volatility, compute_max_drawdown)

        perf_rows = []
        for ticker in tickers_to_load:
            if ticker in multi_data.columns:
                s = multi_data[ticker].dropna()
                if len(s) < 5:
                    continue
                ret   = compute_returns(s).dropna()
                total = (s.iloc[-1] / s.iloc[0] - 1) * 100
                perf_rows.append({
                    "Ticker":        ticker,
                    "Perf. (%)":     round(total, 2),
                    "Vol. ann. (%)": round(compute_volatility(ret), 1),
                    "Sharpe":        round(compute_sharpe(ret), 2),
                    "Max DD (%)":    round(compute_max_drawdown(s), 1),
                    "Dernier":       round(float(s.iloc[-1]), 2),
                })

        if perf_rows:
            df_perf = pd.DataFrame(perf_rows).sort_values("Perf. (%)",
                                                           ascending=False)
            st.dataframe(df_perf, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════
#  ONGLET 4 — MÉTÉO
# ════════════════════════════════════════════════════════════

with tab_weather:

    section_header("🌤️ Météo en temps réel",
                   "Données OpenWeatherMap (mode démo si aucune clé API)")

    cities_to_show = selected_cities if selected_cities else ["Rabat", "Paris"]

    n            = len(cities_to_show)
    cols_per_row = min(n, 3)
    rows         = [cities_to_show[i:i + cols_per_row]
                    for i in range(0, n, cols_per_row)]

    for row in rows:
        cols = st.columns(len(row))
        for i, city in enumerate(row):
            with cols[i]:
                data = fetch_current_weather(city)
                if data:
                    render_weather_card(data)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    primary_city = cities_to_show[0]
    section_header(f"📅 Prévisions 5 jours — {primary_city}")

    fc_data = fetch_forecast(primary_city)
    if fc_data:
        fc_df = parse_forecast_df(fc_data)
        if not fc_df.empty:
            st.plotly_chart(
                chart_temp_forecast(fc_df, primary_city),
                use_container_width=True,
            )

            col_wind1, col_wind2 = st.columns(2)
            with col_wind1:
                st.plotly_chart(
                    chart_wind_speed(fc_df, primary_city),
                    use_container_width=True,
                )
            with col_wind2:
                daily_fc = (
                    fc_df.set_index("datetime")
                         .resample("D")[["temp", "humidity", "wind_speed"]]
                         .agg({"temp": ["min", "max"],
                               "humidity": "mean",
                               "wind_speed": "mean"})
                         .round(1)
                )
                daily_fc.columns = ["T° min", "T° max",
                                    "Hum. moy. (%)", "Vent (km/h)"]
                daily_fc.index = daily_fc.index.strftime("%a %d/%m")
                st.dataframe(daily_fc, use_container_width=True)

    if len(cities_to_show) > 1:
        section_header("🌍 Comparaison multi-villes")
        import pandas as pd
        wx_rows = []
        for city in cities_to_show:
            d = fetch_current_weather(city)
            if d:
                wx_rows.append({
                    "Ville":        f"{d['name']}, {d['sys']['country']}",
                    "Temp (°C)":    d["main"]["temp"],
                    "Ressenti":     d["main"]["feels_like"],
                    "Humidité (%)": d["main"]["humidity"],
                    "Vent (km/h)":  round(d["wind"]["speed"] * 3.6, 1),
                    "Conditions":   d["weather"][0]["description"].title(),
                })
        if wx_rows:
            st.dataframe(
                pd.DataFrame(wx_rows),
                use_container_width=True,
                hide_index=True,
            )


# ════════════════════════════════════════════════════════════
#  ONGLET 5 — À PROPOS
# ════════════════════════════════════════════════════════════

with tab_about:
    st.markdown("""
    <div style="max-width:720px; margin:0 auto;">

    <h2 style="color:#e2e8f0; font-weight:800; margin-bottom:4px;">
        📊 SmartDash Pro
    </h2>
    <p style="color:#64748b; font-size:0.85rem; margin-bottom:24px;">
        Tableau de bord de données financières et météo, temps réel
    </p>

    <div style="background:rgba(17,24,39,0.9); border:1px solid rgba(255,255,255,0.07);
                border-radius:14px; padding:24px; margin-bottom:16px;">
        <h4 style="color:#00d4ff; margin:0 0 16px;">⚙️ Stack technique</h4>
        <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
            <td style="padding:8px 0; color:#94a3b8; width:40%;">Framework</td>
            <td style="color:#e2e8f0; font-weight:600;">Streamlit 1.x</td>
        </tr>
        <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
            <td style="padding:8px 0; color:#94a3b8;">Finance API</td>
            <td style="color:#e2e8f0; font-weight:600;">yfinance (Yahoo Finance) — gratuit, sans clé</td>
        </tr>
        <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
            <td style="padding:8px 0; color:#94a3b8;">Météo API</td>
            <td style="color:#e2e8f0; font-weight:600;">OpenWeatherMap REST API</td>
        </tr>
        <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
            <td style="padding:8px 0; color:#94a3b8;">Visualisation</td>
            <td style="color:#e2e8f0; font-weight:600;">Plotly (Candlestick, Heatmap, Area…)</td>
        </tr>
        <tr>
            <td style="padding:8px 0; color:#94a3b8;">Données</td>
            <td style="color:#e2e8f0; font-weight:600;">Pandas, NumPy</td>
        </tr>
        </table>
    </div>

    <div style="background:rgba(17,24,39,0.9); border:1px solid rgba(255,255,255,0.07);
                border-radius:14px; padding:24px; margin-bottom:16px;">
        <h4 style="color:#7c3aed; margin:0 0 16px;">✨ Fonctionnalités</h4>
        <ul style="color:#94a3b8; font-size:0.85rem; line-height:1.9;
                   margin:0; padding-left:18px;">
            <li>Cours boursiers temps réel (actions, ETFs, crypto)</li>
            <li>Chandeliers japonais OHLCV avec volume</li>
            <li>Indicateurs techniques : RSI, MACD, Bandes de Bollinger</li>
            <li>Métriques risque : Sharpe, Volatilité, Max Drawdown</li>
            <li>Comparaison multi-actifs base 100 + matrice corrélation</li>
            <li>Météo temps réel multi-villes + prévisions 5 jours</li>
            <li>Auto-refresh configurable</li>
        </ul>
    </div>

    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  AUTO-REFRESH
# ════════════════════════════════════════════════════════════

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()