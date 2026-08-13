"""
ab_test_design.py

Given the funnel finding (mobile checkout->purchase conversion is far
below desktop), this script:
  1. Frames the A/B test hypothesis
  2. Calculates required sample size for a given Minimum Detectable
     Effect (MDE) using the standard two-proportion z-test power formula
  3. Estimates how long the test would need to run given current mobile
     checkout traffic
  4. Projects expected revenue impact if the test wins

Uses only scipy (no statsmodels dependency) so it runs anywhere.
"""

import scipy.stats as st
import math

# ------------------------------------------------------------------
# 1. Inputs pulled directly from the SQL funnel analysis results
# ------------------------------------------------------------------
BASELINE_CONVERSION = 0.4275      # mobile checkout -> purchase (from funnel_analysis.sql, Query 2)
MDE_ABSOLUTE = 0.05               # target: detect a 5-point lift (42.75% -> 47.75%)
ALPHA = 0.05                      # significance level (two-tailed)
POWER = 0.80                      # standard 80% power

DAILY_MOBILE_CHECKOUT_USERS = 7666 / 90   # from funnel_analysis.sql Query 2, over the 90-day window
AVG_ORDER_VALUE = 850              # illustrative; replace with real AOV from payments data


def sample_size_two_proportions(p1, mde, alpha=0.05, power=0.80):
    """
    Standard sample-size formula for a two-proportion z-test.
    Returns required sample size PER VARIANT.
    """
    p2 = p1 + mde
    z_alpha = st.norm.ppf(1 - alpha / 2)
    z_beta = st.norm.ppf(power)

    p_bar = (p1 + p2) / 2
    numerator = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) +
                 z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = mde ** 2
    n = numerator / denominator
    return math.ceil(n)


def two_proportion_z_test(conv_a, n_a, conv_b, n_b):
    """Post-hoc significance check (used once real test data comes in)."""
    successes_a, successes_b = conv_a * n_a, conv_b * n_b
    p_pool = (successes_a + successes_b) / (n_a + n_b)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
    z = (conv_b - conv_a) / se
    p_value = 2 * (1 - st.norm.cdf(abs(z)))
    return z, p_value


if __name__ == "__main__":
    print("=" * 60)
    print("A/B TEST DESIGN: Mobile Checkout Optimization")
    print("=" * 60)
    print(f"\nBaseline (mobile checkout->purchase): {BASELINE_CONVERSION:.2%}")
    print(f"Target MDE (absolute): +{MDE_ABSOLUTE:.2%}")

    n_per_variant = sample_size_two_proportions(BASELINE_CONVERSION, MDE_ABSOLUTE, ALPHA, POWER)
    print(f"\nRequired sample size per variant: {n_per_variant:,} mobile checkout sessions")
    print(f"Total sample size (both variants): {n_per_variant * 2:,}")

    days_needed = (n_per_variant * 2) / DAILY_MOBILE_CHECKOUT_USERS
    print(f"\nCurrent daily mobile checkout volume: ~{DAILY_MOBILE_CHECKOUT_USERS:.0f} users/day")
    print(f"Estimated test duration: ~{days_needed:.0f} days (~{days_needed/7:.1f} weeks)")

    # Expected impact if the test wins at the targeted MDE
    incremental_conversions_per_day = DAILY_MOBILE_CHECKOUT_USERS * MDE_ABSOLUTE
    incremental_revenue_per_day = incremental_conversions_per_day * AVG_ORDER_VALUE
    incremental_revenue_annual = incremental_revenue_per_day * 365

    print(f"\n--- Expected impact if test wins (at full mobile rollout) ---")
    print(f"Incremental purchases/day: ~{incremental_conversions_per_day:.1f}")
    print(f"Incremental revenue/day: ~${incremental_revenue_per_day:,.0f}")
    print(f"Incremental revenue/year (projected): ~${incremental_revenue_annual:,.0f}")

    # Sensitivity: sample size at a few different MDEs, for the write-up table
    print(f"\n--- Sample size sensitivity to MDE ---")
    for mde in [0.02, 0.03, 0.05, 0.08]:
        n = sample_size_two_proportions(BASELINE_CONVERSION, mde, ALPHA, POWER)
        days = (n * 2) / DAILY_MOBILE_CHECKOUT_USERS
        print(f"MDE=+{mde:.0%}: n/variant={n:,}, total={n*2:,}, ~{days:.0f} days")
