# Funnel Analysis & A/B Testing Project

A complete BA case study: analyze an e-commerce conversion funnel, find the
biggest drop-off, propose a statistically-grounded A/B test to fix it, and
estimate the expected business impact.

## The finding
Mobile checkout-to-purchase conversion (**42.75%**) is 29 points below
desktop (**72.06%**), despite mobile being 62% of all traffic — the clearest,
highest-leverage problem in the funnel. Full write-up:
[`docs/findings_and_ab_test_proposal.md`](docs/findings_and_ab_test_proposal.md)

## Project structure
```
ab-funnel-project/
├── README.md
├── data/
│   ├── generate_synthetic_data.py   -- generates the funnel event dataset
│   └── funnel_events.csv            -- output (created by the script)
├── sql/
│   └── funnel_analysis.sql          -- funnel + drop-off + segmentation queries
├── analysis/
│   └── ab_test_design.py            -- sample size / power calculation for the A/B test
└── docs/
    └── findings_and_ab_test_proposal.md  -- PRD-style write-up with results
```

## Why synthetic data
This is built to run anywhere without a live Kaggle download. The generator
(`data/generate_synthetic_data.py`) bakes in a realistic, non-obvious business
problem (mobile checkout friction) so the analysis surfaces a genuine finding
rather than random noise — the exact same SQL and Python then apply unchanged
to a real event log (Google Analytics export, Mixpanel/Amplitude data dump,
etc.), you'd just point `sql/funnel_analysis.sql` at your own `events` table
with matching columns: `user_id, session_id, event_time, event_name, device,
traffic_source`.

## How to run it
```bash
# 1. Generate the dataset
cd data && python3 generate_synthetic_data.py && cd ..

# 2. Load into SQLite and run the funnel analysis
python3 -c "
import sqlite3, pandas as pd
conn = sqlite3.connect('funnel.db')
pd.read_csv('data/funnel_events.csv').to_sql('events', conn, if_exists='replace', index=False)
"
sqlite3 funnel.db < sql/funnel_analysis.sql

# 3. Run the A/B test sample-size / power calculation
cd analysis && python3 ab_test_design.py
```

## Skills demonstrated
- **SQL**: CTEs, conditional aggregation, funnel/segmentation analysis
- **Statistics**: two-proportion z-test, power analysis, sample size
  calculation, MDE trade-off reasoning
- **Business reasoning**: translating a data pattern into a hypothesis,
  a testable experiment design, and a revenue-impact estimate — with
  explicit caveats about what the numbers do and don't prove
