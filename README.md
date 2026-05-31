# 📊 SmartDash Pro — Tableau de bord temps réel

Dashboard financier et météo interactif construit avec **Streamlit**, **yfinance** et **OpenWeatherMap**.

---

## 🚀 Démarrage rapide

```bash
# 1. Cloner / extraire le projet
cd smartdash

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. (Optionnel) Clé API météo dans config.py
#    OPENWEATHER_API_KEY = "votre_cle_ici"

# 4. Lancer l'application
streamlit run app.py
```

L'app est accessible sur **http://localhost:8501**

---

## 🏗️ Architecture

```
smartdash/
│
├── app.py                  ← Point d'entrée principal
├── config.py               ← Configuration centralisée
├── requirements.txt        ← Dépendances Python
│
├── components/
│   ├── finance.py          ← Module finance (yfinance + graphiques)
│   └── weather.py          ← Module météo (OpenWeatherMap)
│
├── utils/
│   └── helpers.py          ← Formatage, indicateurs techniques, UI
│
└── .streamlit/
    └── config.toml         ← Thème dark custom
```

---

## ✨ Fonctionnalités

### 🏦 Onglet Marché
- Cours en temps réel : actions (NYSE, NASDAQ), ETFs, crypto
- Cards dynamiques avec variation colorée
- Tableau récapitulatif exportable
- Graphique chandeliers japonais (OHLCV)

### 📈 Onglet Analyse technique
| Indicateur | Détails |
|---|---|
| RSI (14) | Zones surachat/survente colorées |
| MACD | Ligne signal + histogramme |
| Bandes de Bollinger | Superposées sur le graphique prix |
| Sharpe Ratio | Annualisé, taux sans risque 5 % |
| Max Drawdown | Pire perte depuis un sommet |
| Volatilité | Annualisée sur les rendements log |
| Distribution | Histogramme + courbe normale |

### ⚖️ Onglet Comparaison
- Performance relative base 100 (multi-actifs)
- Matrice de corrélation interactive (Heatmap)
- Tableau de performance : Perf., Sharpe, Volatilité, Max DD

### 🌤️ Onglet Météo
- Météo actuelle multi-villes (temp., humidité, vent, pression)
- Prévisions 5 jours / 3h → courbe temp. + humidité
- Tableau synthèse journalier
- **Mode démo** si aucune clé API (données réalistes simulées)

---

## ⚙️ Configuration

### Clé API OpenWeatherMap
1. Créez un compte sur https://openweathermap.org/api
2. Générez une clé API gratuite (plan Free = 1000 req/jour)
3. Dans `config.py` :
```python
OPENWEATHER_API_KEY = "votre_clé_api_ici"
```

### Personnalisation
Tout est configurable dans `config.py` :
- Groupes de tickers par défaut
- Villes météo
- Intervalles de rafraîchissement
- Palettes de couleurs

---

## 🌐 Déploiement

### Streamlit Community Cloud (gratuit)
1. Push le projet sur GitHub
2. Connectez-vous sur https://streamlit.io/cloud
3. Déployez depuis votre dépôt
4. Ajoutez `OPENWEATHER_API_KEY` dans **Secrets** (Settings → Secrets)

```toml
# .streamlit/secrets.toml (ne pas committer !)
OPENWEATHER_API_KEY = "votre_clé"
```

Puis dans `config.py` :
```python
import streamlit as st
OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "YOUR_KEY")
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t smartdash .
docker run -p 8501:8501 smartdash
```

---

## 📦 Stack

| Composant | Technologie |
|---|---|
| Framework | Streamlit 1.32+ |
| Finance | yfinance (Yahoo Finance) |
| Météo | OpenWeatherMap REST API |
| Graphiques | Plotly (Candlestick, Heatmap, Scatter…) |
| Data | Pandas, NumPy |
| UI | HTML/CSS inline + thème dark custom |

---

## 📄 Licence
MIT — Libre d'utilisation et de modification.
