# Funnel Analysis & A/B Test Proposal: Mobile Checkout Optimization

## 1. Problem Statement
The purchase funnel (view product → add to cart → begin checkout → purchase)
converts at **10.93% overall**, but this masks a large disparity by device.
Mobile — 62% of all traffic — converts at nearly half the rate of desktop
at the final step of the funnel. Fixing this is the single highest-leverage
lever available, because it affects the majority of traffic and the drop
is concentrated in one specific, actionable stage.

## 2. Funnel Analysis (from `sql/funnel_analysis.sql`)

| Stage | Users | Conversion from prior stage |
|---|---|---|
| Viewed product | 60,000 | — |
| Added to cart | 22,685 | 37.81% |
| Began checkout | 12,338 | 54.39% |
| Purchased | 6,555 | **53.13%** |

**Overall conversion: 10.93%**

### Where users are lost (absolute)
| Transition | Users lost |
|---|---|
| View → Cart | 37,315 |
| Cart → Checkout | 10,347 |
| **Checkout → Purchase** | **5,783** |

View→Cart loses the most users in absolute terms, but that's expected —
most product views are casual browsing, not purchase intent. Checkout→Purchase
is the more informative signal because everyone reaching that stage has
already declared intent to buy; losing over half of them there is a
conversion problem, not a browsing problem.

### The finding: device segmentation
| Device | Traffic share | Checkout → Purchase | Overall conversion |
|---|---|---|---|
| **Mobile** | 62% | **42.75%** | 8.78% |
| Tablet | 6% | 59.78% | 12.23% |
| Desktop | 32% | **72.06%** | 14.86% |

Mobile's checkout-to-purchase rate is **29 points below desktop** — the
single clearest, most actionable gap in the entire funnel. Every other
stage (view→cart, cart→checkout) converts similarly across devices, which
isolates the problem specifically to the checkout step on mobile, not to
mobile users being generally less interested.

### Traffic source (secondary cut)
Social (11.37%) and organic (11.18%) convert best; paid search (10.63%)
and direct (10.47%) convert worst. The spread here (~1 point) is much
smaller than the device spread (29 points) — device is the priority.

## 3. Hypothesis
**Why**: Mobile checkout likely has friction that desktop doesn't — a
longer form, harder-to-tap payment fields, or a lack of saved payment
methods/autofill. Without session-replay or heatmap data, this is a
reasoned hypothesis rather than a confirmed root cause, and would
normally be validated with qualitative research (session recordings,
a short user survey) before committing engineering time to a fix.

**If we...** simplify the mobile checkout flow (e.g., single-page
checkout, autofill/digital wallet support, fewer required fields)
**then...** mobile checkout-to-purchase conversion will increase,
**because...** we remove the friction causing intent-to-purchase users
to abandon at this specific step.

## 4. A/B Test Proposal

| Parameter | Value |
|---|---|
| **Unit of randomization** | User (mobile checkout sessions) |
| **Primary metric** | Checkout → Purchase conversion rate |
| **Guardrail metrics** | Average order value, refund rate, checkout load time |
| **Baseline conversion** | 42.75% |
| **Target MDE** | +5 percentage points (absolute) |
| **Significance level (α)** | 0.05 |
| **Power (1-β)** | 80% |
| **Required sample size** | 1,555 users per variant (3,110 total) |
| **Estimated duration** | ~37 days at current mobile checkout volume (~85/day) |

### Sample size sensitivity (from `analysis/ab_test_design.py`)
| MDE | Sample/variant | Est. duration |
|---|---|---|
| +2 pts | 9,657 | ~227 days |
| +3 pts | 4,302 | ~101 days |
| +5 pts | 1,555 | ~37 days |
| +8 pts | 610 | ~14 days |

**Recommendation**: target the +5pt MDE. Smaller effects (+2–3pt) would
take 3–7 months to detect at current traffic — too slow to be actionable.
An +8pt MDE runs fast but risks being underpowered to detect a real,
smaller improvement, and would waste a test slot if the true effect is
in the 3–5pt range.

## 5. Expected Impact (if test wins)
Using current mobile checkout volume (~85 users/day) and an illustrative
average order value:

- **+4.3 incremental purchases/day**
- **~$3,620 incremental revenue/day**
- **~$1.32M incremental revenue/year** at full mobile rollout

*(Average order value used here is illustrative — in a real deployment,
this would be pulled from actual payments data rather than assumed, since
the revenue projection is only as reliable as that input.)*

## 6. Risks & Caveats
- This dataset is synthetic, generated to demonstrate the analysis
  methodology end-to-end (see `data/generate_synthetic_data.py`) — the
  mobile/desktop gap was seeded deliberately to create a realistic,
  analyzable scenario. On real data, run the same SQL against actual
  event logs; the queries require no changes beyond the data source.
- Revenue projection assumes the effect holds at 100% rollout and ignores
  novelty effects (a redesigned checkout may see a temporary lift or dip
  that fades) — a real rollout would ramp gradually and re-measure.
- Sample size math assumes independent, roughly stable daily traffic;
  a pre-test check of day-of-week variance (see Query 5 in the SQL file)
  is recommended before committing to the ~37-day window.
