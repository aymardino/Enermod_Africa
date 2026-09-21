"""Author-origin world map, shared by Home and Gap Analysis."""
import pandas as pd
import plotly.graph_objects as go
import pycountry
from collections import Counter
from utils.data import ISO2_TO_ISO3

def _build_world_maps():
    iso3, names = {}, {}
    for c in pycountry.countries:
        iso3[c.alpha_2] = c.alpha_3
        names[c.alpha_2] = getattr(c, "common_name", c.name)
    return iso3, names

_WORLD_ISO3, _WORLD_NAMES = _build_world_maps()
ISO2_TO_ISO3_WORLD = {**_WORLD_ISO3, **ISO2_TO_ISO3}
AFRICAN_ISOS = set(ISO2_TO_ISO3)

_GEO = dict(projection_type="natural earth", fitbounds=False,
            projection_rotation=dict(lon=0, lat=0, roll=0),
            showframe=False, showcoastlines=False,
            showland=True, landcolor="rgba(128,128,128,0.10)",
            showcountries=True, countrycolor="rgba(128,128,128,0.20)",
            bgcolor="rgba(0,0,0,0)")


def build_origin_map_df(studies: pd.DataFrame, countries: pd.DataFrame) -> pd.DataFrame:
    """One row per author country: n studies (counted once per study), group, name."""
    oc = Counter()
    for d in studies["developer_origin"].dropna():
        for code in {x.strip()[:2].upper()
                     for x in str(d).replace(",", ";").split(";") if x.strip()}:
            oc[code] += 1
    afr_name = dict(zip(countries["iso_code"], countries["country_name"]))
    rows = []
    for c, v in oc.items():
        if c not in ISO2_TO_ISO3_WORLD:
            continue
        rows.append({"iso3": ISO2_TO_ISO3_WORLD[c], "n": v,
                     "group": "African-based" if c in AFRICAN_ISOS else "Based outside Africa",
                     "name": afr_name.get(c) or _WORLD_NAMES.get(c, c)})
    return pd.DataFrame(rows, columns=["iso3", "n", "group", "name"])


def author_origin_choropleth(df: pd.DataFrame, height: int = 380) -> go.Figure:
    afr = df[df["group"] == "African-based"]
    non = df[df["group"] == "Based outside Africa"]
    fig = go.Figure()
    fig.add_choropleth(locations=afr["iso3"], z=afr["n"], text=afr["name"],
                       colorscale=[[0, "#CFE6D6"], [1, "#12402A"]],
                       marker_line_color="rgba(128,128,128,0.30)", marker_line_width=0.3,
                       colorbar=dict(title=dict(text="Africa", side="top"), x=1.00, y=0.76, len=0.46, thickness=8),
                       hovertemplate="<b>%{text}</b><br>%{z} studies<extra>African-based</extra>")
    fig.add_choropleth(locations=non["iso3"], z=non["n"], text=non["name"],
                       colorscale=[[0, "#F6D9BC"], [1, "#7E430E"]],
                       marker_line_color="rgba(128,128,128,0.30)", marker_line_width=0.3,
                       colorbar=dict(title=dict(text="Outside", side="top"), x=1.08, y=0.24, len=0.46, thickness=8),
                       hovertemplate="<b>%{text}</b><br>%{z} studies<extra>Outside Africa</extra>")
    fig.update_geos(**_GEO)
    fig.update_layout(height=height, margin={"t": 0, "b": 0, "l": 0, "r": 60},
                      paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)")
    return fig