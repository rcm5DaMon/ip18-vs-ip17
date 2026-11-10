# iPhone 18 vs iPhone 17 — Pro & Pro Max launch sell-out (Erajaya Region 5)

Static dashboard comparing iPhone 18 Pro / Pro Max with iPhone 17 Pro / Pro Max over the **same number of selling days** after launch.

- **Live page:** GitHub Pages (Settings → Pages → Deploy from branch `main`, folder `/root`)
- **Snapshot date:** 10 Nov 2026 (iPhone 18: 16 Oct – 9 Nov 2026 · iPhone 17: 17 Oct – 10 Nov 2025 · 25 days each)

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

## Refreshing
The page is a snapshot. To update it, re-export the queries above into `data/data.json` (same structure) and push.
