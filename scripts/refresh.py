"""
Import-mode refresh for the iPhone 18 vs iPhone 17 dashboard: query BigQuery, write data/data.json and data/stores.csv.

Runs in GitHub Actions (.github/workflows/refresh.yml) when you press "Refresh data" -> "Run workflow".
Credentials come from the GCP_SA_KEY repo secret, so nothing secret is in the repo.

What it does
  1. Finds the latest iPhone 18 Non PO sale date in BigQuery.
  2. Counts the selling days since iPhone 18 launched (16 Oct 2026) up to that date.
  3. Pulls the same number of days for iPhone 17 (from 17 Oct 2025), Pro and Pro Max only.
  4. Writes data/data.json (read by index.html) and data/stores.csv.

Local run (optional)
  pip install google-cloud-bigquery
  gcloud auth application-default login      # sign in with the Google account that can read e-smart-433113

  python scripts/refresh.py
"""
import csv
import json
import os
import sys
from datetime import datetime, timezone
from collections import defaultdict
from datetime import date, timedelta

from google.cloud import bigquery

PROJECT = "e-smart-433113"
TABLE = "`e-smart-433113.region_data.sales_all_retail`"
LAUNCH17 = date(2025, 10, 17)   # first Non PO sale of iPhone 17
LAUNCH18 = date(2026, 10, 16)   # first Non PO sale of iPhone 18
MODELS = "('IPHONE 17 PRO', 'IPHONE 17 PRO MAX', 'IPHONE 18 PRO', 'IPHONE 18 PRO MAX')"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root
MAX_GB = float(os.environ.get("MAX_GB", "3"))   # per-query safety cap

client = bigquery.Client(project=PROJECT, location="asia-southeast2")


def q(sql):
    # dry run first (free) so a bad edit can never scan more than MAX_GB
    dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    gb = dry.total_bytes_processed / 1e9
    if gb > MAX_GB:
        sys.exit(f"Aborting: query would scan {gb:.2f} GB, above MAX_GB={MAX_GB}.")
    job = client.query(sql, job_config=bigquery.QueryJobConfig(
        maximum_bytes_billed=int(MAX_GB * 1e9), labels={"app": "ip18-vs-ip17-dashboard"}))
    rows = [dict(r.items()) for r in job.result()]
    print(f"  query scanned {gb:.2f} GB, {len(rows)} rows")
    return rows


# 1. Window length = iPhone 18 selling days so far
last18 = q(f"""SELECT MAX(order_date) d FROM {TABLE}
  WHERE ket_po = 'Non PO' AND Product_Category = 'Device' AND Model_Type = 'IPHONE 18'""")[0]["d"]
n = (last18 - LAUNCH18).days + 1
end17 = LAUNCH17 + timedelta(days=n - 1)
end18 = LAUNCH18 + timedelta(days=n - 1)
print(f"Window: {n} selling days  |  iPhone 17 {LAUNCH17}..{end17}  |  iPhone 18 {LAUNCH18}..{end18}")

WHERE = f"""ket_po = 'Non PO' AND Product_Category = 'Device' AND Model_Type_Detail IN {MODELS}
  AND ((Model_Type = 'IPHONE 17' AND order_date BETWEEN DATE '{LAUNCH17}' AND DATE '{end17}')
    OR (Model_Type = 'IPHONE 18' AND order_date BETWEEN DATE '{LAUNCH18}' AND DATE '{end18}'))"""

# 2. Store level: units and value (Rp mio) by model
stores = q(f"""SELECT business_unit bu, channel ch, LOB lob, TSH tsh, territory terr, store_status st,
    site_code sc, TRIM(store_name) sn,
    SUM(IF(Model_Type_Detail = 'IPHONE 17 PRO', quantity, 0)) u17p,
    SUM(IF(Model_Type_Detail = 'IPHONE 17 PRO MAX', quantity, 0)) u17m,
    SUM(IF(Model_Type_Detail = 'IPHONE 18 PRO', quantity, 0)) u18p,
    SUM(IF(Model_Type_Detail = 'IPHONE 18 PRO MAX', quantity, 0)) u18m,
    ROUND(SUM(IF(Model_Type_Detail = 'IPHONE 17 PRO', total_nett_amount_with_tax, 0)) / 1e6, 1) v17p,
    ROUND(SUM(IF(Model_Type_Detail = 'IPHONE 17 PRO MAX', total_nett_amount_with_tax, 0)) / 1e6, 1) v17m,
    ROUND(SUM(IF(Model_Type_Detail = 'IPHONE 18 PRO', total_nett_amount_with_tax, 0)) / 1e6, 1) v18p,
    ROUND(SUM(IF(Model_Type_Detail = 'IPHONE 18 PRO MAX', total_nett_amount_with_tax, 0)) / 1e6, 1) v18m
  FROM {TABLE} WHERE {WHERE}
  GROUP BY bu, ch, lob, tsh, terr, st, sc, sn
  HAVING u17p + u17m <> 0 OR u18p + u18m <> 0
  ORDER BY bu, ch, sc""")

# 3. Daily units by business unit x LOB x TSH x model
rows = q(f"""SELECT business_unit bu, LOB lob, TSH tsh,
    IF(Model_Type = 'IPHONE 18', '18', '17') ser,
    IF(Model_Type_Detail LIKE '%PRO MAX', 'PRO MAX', 'PRO') mdl,
    DATE_DIFF(order_date, IF(Model_Type = 'IPHONE 18', DATE '{LAUNCH18}', DATE '{LAUNCH17}'), DAY) + 1 day_n,
    SUM(quantity) qty
  FROM {TABLE} WHERE {WHERE}
  GROUP BY bu, lob, tsh, ser, mdl, day_n""")
series = defaultdict(lambda: [0] * n)
for r in rows:
    series[(r["bu"], r["lob"], r["tsh"], r["ser"], r["mdl"])][r["day_n"] - 1] += r["qty"]
daily = [dict(bu=k[0], lob=k[1], tsh=k[2], ser=k[3], mdl=k[4], d=v) for k, v in sorted(series.items())]

# 4. Write files
for s in stores:
    for k in ("u17p", "u17m", "u18p", "u18m"):
        s[k] = int(s[k] or 0)
    for k in ("v17p", "v17m", "v18p", "v18m"):
        s[k] = float(s[k] or 0)
wib = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
meta = dict(generated=wib.strftime('%Y-%m-%d'), refreshed_at=wib.strftime('%Y-%m-%d %H:%M'), window_days=n,
            launch17=LAUNCH17.isoformat(), end17=end17.isoformat(),
            launch18=LAUNCH18.isoformat(), end18=end18.isoformat(),
            source="BigQuery e-smart-433113.region_data.sales_all_retail · ket_po = Non PO · Product_Category = Device · Pro and Pro Max only")
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
with open(os.path.join(HERE, "data", "data.json"), "w", encoding="utf-8") as f:
    json.dump(dict(meta=meta, stores=stores, daily=daily), f, separators=(",", ":"), ensure_ascii=False)
with open(os.path.join(HERE, "data", "stores.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(stores[0].keys()))
    w.writeheader()
    w.writerows(stores)

u17 = sum(s["u17p"] + s["u17m"] for s in stores)
u18 = sum(s["u18p"] + s["u18m"] for s in stores)
print(f"Stores: {len(stores)}  |  iPhone 17 Pro+Pro Max: {u17:,}  |  iPhone 18 Pro+Pro Max: {u18:,}  |  growth {u18 / u17 - 1:+.1%}")
print("Wrote data/data.json and data/stores.csv")
