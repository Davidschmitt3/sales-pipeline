-- Sales pipeline analysis queries (SQLite). Run after loading data/opportunities.csv.
-- Note: close_date is an empty string (not SQL NULL) for open deals, hence NULLIF(close_date, '').

-- 1. Funnel conversion by stage.
-- Snapshot export has no stage-history table, so conversion is "confirmed":
-- deals proven past a stage (sitting in a later stage, or closed won)
-- divided by all deals that entered it. Conservative lower bound.
WITH f AS (
    SELECT
        COUNT(*) AS total,
        SUM(stage = 'Prospecting')   AS open_prosp,
        SUM(stage = 'Qualification') AS open_qual,
        SUM(stage = 'Proposal')      AS open_prop,
        SUM(stage = 'Negotiation')   AS open_neg,
        SUM(stage = 'Closed Won')    AS won,
        SUM(stage = 'Closed Lost')   AS lost
    FROM opportunities
)
SELECT 'Prospecting -> Qualification' AS step,
       total - open_prosp - lost AS advanced,
       total AS entered,
       ROUND(100.0 * (total - open_prosp - lost) / total, 1) AS conv_pct FROM f
UNION ALL
SELECT 'Qualification -> Proposal',
       total - open_prosp - open_qual - lost,
       total - open_prosp,
       ROUND(100.0 * (total - open_prosp - open_qual - lost) / (total - open_prosp), 1) FROM f
UNION ALL
SELECT 'Proposal -> Negotiation',
       total - open_prosp - open_qual - open_prop - lost,
       total - open_prosp - open_qual,
       ROUND(100.0 * (total - open_prosp - open_qual - open_prop - lost) / (total - open_prosp - open_qual), 1) FROM f
UNION ALL
SELECT 'Negotiation -> Closed Won',
       won,
       won + lost + open_neg,
       ROUND(100.0 * won / (won + lost + open_neg), 1) FROM f;

-- 2. Win rate by rep.
SELECT rep_name,
       COUNT(*) AS closed_deals,
       SUM(stage = 'Closed Won') AS won_deals,
       ROUND(100.0 * SUM(stage = 'Closed Won') / COUNT(*), 1) AS win_rate_pct,
       SUM(CASE WHEN stage = 'Closed Won' THEN amount ELSE 0 END) AS won_revenue
FROM opportunities
WHERE stage IN ('Closed Won', 'Closed Lost')
GROUP BY rep_name
ORDER BY win_rate_pct DESC;

-- 3. Quota attainment per rep (annual quotas pro-rated x1.75 for the 21-month window).
WITH quotas(rep_name, annual_quota) AS (
    VALUES
        ('Elena Torres', 1000000),
        ('Marcus Webb',   950000),
        ('Priya Nair',    900000),
        ('Dan Kowalski',  850000),
        ('Sofia Reyes',   900000),
        ('Jake Morris',   800000),
        ('Tom Becker',   1100000),
        ('Aisha Khan',   1200000)
),
rev AS (
    SELECT rep_name, SUM(amount) AS won_revenue
    FROM opportunities
    WHERE stage = 'Closed Won'
    GROUP BY rep_name
)
SELECT q.rep_name,
       r.won_revenue,
       CAST(ROUND(q.annual_quota * 1.75) AS INTEGER) AS prorated_quota,
       ROUND(100.0 * r.won_revenue / (q.annual_quota * 1.75), 1) AS attainment_pct
FROM quotas q
JOIN rev r ON r.rep_name = q.rep_name
ORDER BY attainment_pct DESC;

-- 4. Average sales cycle length in days (closed deals only).
SELECT CASE WHEN stage = 'Closed Won' THEN 'won' ELSE 'lost' END AS outcome,
       COUNT(*) AS deals,
       ROUND(AVG(julianday(NULLIF(close_date, '')) - julianday(created_date)), 0) AS avg_cycle_days
FROM opportunities
WHERE NULLIF(close_date, '') IS NOT NULL
GROUP BY outcome
UNION ALL
SELECT 'overall',
       COUNT(*),
       ROUND(AVG(julianday(NULLIF(close_date, '')) - julianday(created_date)), 0)
FROM opportunities
WHERE NULLIF(close_date, '') IS NOT NULL;

-- 5. Win rate by lead source.
SELECT lead_source,
       COUNT(*) AS closed_deals,
       SUM(stage = 'Closed Won') AS won_deals,
       ROUND(100.0 * SUM(stage = 'Closed Won') / COUNT(*), 1) AS win_rate_pct,
       SUM(CASE WHEN stage = 'Closed Won' THEN amount ELSE 0 END) AS won_revenue
FROM opportunities
WHERE stage IN ('Closed Won', 'Closed Lost')
GROUP BY lead_source
ORDER BY win_rate_pct DESC;

-- 6. Quarterly closed revenue (by created quarter).
SELECT substr(created_date, 1, 4) || 'Q' || CAST((CAST(substr(created_date, 6, 2) AS INTEGER) + 2) / 3 AS TEXT) AS quarter,
       COUNT(*) AS deals_created,
       SUM(CASE WHEN stage = 'Closed Won' THEN amount ELSE 0 END) AS won_revenue,
       SUM(CASE WHEN stage = 'Closed Lost' THEN amount ELSE 0 END) AS lost_revenue
FROM opportunities
GROUP BY quarter
ORDER BY quarter;
