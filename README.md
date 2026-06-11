# AISESA Energy Models Africa - Streamlit App

Decision-support platform for energy modelling across 54 African countries.

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

The app opens at https://enermod.africa/ in your browser.

## Structure

```
aisesa-streamlit/
├── app.py                  # Home page
├── pages/
│   ├── 1_Map.py            # Interactive choropleth map
│   ├── 2_Gap_Analysis.py   # Gap metrics & charts
│   ├── 3_Readiness.py      # Readiness scores & comparison
│   └── 4_Recommender.py    # Tool recommender
├── data/
│   ├── countries.csv
│   ├── studies.csv
│   ├── tools.csv
│   └── power_pools.csv
├── utils/
│   └── data.py             # Data loading & computation
├── assets/
│   └── aisesa_logo.png
├── .streamlit/
│   └── config.toml         # Theme (green branding)
└── requirements.txt
```

## No GeoJSON needed

The map uses Plotly's built-in choropleth with ISO-3 country codes — 
no external file download required.
