# Sales Pipeline Analytics

I generated a fake CRM dataset (800 opportunities, 8 reps, 21 months) and analyzed it the way I wish someone had analyzed my book when I was selling at Dell.

## Key findings

1. The team wins 20.5% of closed deals (96 of 468). The funnel leaks hardest between Proposal and Negotiation: only 22.3% of deals that entered Proposal made it out, the steepest drop at any stage. That is where deals go to die.

2. Two reps carry the team. Elena Torres wins 44.1% of her deals and finished at 182.6% of quota on $3.2M closed. Marcus Webb is right behind at 32.9% and 174.7%. At the other end, Tom Becker wins 4.3% and sits at 11.5% of quota. Elena and Marcus alone closed 55 of the team's 96 wins.

3. Referrals close. Referral-sourced deals win 31.4% of the time vs 9.2% for Outbound, a 3.4x gap. Referral and Partner together produced 52 of the 96 wins despite being a minority of pipeline.

4. Winners take time. Closed-won deals averaged 139 days vs 41 days for losses. Deals that survive deep into the funnel run long; the losses died fast, mostly inside six weeks.

## Tools

- Python (pandas) for the full analysis
- SQLite for the query layer (schema + 6 analysis queries)
- Tableau and Power BI build guides so the dashboards can be rebuilt from the CSV in about an hour each

## Project structure

```
sales-pipeline/
├── data/
│   ├── generate_data.py      # seeded synthetic CRM generator (seed 42)
│   └── opportunities.csv     # 800 rows, generated output
├── python/
│   └── pipeline_analysis.py  # win rate, funnel, reps, quota, cycles, forecast
├── sql/
│   ├── schema.sql            # CREATE TABLE opportunities (SQLite)
│   └── analysis_queries.sql  # 6 analysis queries
├── tableau/
│   └── build_guide.md        # exact sheets, fields, filters, layout
├── powerbi/
│   └── build_guide.md        # data model, DAX measures, visuals, slicers
├── requirements.txt
└── README.md
```

## How to run

```bash
pip install -r requirements.txt

# generate the data (seeded, reproducible)
python3 data/generate_data.py

# run the analysis
python3 python/pipeline_analysis.py

# load into SQLite and run the queries
sqlite3 pipeline.db < sql/schema.sql
sqlite3 pipeline.db <<'EOF'
.mode csv
.import --skip 1 data/opportunities.csv opportunities
EOF
sqlite3 pipeline.db < sql/analysis_queries.sql
```

One note on the funnel math: the CSV is a snapshot with no stage-history table, so a Closed Lost deal can't be traced to the stage where it died. Stage-to-stage conversion is "confirmed" (deals proven past a stage divided by deals that entered it), which makes the rates conservative lower bounds. The relative pattern across stages is the point.
