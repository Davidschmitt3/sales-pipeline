"""Generate a synthetic CRM opportunities dataset (~800 rows).

Baked-in patterns (so the analysis finds something real):
- Conversion decays at each funnel stage.
- Proposal -> Negotiation is the leakiest step (deals stall in Proposal).
- Two standout reps (Elena Torres, Marcus Webb); two weak reps (Tom Becker, Aisha Khan).
- Referral/Partner leads close at higher rates than Outbound.
- Cycle lengths: Negotiation-stage deals take longest; early losses die fast.
- Recent deals are still open (close_date is null); stale open deals die as losses.
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)

N_OPPS = 800
START = date(2024, 1, 1)
END = date(2025, 9, 15)
TODAY = date(2025, 10, 6)  # reference "today" for open vs closed

REPS = [
    ("Elena Torres", 1.45),   # standout
    ("Marcus Webb", 1.38),    # standout
    ("Priya Nair", 1.12),
    ("Dan Kowalski", 1.08),
    ("Sofia Reyes", 1.05),
    ("Jake Morris", 1.00),
    ("Tom Becker", 0.72),     # weak
    ("Aisha Khan", 0.68),     # weak
]

# (name, weight, close-rate multiplier)
SOURCES = [
    ("Inbound", 0.30, 1.00),
    ("Outbound", 0.38, 0.85),
    ("Referral", 0.16, 1.30),
    ("Partner", 0.16, 1.22),
]

# (name, weight, typical deal size)
INDUSTRIES = [
    ("Tech", 0.30, 120_000),
    ("Healthcare", 0.22, 110_000),
    ("Finance", 0.20, 150_000),
    ("Retail", 0.14, 60_000),
    ("Manufacturing", 0.14, 85_000),
]

STAGES = ["Prospecting", "Qualification", "Proposal", "Negotiation"]

# per-stage base advance prob and base lost prob (rest = still open/stalled)
STAGE_PARAMS = {
    "Prospecting": {"adv": 0.60, "lost": 0.22},
    "Qualification": {"adv": 0.55, "lost": 0.25},
    "Proposal": {"adv": 0.40, "lost": 0.30},     # stall stage: lowest advance
    "Negotiation": {"adv": 0.60, "lost": 0.25},  # adv here = Closed Won
}

# typical cycle length (days) sampled by final stage
CYCLE_DAYS = {
    "Closed Won": (95, 190),
    "Lost@Negotiation": (70, 150),
    "Lost@Proposal": (45, 110),
    "Lost@Qualification": (25, 60),
    "Lost@Prospecting": (8, 30),
}


def weighted_pick(options):
    names = [o[0] for o in options]
    weights = [o[1] for o in options]
    return random.choices(names, weights=weights, k=1)[0]


def main():
    rep_mult = {name: mult for name, mult in REPS}
    src_mult = {name: mult for name, _, mult in SOURCES}
    ind_base = {name: base for name, _, base in INDUSTRIES}

    rows = []
    for i in range(1, N_OPPS + 1):
        rep = weighted_pick([(n, 1, 0) for n, _ in REPS])  # even book across reps
        source = weighted_pick(SOURCES)
        industry = weighted_pick(INDUSTRIES)
        base = ind_base[industry]
        amount = int(round(base * random.lognormvariate(0, 0.45), -2))
        amount = max(amount, 5_000)

        created = START + timedelta(days=random.randint(0, (END - START).days))

        # walk the funnel
        final_stage = "Prospecting"
        terminal = None  # None, "won", or the stage where it was lost
        stall_stage = None
        big_deal_adj = 0.90 if amount > 200_000 else 1.0
        for stage in STAGES:
            params = STAGE_PARAMS[stage]
            p_adv = params["adv"] * rep_mult[rep] * src_mult[source] * big_deal_adj
            p_adv = max(0.05, min(0.92, p_adv))
            p_lost = params["lost"]
            roll = random.random()
            if roll < p_adv:
                if stage == "Negotiation":
                    terminal = "won"
                else:
                    final_stage = STAGES[STAGES.index(stage) + 1]
                continue
            elif roll < p_adv + p_lost:
                terminal = stage  # lost at this stage
                final_stage = stage
                break
            else:
                stall_stage = stage  # still open
                final_stage = stage
                break

        # figure out stage label and cycle
        if terminal == "won":
            stage_label = "Closed Won"
            cycle_key = "Closed Won"
            last_open = "Negotiation"
        elif terminal is not None:
            stage_label = "Closed Lost"
            cycle_key = f"Lost@{terminal}"
            last_open = terminal
        else:
            stage_label = stall_stage  # still in pipeline
            cycle_key = None
            last_open = None

        if cycle_key is not None:
            lo, hi = CYCLE_DAYS[cycle_key]
            cycle = random.randint(lo, hi)
            cycle = int(cycle * (amount / 100_000) ** 0.12)  # bigger deals drag
            close_date = created + timedelta(days=cycle)
            if close_date > TODAY:
                # hasn't had time to finish yet: still open
                stage_label = last_open
                close_date_str = ""
            else:
                close_date_str = close_date.isoformat()
        else:
            close_date_str = ""

        rows.append({
            "opp_id": f"OPP-{i:04d}",
            "rep_name": rep,
            "stage": stage_label,
            "amount": amount,
            "created_date": created.isoformat(),
            "close_date": close_date_str,
            "industry": industry,
            "lead_source": source,
        })

    out_path = "data/opportunities.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
