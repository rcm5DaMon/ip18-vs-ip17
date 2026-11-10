# iPhone 18 vs iPhone 17 — Pro & Pro Max launch sell-out (Erajaya Region 5)

Static dashboard comparing iPhone 18 Pro / Pro Max with iPhone 17 Pro / Pro Max over the **same number of selling days** after launch.

- **Live page:** `https://rcm5damon.github.io/ip18-vs-ip17/` (GitHub Pages, deployed by GitHub Actions)
- **Refresh:** the **Refresh data ↗** button on the page opens the workflow. Press **Run workflow**, wait about 2 minutes, reload the page.

## What's in the page
- Filters: Model type detail (Pro / Pro Max), Business unit, LOB, TSH
- KPI cards: units, value, ASP, Pro Max units — iPhone 18 vs 17 with growth
- Cumulative and daily units by selling day
- Breakdown by business unit, channel, LOB, TSH
- LOB → TSH → store table with collapsible groups

## Data
| File | Contents |
|---|---|
| `data/data.json` | Data the page reads: one row per store (units and value by model) and daily units by business unit × TSH × model |
| `data/stores.csv` | Same store-level data as CSV |
| `downloads/iPhone18_vs_iPhone17_ProProMax_Region5.xlsx` | Excel version with formulas (Summary, Daily Curve, BU, Channel, LOB, TSH, LOB-TSH-Store, By Store) |

Source: BigQuery `e-smart-433113.region_data.sales_all_retail`, `ket_po = 'Non PO'`, `Product_Category = 'Device'`, `Model_Type_Detail` in iPhone 17/18 Pro and Pro Max. Units are net quantity; value is `total_nett_amount_with_tax` (Rp million in the data files).

| `scripts/refresh.py` | Runs the BigQuery import (dry-run cost check first, capped at 3 GB per query) and writes the two data files |
| `.github/workflows/refresh.yml` | The "Refresh data" workflow + Pages deploy |

## One-time setup
1. Upload **all** files in this folder to the repo, including the hidden `.github` folder.
2. **Settings → Secrets and variables → Actions → New repository secret.** Name: `GCP_SA_KEY`. Value: the whole JSON key of a service account with **BigQuery Data Viewer** + **BigQuery Job User** on `e-smart-433113` (the same key you use for `sbd_vivo` works).
3. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
4. If your repo is not named `rcm5DaMon/ip18-vs-ip17`, change `const GITHUB_REPO = ...` near the top of the script in `index.html`.
5. **Actions → Refresh data → Run workflow** for the first deploy.

## How refresh works
- The workflow finds the latest iPhone 18 Non PO sale date, sets both windows to that many selling days (iPhone 18 from 16 Oct 2026, iPhone 17 from 17 Oct 2025), and rewrites `data/data.json` and `data/stores.csv`.
- About 2 GB scanned per refresh (well within BigQuery's free 1 TB/month).
- Filters on the page never query BigQuery; they re-slice the imported data in the browser.
- To refresh every morning automatically, uncomment the `schedule` block in `.github/workflows/refresh.yml`.
- The Excel file in `downloads/` is a 10 Nov 2026 snapshot and is not updated by the workflow.

## ⚠ Visibility
GitHub Pages sites are public. Anyone with the URL can see store names and sales figures.
