"""Data loading and computation utilities for AISESA Energy Models Africa.

Source of truth: data/enermod.db (SQLite), regenerated from Excel via build_database.py.
Backward-compatible with the existing pages: rebuilds the legacy `countries` and
`power_pool` text columns from the junction tables, and aliases renamed columns
(study_id->id, frequency_of_use->frequency, author_origin->developer_origin).
"""

import re
import sqlite3
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent / "data"
DB = BASE / "enermod.db"

ISO2_TO_ISO3 = {
    "DZ": "DZA", "AO": "AGO", "BJ": "BEN", "BW": "BWA", "BF": "BFA",
    "BI": "BDI", "CV": "CPV", "CM": "CMR", "CF": "CAF", "TD": "TCD",
    "KM": "COM", "CD": "COD", "CG": "COG", "DJ": "DJI", "EG": "EGY",
    "GQ": "GNQ", "ER": "ERI", "SZ": "SWZ", "ET": "ETH", "GA": "GAB",
    "GM": "GMB", "GH": "GHA", "GN": "GIN", "GW": "GNB", "CI": "CIV",
    "KE": "KEN", "LS": "LSO", "LR": "LBR", "LY": "LBY", "MG": "MDG",
    "MW": "MWI", "ML": "MLI", "MR": "MRT", "MU": "MUS", "MA": "MAR",
    "MZ": "MOZ", "NA": "NAM", "NE": "NER", "NG": "NGA", "RW": "RWA",
    "ST": "STP", "SN": "SEN", "SC": "SYC", "SL": "SLE", "SO": "SOM",
    "ZA": "ZAF", "SS": "SSD", "SD": "SDN", "TZ": "TZA", "TG": "TGO",
    "TN": "TUN", "UG": "UGA", "ZM": "ZMB", "ZW": "ZWE", "RE": "REU",
}


def _conn():
    return sqlite3.connect(DB)


def db_cache_token() -> int:
    """Return a filesystem stamp that changes when the SQLite file changes."""
    try:
        return DB.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


# Niveaux d'extraction : full (complet) / light (partiel) / narrative (texte seul)
EXTRACTION_LEVELS = ["full", "light", "narrative", "unspecified"]
_EXTRACT_MAP = {"all": "full", "full": "full", "complete": "full",
                "light": "light", "partial": "light",
                "narrative": "narrative", "narrative_only": "narrative",
                "": "unspecified", "nan": "unspecified", "none": "unspecified"}


def _norm_level(v):
    k = str(v).strip().lower()
    return _EXTRACT_MAP.get(k, k or "unspecified")


def coverage(studies: pd.DataFrame, col: str, positive=("yes",)) -> dict:
    """Couverture d'une dimension en ne comptant QUE les études évaluées.

    Une cellule vide = 'non évalué' (exclue du dénominateur), jamais 'non'.
    Retourne positive (n), assessed (dénominateur), total, pct (sur assessed).
    """
    if col not in studies.columns:
        return {"positive": 0, "assessed": 0, "total": len(studies), "pct": 0}
    s = studies[col].astype(str).str.strip().str.lower()
    assessed = s[(s != "") & (s != "nan") & (s != "unknown") & (s != "not_stated")]
    pos = int(assessed.isin([p.lower() for p in positive]).sum())
    n = int(len(assessed))
    return {"positive": pos, "assessed": n, "total": len(s),
            "pct": round(pos / n * 100) if n else 0}


@pd.api.extensions.register_dataframe_accessor("_")
class _Dummy:
    pass


