-- SQLite schema for the synthetic CRM opportunities export.
-- Load with: sqlite3 pipeline.db < sql/schema.sql
-- then: sqlite3 pipeline.db
--   sqlite> .mode csv
--   sqlite> .import --skip 1 data/opportunities.csv opportunities

CREATE TABLE opportunities (
    opp_id      TEXT PRIMARY KEY,
    rep_name    TEXT NOT NULL,
    stage       TEXT NOT NULL,   -- Prospecting | Qualification | Proposal | Negotiation | Closed Won | Closed Lost
    amount      INTEGER NOT NULL,
    created_date TEXT NOT NULL,  -- YYYY-MM-DD
    close_date  TEXT,            -- YYYY-MM-DD, NULL/empty when still open
    industry    TEXT NOT NULL,
    lead_source TEXT NOT NULL
);
