# Tableau Build Guide: Sales Pipeline Dashboard

Time: about 1 hour. Source file: `data/opportunities.csv`.

## 1. Connect the data (5 min)

1. Open Tableau Desktop. Connect > To a File > Text file > `opportunities.csv`.
2. Check the field types Tableau assigned:
   - `Amount` > Number (whole)
   - `Created Date`, `Close Date` > Date
   - `Close Date` will show Null for open deals. That is correct.
3. Go to a new worksheet.

## 2. Calculated fields (10 min)

Create these (right-click in the Data pane > Create Calculated Field):

- **Is Won**: `IF [Stage] = "Closed Won" THEN 1 ELSE 0 END`
- **Is Closed**: `IF [Stage] = "Closed Won" OR [Stage] = "Closed Lost" THEN 1 ELSE 0 END`
- **Win Rate**: `SUM([Is Won]) / SUM([Is Closed])` (format as percentage)
- **Cycle Days**: `DATEDIFF('day', [Created Date], [Close Date])` (Null for open deals, fine)
- **Quota**: 
  ```
  CASE [Rep Name]
    WHEN "Elena Torres" THEN 1000000
    WHEN "Marcus Webb"  THEN 950000
    WHEN "Priya Nair"   THEN 900000
    WHEN "Dan Kowalski" THEN 850000
    WHEN "Sofia Reyes"  THEN 900000
    WHEN "Jake Morris"  THEN 800000
    WHEN "Tom Becker"   THEN 1100000
    WHEN "Aisha Khan"   THEN 1200000
  END
  ```
- **Attainment**: `SUM(IF [Stage] = "Closed Won" THEN [Amount] END) / (AVG([Quota]) * 1.75)`
  (quotas are annual; x1.75 pro-rates for the 21-month window)
- **Quarter**: `DATETRUNC('quarter', [Created Date])`
- **Stage Sort**: `CASE [Stage] WHEN "Prospecting" THEN 1 WHEN "Qualification" THEN 2 WHEN "Proposal" THEN 3 WHEN "Negotiation" THEN 4 WHEN "Closed Won" THEN 5 WHEN "Closed Lost" THEN 6 END`

## 3. Sheets (30 min)

**Sheet 1 "Funnel"** (bar chart)
- Rows: `Stage` (right-click > Sort > Manual, order: Prospecting, Qualification, Proposal, Negotiation, Closed Won, Closed Lost)
- Columns: `CNT(Opportunities)` (drag Number of Records, or CNT(Opp Id))
- Color: `Stage`
- Label: CNT(Opportunities)
- Shows the pipeline snapshot: 154 sitting in Prospecting, 80 in Proposal, 33 in Negotiation, 72 won, 376 lost.

**Sheet 2 "Rep leaderboard"** (bar chart)
- Rows: `Rep Name`, sorted descending by Win Rate
- Columns: `Win Rate`
- Color: `Attainment` (red-blue diverging, stepped, centered at 100%)
- Tooltip: add `Attainment`, `Won Revenue` (`SUM(IF [Stage]="Closed Won" THEN [Amount] END)`), closed deal count
- Reference line at 100% attainment if you want it: Analytics pane > Reference Line on the Attainment axis is not available here since color holds it; skip it.

**Sheet 3 "Win rate by source"** (bar chart)
- Rows: `Lead Source`
- Columns: `Win Rate`
- Color: `Win Rate` (sequential blue)
- Label: Win Rate as %
- Referral should sit near 31%, Outbound near 9%.

**Sheet 4 "Cycle length"** (bar chart)
- Filter: `Stage` = Closed Won, Closed Lost only
- Rows: `Stage`
- Columns: `AVG(Cycle Days)`
- Won should show ~139 days, Lost ~44.

**Sheet 5 "Quarterly revenue"** (line chart)
- Filter: `Stage` = Closed Won
- Columns: `Quarter` (continuous, exact date)
- Rows: `SUM(Amount)`
- Line, with circles on. Shows revenue by created quarter.

## 4. Dashboard (15 min)

1. New Dashboard, size 1200 x 800 (Fixed size).
2. Layout:
   - Top: text title "Sales Pipeline Performance" + subtitle "800 opportunities, Jan 2024 - Sep 2025"
   - KPI tiles (use Sheet 2-style text or BANs): Win Rate 20.5%, Open Pipeline $40.0M, Avg Cycle 64 days. Build each as a one-cell worksheet (MIN/MAX trick) or just text boxes with the numbers.
   - Left column: Funnel (Sheet 1) on top, Cycle length (Sheet 4) below
   - Right column: Rep leaderboard (Sheet 2) on top, Win rate by source (Sheet 3) below
   - Bottom: Quarterly revenue (Sheet 5) spanning full width
3. Filters (right rail, apply to all worksheets using the data source):
   - `Rep Name` (multi-select dropdown)
   - `Industry` (multi-select)
   - `Quarter` (multi-select)
4. Interactivity: Dashboard > Actions > Add Action > Filter. Source sheet: Rep leaderboard, target: all sheets, run on Select. Clicking a rep filters the whole dashboard to them.

## 5. Sanity checks

- Win Rate KPI = 20.5%. If it is not, check the Is Closed calc.
- Elena Torres tops the leaderboard at 44.1%. Tom Becker sits at the bottom at 4.3%.
- Filters should cross-filter every sheet. If a sheet ignores a filter, right-click the filter > Apply to Worksheets > All Using This Data Source.
