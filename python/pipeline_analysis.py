"""Sales pipeline analysis on the synthetic CRM dataset.

Reads data/opportunities.csv and prints: win rate, funnel conversion,
rep leaderboard with quota attainment, cycle lengths, win rate by
industry and lead source, and a pipeline-weighted forecast vs actuals.

Note on the funnel: this is a snapshot export with no stage-history table,
so a deal marked Closed Lost can't be traced to the stage where it died.
Conversion below is "confirmed": deals we can prove advanced past a stage
(open in a later stage, or closed won) divided by all deals that entered it.
Closed-lost deals count as entered but not as advanced, so these rates are
conservative lower bounds. The relative pattern across stages is what matters.
"""
import pandas as pd

df = pd.read_csv("data/opportunities.csv", parse_dates=["created_date", "close_date"])

CLOSED = ["Closed Won", "Closed Lost"]
STAGE_ORDER = ["Prospecting", "Qualification", "Proposal", "Negotiation"]

QUOTAS = {  # annual quota per rep, in dollars
    "Elena Torres": 1_000_000,
    "Marcus Webb": 950_000,
    "Priya Nair": 900_000,
    "Dan Kowalski": 850_000,
    "Sofia Reyes": 900_000,
    "Jake Morris": 800_000,
    "Tom Becker": 1_100_000,
    "Aisha Khan": 1_200_000,
}

# close probability used to weight open pipeline in the forecast
STAGE_WEIGHT = {"Prospecting": 0.10, "Qualification": 0.20, "Proposal": 0.40, "Negotiation": 0.65}

closed = df[df["stage"].isin(CLOSED)].copy()
closed["cycle_days"] = (closed["close_date"] - closed["created_date"]).dt.days
won = closed[closed["stage"] == "Closed Won"]
open_df = df[~df["stage"].isin(CLOSED)].copy()

print("=" * 60)
print("SALES PIPELINE ANALYSIS")
print("=" * 60)

# 1. overall win rate
win_rate = len(won) / len(closed) * 100
print(f"\n1. OVERALL WIN RATE: {win_rate:.1f}% ({len(won)} won / {len(closed)} closed)")
print(f"   Total pipeline value: ${df['amount'].sum():,.0f}")
print(f"   Open pipeline: {len(open_df)} deals worth ${open_df['amount'].sum():,.0f}")

# 2. funnel conversion (confirmed advances / entered)
print("\n2. FUNNEL CONVERSION (confirmed stage-to-stage, see note above)")
for i, stage in enumerate(STAGE_ORDER):
    later = STAGE_ORDER[i + 1:]
    entered = int((df["stage"].isin([stage] + later).sum()) + (df["stage"] == "Closed Won").sum() + (df["stage"] == "Closed Lost").sum())
    advanced = int(df["stage"].isin(later).sum() + (df["stage"] == "Closed Won").sum())
    conv = advanced / entered * 100
    nxt = later[0] if later else "Closed Won"
    print(f"   {stage:<14} -> {nxt:<12}: {advanced:>4} advanced / {entered:>4} entered = {conv:>5.1f}%")

# 3. win rate by rep
print("\n3. WIN RATE BY REP")
rep = closed.groupby("rep_name").agg(
    closed_deals=("opp_id", "count"),
    won_deals=("stage", lambda s: (s == "Closed Won").sum()),
)
rep["won_revenue"] = closed[closed["stage"] == "Closed Won"].groupby("rep_name")["amount"].sum()
rep["won_revenue"] = rep["won_revenue"].fillna(0)
rep["win_rate"] = rep["won_deals"] / rep["closed_deals"] * 100
rep = rep.sort_values("win_rate", ascending=False)
for name, r in rep.iterrows():
    print(f"   {name:<14} win rate {r['win_rate']:>5.1f}%  ({int(r['won_deals']):>2}/{int(r['closed_deals']):>2})  won revenue ${r['won_revenue']:>11,.0f}")

# 4. quota attainment (quotas are annual; pro-rated x1.75 for the 21-month window)
print("\n4. QUOTA ATTAINMENT (closed-won revenue vs pro-rated quota, 21 months)")
attain = []
for name, r in rep.iterrows():
    quota = QUOTAS[name] * 1.75
    att = r["won_revenue"] / quota * 100
    attain.append((name, att))
    print(f"   {name:<14} ${r['won_revenue']:>11,.0f} / ${quota:>11,.0f}  = {att:>6.1f}%")

# 5. cycle length
print("\n5. AVG SALES CYCLE (days)")
print(f"   Overall (closed deals): {closed['cycle_days'].mean():.0f} days (median {closed['cycle_days'].median():.0f})")
print(f"   Won deals: {won['cycle_days'].mean():.0f} days | Lost deals: {closed[closed['stage'] == 'Closed Lost']['cycle_days'].mean():.0f} days")
print("   Age of deals currently sitting in each open stage:")
open_df["age_days"] = (pd.Timestamp("2025-10-06") - open_df["created_date"]).dt.days
for stage in STAGE_ORDER:
    age = open_df[open_df["stage"] == stage]["age_days"]
    if len(age):
        print(f"     {stage:<14}: {len(age):>3} deals, avg age {age.mean():.0f} days")

# 6. win rate by industry and lead source
print("\n6. WIN RATE BY INDUSTRY")
for ind, g in closed.groupby("industry"):
    wr = (g["stage"] == "Closed Won").mean() * 100
    rev = g.loc[g["stage"] == "Closed Won", "amount"].sum()
    print(f"   {ind:<14} {wr:>5.1f}%  ({int((g['stage'] == 'Closed Won').sum())}/{len(g)})  won revenue ${rev:>11,.0f}")
print("\n   WIN RATE BY LEAD SOURCE")
for src, g in closed.groupby("lead_source"):
    wr = (g["stage"] == "Closed Won").mean() * 100
    rev = g.loc[g["stage"] == "Closed Won", "amount"].sum()
    print(f"   {src:<14} {wr:>5.1f}%  ({int((g['stage'] == 'Closed Won').sum())}/{len(g)})  won revenue ${rev:>11,.0f}")

# 7. forecast vs actual per quarter
print("\n7. FORECAST VS ACTUAL (quarterly)")
df["quarter"] = df["created_date"].dt.to_period("Q").astype(str)
fw = open_df.copy()
fw["weighted"] = fw["stage"].map(STAGE_WEIGHT) * fw["amount"]
forecast = fw.groupby(fw["created_date"].dt.to_period("Q").astype(str))["weighted"].sum()
actual = won.copy()
actual_q = actual.groupby(actual["created_date"].dt.to_period("Q").astype(str))["amount"].sum()
for q in sorted(set(forecast.index) | set(actual_q.index)):
    f = forecast.get(q, 0)
    a = actual_q.get(q, 0)
    print(f"   {q}  forecast (pipeline-weighted) ${f:>11,.0f}   actual closed-won ${a:>11,.0f}")

print("\nDone.")
