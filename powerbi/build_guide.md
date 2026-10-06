# Power BI Build Guide: Sales Pipeline Dashboard

Time: about 1 hour. Source file: `data/opportunities.csv`.

## 1. Load the data (10 min)

1. Home > Get Data > Text/CSV > `opportunities.csv` > Transform Data (open Power Query).
2. Set column types:
   - `amount` > Whole Number
   - `created_date`, `close_date` > Date
   - `close_date` empty strings become null automatically. If any show as blank text, select the column > Transform > Replace Values, replace `` (empty) with null.
3. Add a custom column: Add Column > Custom Column, name `quarter`, formula:
   ```
   Text.From(Date.Year([created_date])) & "Q" & Text.From(Date.QuarterOfYear([created_date]))
   ```
4. Add a custom column `cycle_days`:
   ```
   if [close_date] = null then null else Duration.Days([close_date] - [created_date])
   ```
5. Close & Apply.

## 2. Quota table + DAX measures (10 min)

Quotas live outside the CSV, so add a small table: Home > Enter Data, name it `Quotas`:

| rep_name     | annual_quota |
|--------------|--------------|
| Elena Torres | 1000000      |
| Marcus Webb  | 950000       |
| Priya Nair   | 900000       |
| Dan Kowalski | 850000       |
| Sofia Reyes  | 900000       |
| Jake Morris  | 800000       |
| Tom Becker   | 1100000      |
| Aisha Khan   | 1200000      |

Model view: create a relationship `opportunities[rep_name]` > `Quotas[rep_name]` (many to one, single direction).

Then Modeling > New Measure, one at a time:

```dax
Closed Deals = CALCULATE(COUNTROWS(opportunities), opportunities[stage] IN {"Closed Won", "Closed Lost"})

Won Deals = CALCULATE(COUNTROWS(opportunities), opportunities[stage] = "Closed Won")

Win Rate = DIVIDE([Won Deals], [Closed Deals])

Won Revenue = CALCULATE(SUM(opportunities[amount]), opportunities[stage] = "Closed Won")

Attainment = DIVIDE([Won Revenue], SUM(Quotas[annual_quota]) * 1.75)
```
(quotas are annual; x1.75 pro-rates for the 21-month window)

```dax
Avg Cycle Days = AVERAGEX(FILTER(opportunities, NOT(ISBLANK(opportunities[close_date]))), opportunities[cycle_days])

Open Pipeline $ = CALCULATE(SUM(opportunities[amount]), NOT(opportunities[stage] IN {"Closed Won", "Closed Lost"}))
```

Sort order for stages: select the `stage` column > Column Tools > Sort by Column won't have a helper, so instead in the Funnel visual sort manually, or add a calculated column `stage_sort` with SWITCH mapping Prospecting=1 ... Closed Lost=6 and sort `stage` by it.

## 3. Visuals (30 min)

Page size: 16:9.

**KPI cards (top row, 4 cards):** Win Rate (20.5%), Won Revenue, Open Pipeline $, Avg Cycle Days (64). Format Win Rate as %, revenue as $ millions.

**Funnel visual (left):** Visualizations > Funnel. Category = `stage` (sorted by stage_sort), Values = Count of `opp_id`. Shows 154 > 85 > 80 > 33 > 72 won / 376 lost.

**Rep leaderboard (right):** Clustered bar chart. Y-axis = `rep_name`, X-axis = `[Win Rate]`. Sort descending. Data labels on. Add `[Attainment]` to Tooltips. Elena Torres should top it at 44.1%.

**Win rate by lead source (bottom left):** Clustered bar chart. Y-axis = `lead_source`, X-axis = `[Win Rate]`. Referral ~31%, Outbound ~9%.

**Quarterly won revenue (bottom right):** Line chart. X-axis = `quarter`, Y-axis = `[Won Revenue]`. Add a second line for open-pipeline forecast if you want: `[Open Pipeline $]` by `quarter`.

**Cycle length:** small clustered bar chart. Axis = `stage` filtered to Closed Won / Closed Lost (visual-level filter), Values = `[Avg Cycle Days]`. Won ~139 days, Lost ~44.

## 4. Slicers + interactivity (10 min)

Slicers on the right rail (or top):
- `rep_name` (dropdown, multi-select with Ctrl)
- `industry` (dropdown)
- `quarter` (dropdown)

Interactivity is on by default: clicking a rep in the leaderboard cross-filters the funnel, source chart, cards, and quarterly line. If a visual should not be filtered (e.g. keep KPI cards global), select the source visual > Format > Edit interactions > set the target visual to None.

## 5. Sanity checks

- Win Rate card = 20.5%. If blank, check the `Closed Deals` measure syntax.
- Attainment for Elena Torres = 182.6%. If it shows ~320%, you forgot the x1.75.
- Slicing to 2025Q3 should show almost no won revenue (those deals are still open). That is correct, not a bug.
