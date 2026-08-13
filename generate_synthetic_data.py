"""
generate_synthetic_data.py

Generates a realistic e-commerce funnel event dataset:
    view_product -> add_to_cart -> begin_checkout -> purchase

Why synthetic: this project is designed to run offline / anywhere without
depending on a live Kaggle download. The generation logic bakes in a
realistic, non-obvious business problem (a mobile checkout friction point)
so the SQL analysis has a genuine finding to surface -- not a random walk.

To use a REAL dataset instead (e.g. Kaggle "Google Analytics Customer
Revenue" or "E-commerce Funnel Analysis"), just replace data/funnel_events.csv
with your own file matching this schema:
    user_id, session_id, event_time, event_name, device, traffic_source
and everything downstream (SQL + power calc) still works unchanged.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

N_USERS = 60000
START_DATE = datetime(2026, 4, 1)
DAYS = 90

DEVICES = ["mobile", "desktop", "tablet"]
DEVICE_WEIGHTS = [0.62, 0.32, 0.06]  # realistic e-commerce traffic split

SOURCES = ["organic", "paid_search", "social", "direct", "email"]
SOURCE_WEIGHTS = [0.35, 0.25, 0.15, 0.15, 0.10]

STAGES = ["view_product", "add_to_cart", "begin_checkout", "purchase"]

# Baseline stage-to-stage conversion rates, then adjusted per device below.
# The deliberate "finding": mobile has a much worse checkout->purchase
# conversion than desktop (simulating a real friction point, e.g. a clunky
# mobile payment form) -- this is what the funnel analysis should surface.
BASE_CONVERSION = {
    "view_to_cart": 0.38,
    "cart_to_checkout": 0.55,
    "checkout_to_purchase": 0.62,
}

DEVICE_ADJUSTMENT = {
    # multiplicative adjustment applied to checkout_to_purchase specifically
    "mobile": 0.70,   # mobile checkout converts much worse (the finding)
    "desktop": 1.15,
    "tablet": 0.95,
}

rows = []
user_id_counter = 1

for _ in range(N_USERS):
    user_id = f"u_{user_id_counter:07d}"
    user_id_counter += 1

    device = np.random.choice(DEVICES, p=DEVICE_WEIGHTS)
    source = np.random.choice(SOURCES, p=SOURCE_WEIGHTS)

    day_offset = np.random.randint(0, DAYS)
    session_start = START_DATE + timedelta(
        days=int(day_offset),
        hours=int(np.random.randint(0, 24)),
        minutes=int(np.random.randint(0, 60)),
    )
    session_id = f"s_{user_id}_{day_offset}"

    # Everyone in this dataset views a product (that's the funnel entry point)
    t = session_start
    rows.append((user_id, session_id, t, "view_product", device, source))

    if np.random.random() < BASE_CONVERSION["view_to_cart"]:
        t = t + timedelta(minutes=np.random.exponential(2))
        rows.append((user_id, session_id, t, "add_to_cart", device, source))

        if np.random.random() < BASE_CONVERSION["cart_to_checkout"]:
            t = t + timedelta(minutes=np.random.exponential(3))
            rows.append((user_id, session_id, t, "begin_checkout", device, source))

            checkout_rate = BASE_CONVERSION["checkout_to_purchase"] * DEVICE_ADJUSTMENT[device]
            checkout_rate = min(checkout_rate, 0.95)
            if np.random.random() < checkout_rate:
                t = t + timedelta(minutes=np.random.exponential(4))
                rows.append((user_id, session_id, t, "purchase", device, source))

df = pd.DataFrame(rows, columns=["user_id", "session_id", "event_time", "event_name", "device", "traffic_source"])
df = df.sort_values(["user_id", "event_time"]).reset_index(drop=True)

df.to_csv("funnel_events.csv", index=False)

print(f"Generated {len(df):,} events for {df['user_id'].nunique():,} users")
print(df["event_name"].value_counts())