def load_countries() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql("SELECT * FROM countries", con)
    df["electrification_rate"] = pd.to_numeric(df["electrification_rate"], errors="coerce").fillna(0.0)
    for c in ("nb_models_applied", "nb_models_national"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    if "iso3" not in df.columns or df["iso3"].isna().any() or (df["iso3"] == "").any():
        df["iso3"] = df["iso_code"].map(ISO2_TO_ISO3)
    return df


def load_studies() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql("SELECT * FROM studies", con)
        cj = pd.read_sql(
            "SELECT study_id, GROUP_CONCAT(iso_code, ', ') AS countries "
            "FROM study_countries GROUP BY study_id", con)
        pj = pd.read_sql(
            "SELECT study_id, GROUP_CONCAT(pool_code, ',') AS power_pool "
            "FROM study_pools GROUP BY study_id", con)

    # Rebuild legacy text columns from the junction tables (authoritative)
    df = df.drop(columns=[c for c in ("countries", "power_pool") if c in df.columns])
    df = df.merge(cj, on="study_id", how="left").merge(pj, on="study_id", how="left")
    df["countries"] = df["countries"].fillna("")
    df["power_pool"] = df["power_pool"].fillna("")

    # Backward-compatible aliases for the pages
    df["id"] = pd.to_numeric(df["study_id"], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    if "extraction_level" in df.columns:
        df["extraction_level"] = df["extraction_level"].map(_norm_level)
    else:
        df["extraction_level"] = "unspecified"
    if "frequency_of_use" in df.columns:
        df["frequency"] = df["frequency_of_use"]
    if "author_origin" in df.columns:
        df["developer_origin"] = df["author_origin"]
    if "link_doi" in df.columns:
        df["link"] = df["link_doi"]
    return df


def load_tools() -> pd.DataFrame:
    with _conn() as con:
        df = pd.read_sql("SELECT * FROM tools", con)
    df["cost_usd"] = (
        df["cost_usd"].astype(str).str.replace("?", "", regex=False)
        .str.replace(",", "", regex=False).str.strip()
    )
    df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce").fillna(0)
    df["nb_studies_in_inventory"] = pd.to_numeric(
        df["nb_studies_in_inventory"], errors="coerce").fillna(0).astype(int)
    return df


def load_power_pools() -> pd.DataFrame:
    with _conn() as con:
        return pd.read_sql("SELECT * FROM power_pools", con)


def get_country_studies(studies: pd.DataFrame, iso: str) -> pd.DataFrame:
    """Return studies that cover a given ISO-2 country code."""
    pattern = r"\b" + re.escape(iso) + r"\b"
    mask = studies["countries"].str.contains(pattern, regex=True, na=False)
    return studies[mask].copy()


def compute_gap_score(row) -> float:
    cap_map = {"yes": 2, "partial": 1, "no": 0}
    dat_map = {"good": 2, "moderate": 1, "poor": 0}
    feat = row.get("feature_ratio", 0)
    cap = cap_map.get(str(row.get("has_institutional_capacity", "no")), 0)
    dat = dat_map.get(str(row.get("data_availability", "poor")), 0)
    n = min(row.get("nb_models_applied", 0), 10)
    return round(
        (1 - feat) * 40
        + (1 - cap / 2) * 30
        + (1 - dat / 2) * 20
        + (1 - n / 10) * 10
    )


def compute_readiness(row) -> float:
    cap_pts = {"yes": 3, "partial": 1.5, "no": 0}.get(str(row.get("has_institutional_capacity", "no")), 0)
    dat_pts = {"good": 3, "moderate": 1.5, "poor": 0}.get(str(row.get("data_availability", "poor")), 0)
    ndc_pt = 1 if str(row.get("has_ndc", "no")) == "yes" else 0
    lts_pt = 1 if str(row.get("has_lts", "no")) == "yes" else 0
    elec_pts = min(float(row.get("electrification_rate", 0)) / 100 * 2, 2)
    return round(cap_pts + dat_pts + ndc_pt + lts_pt + elec_pts, 1)


def enrich_countries(countries: pd.DataFrame, studies: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, c in countries.iterrows():
        iso = c["iso_code"]
        cs = get_country_studies(studies, iso)
        n = len(cs)
        feats = 0
        if n > 0:
            feats = sum([
                cs["informal_economy"].eq("yes").any(),
                cs["biomass_charcoal"].eq("yes").any(),
                cs["power_reliability"].eq("yes").any(),
                cs["urbanization"].eq("yes").any(),
            ]) / 4
        row = c.to_dict()
        row["n_studies_actual"] = n
        row["feature_ratio"] = feats
        row["gap_score"] = compute_gap_score({**row})
        row["readiness_score"] = compute_readiness(row)
        rows.append(row)
    return pd.DataFrame(rows)
