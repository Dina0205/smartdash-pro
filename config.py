# ============================================================
#  config.py — Configuration centrale SmartDash Pro
# ============================================================

# ── Clés API (remplacer par vos vraies clés) ────────────────
OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"   # https://openweathermap.org/api
# yfinance n'exige pas de clé API

# ── Univers d'actions par défaut ────────────────────────────
DEFAULT_TICKERS = {
    "🇺🇸 US Tech":    ["AAPL", "MSFT", "GOOGL", "NVDA", "META"],
    "🇺🇸 US Finance": ["JPM", "GS", "BAC", "MS", "WFC"],
    "🌍 Global":      ["TSLA", "AMZN", "NFLX", "BABA", "TSM"],
    "📈 ETFs":        ["SPY", "QQQ", "IWM", "VTI", "EFA"],
    "🪙 Crypto":      ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD"],
}

ALL_TICKERS = [t for group in DEFAULT_TICKERS.values() for t in group]

# ── Villes météo par défaut ─────────────────────────────────
DEFAULT_CITIES = ["Rabat", "Paris", "London", "New York", "Dubai"]

# ── Intervalles de rafraîchissement (secondes) ─────────────
REFRESH_INTERVALS = {
    "5 s":  5,
    "15 s": 15,
    "30 s": 30,
    "1 min": 60,
    "5 min": 300,
}

# ── Périodes historiques ────────────────────────────────────
HIST_PERIODS = {
    "1 semaine":  "7d",
    "1 mois":     "1mo",
    "3 mois":     "3mo",
    "6 mois":     "6mo",
    "1 an":       "1y",
    "5 ans":      "5y",
}

# ── Intervalles OHLC ────────────────────────────────────────
OHLC_INTERVALS = {
    "1 h":   "1h",
    "1 jour": "1d",
    "1 sem": "1wk",
    "1 mois": "1mo",
}

# ── Palettes de couleurs ────────────────────────────────────
COLOR_UP    = "#00d4ff"
COLOR_DOWN  = "#ff4d6d"
COLOR_NEUT  = "#94a3b8"
ACCENT      = "#7c3aed"
BG_CARD     = "rgba(17,24,39,0.85)"

CHART_COLORS = [
    "#00d4ff", "#7c3aed", "#f59e0b",
    "#10b981", "#ff4d6d", "#f97316",
    "#8b5cf6", "#06b6d4",
]
