"""
African institutional authorship enrichment via OpenAlex.

For each study DOI, retrieves author affiliations from OpenAlex and computes:
  - composition: all_african | mixed | none   (institutional country codes)
  - leadership:  yes | no   (first or corresponding author at an African institution)
  - a flag for studies needing manual review (no DOI, not found, no affiliations)

Usage:
  pip install requests pandas openpyxl
  python openalex_authorship.py
Input : Models_Africa_v2.xlsm (sheet studies.csv, columns study_id + link_doi)
Output: authorship_openalex.csv
Run it at the final harmonization pass; ~1,000 DOIs take a few minutes.
"""

import re
import time
import requests
import pandas as pd

WORKBOOK = "Models_Africa_v2.xlsm"
OUTPUT = "authorship_openalex.csv"
MAILTO = "aymardplakoo@gmail.com"  # put your email (OpenAlex polite pool, faster)

AFRICAN_ISO2 = {
    "DZ","AO","BJ","BW","BF","BI","CV","CM","CF","TD","KM","CG","CD","CI","DJ",
    "EG","GQ","ER","SZ","ET","GA","GM","GH","GN","GW","KE","LS","LR","LY","MG",
    "MW","ML","MR","MU","MA","MZ","NA","NE","NG","RW","ST","SN","SC","SL","SO",
    "ZA","SS","SD","TZ","TG","TN","UG","ZM","ZW",
}


def norm_doi(x):
    if not isinstance(x, str) or not x.strip():
        return None
    x = x.strip().lower()
    x = re.sub(r"^https?://(dx\.)?doi\.org/", "", x)
    return x if x.startswith("10.") else None


def classify(work):
    """Return (composition, leadership, note) from an OpenAlex work record."""
    auths = work.get("authorships", [])
    if not auths:
        return None, None, "no_authorships"
    per_author = []          # one country-set per author
    lead_countries = set()   # countries of first + corresponding authors
    for a in auths:
        countries = {c for i in a.get("institutions", [])
                     if (c := i.get("country_code"))}
        per_author.append(countries)
        if a.get("author_position") == "first" or a.get("is_corresponding"):
            lead_countries |= countries
    known = [c for c in per_author if c]
    if not known:
        return None, None, "no_affiliations"
    african = [bool(c & AFRICAN_ISO2) for c in known]
    composition = ("all_african" if all(african)
                   else "mixed" if any(african) else "none")
    leadership = "yes" if lead_countries & AFRICAN_ISO2 else "no"
    note = "some_authors_unaffiliated" if len(known) < len(per_author) else ""
    return composition, leadership, note


def main():
    df = pd.read_excel(WORKBOOK, sheet_name="studies.csv")
    doi_col = next(c for c in df.columns if "doi" in c.lower())
    df["_doi"] = df[doi_col].map(norm_doi)

    rows, todo = [], df[df["_doi"].notna()][["study_id", "_doi"]].values.tolist()
    for sid, _ in df[df["_doi"].isna()][["study_id", doi_col]].values.tolist():
        rows.append({"study_id": sid, "composition": "", "leadership": "",
                     "review": "no_doi"})

    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        flt = "|".join(d for _, d in batch)
        r = requests.get(
            "https://api.openalex.org/works",
            params={"filter": f"doi:{flt}", "per-page": 50, "mailto": MAILTO},
            timeout=60,
        )
        r.raise_for_status()
        found = {re.sub(r"^https://doi\.org/", "", w["doi"]).lower(): w
                 for w in r.json().get("results", []) if w.get("doi")}
        for sid, doi in batch:
            w = found.get(doi)
            if w is None:
                rows.append({"study_id": sid, "composition": "",
                             "leadership": "", "review": "not_in_openalex"})
                continue
            comp, lead, note = classify(w)
            rows.append({"study_id": sid,
                         "composition": comp or "",
                         "leadership": lead or "",
                         "review": note if comp is None else note})
        print(f"{min(i + 50, len(todo))}/{len(todo)} DOIs processed")
        time.sleep(0.3)

    out = pd.DataFrame(rows).sort_values("study_id")
    out.to_csv(OUTPUT, index=False)
    n = len(out)
    ok = (out["composition"] != "").sum()
    print(f"\nDone: {ok}/{n} classified -> {OUTPUT}")
    print(out[out["composition"] != ""]["composition"].value_counts())
    print("Manual review needed:",
          (out["review"].isin(["no_doi", "not_in_openalex",
                               "no_affiliations", "no_authorships"])).sum())


if __name__ == "__main__":
    main()
