"""Generate synthetic orders data for the parity-check demo."""

import numpy as np
import pandas as pd

SEED = 42
START_DATE = "2026-01-01"
DAYS = 90
BASE_ORDERS_PER_DAY = 5_000

# Relative order volume by day of week: Monday=0 ... Sunday=6
DAY_OF_WEEK_FACTOR = [0.90, 0.90, 0.95, 1.00, 1.15, 1.35, 1.25]

# Relative order volume by hour: quiet overnight, peak in the evening
HOUR_WEIGHTS = np.array([
    1, 1, 1, 1, 1, 2,        # 00:00 to 05:59
    3, 4, 5, 6, 6, 7,        # 06:00 to 11:59
    8, 7, 6, 6, 7, 8,        # 12:00 to 17:59
    10, 12, 13, 12, 9, 5,    # 18:00 to 23:59
], dtype=float)
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()   # turn into probabilities that add up to 1

REGIONS = ["north", "south", "east", "west", "central"]
STATUSES = ["completed", "shipped", "cancelled", "returned"]
STATUS_WEIGHTS = [0.70, 0.20, 0.06, 0.04]
NULL_CUSTOMER_RATE = 0.02


def build_orders(seed: int = SEED) -> pd.DataFrame:
    """Return one DataFrame of orders. Same seed, same data, every time."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(START_DATE, periods=DAYS, freq="D")

    # 1. How many orders each day: base x weekday factor x a little noise
    factors = np.array([DAY_OF_WEEK_FACTOR[d.dayofweek] for d in days])
    noise = rng.normal(1.0, 0.05, size=DAYS)
    counts = np.round(BASE_ORDERS_PER_DAY * factors * noise).astype(int)
    n = int(counts.sum())

    # 2. When each order happened: its day, plus a random hour and second
    order_day = np.repeat(days.values, counts)
    hours = rng.choice(24, size=n, p=HOUR_WEIGHTS)
    seconds = rng.integers(0, 3600, size=n)
    order_ts = order_day + pd.to_timedelta(hours * 3600 + seconds, unit="s")

    # 3. Money as whole cents, long-tailed, at least $1.00
    revenue_cents = np.round(rng.lognormal(mean=3.6, sigma=0.8, size=n) * 100).astype(np.int64)
    revenue_cents = np.maximum(revenue_cents, 100)

    # 4. Customers, with about 2% missing
    customer_id = pd.array(rng.integers(1, 40_001, size=n), dtype="Int64")
    customer_id[rng.random(n) < NULL_CUSTOMER_RATE] = pd.NA

    df = pd.DataFrame({
        "order_ts": order_ts,
        "customer_id": customer_id,
        "revenue_cents": revenue_cents,
        "quantity": rng.choice([1, 2, 3, 4, 5], size=n, p=[0.55, 0.25, 0.10, 0.06, 0.04]),
        "status": rng.choice(STATUSES, size=n, p=STATUS_WEIGHTS),
        "region": rng.choice(REGIONS, size=n),
    })

    # 5. Sort by time, number the orders, derive the partition date
    df = df.sort_values("order_ts", kind="stable").reset_index(drop=True)
    df.insert(0, "order_id", np.arange(1, n + 1, dtype=np.int64))
    df["order_date"] = df["order_ts"].dt.date
    return df


if __name__ == "__main__":
    df = build_orders()
    print(df.head(10))
    print(f"\nrows: {len(df):,}")
    print(f"days: {df['order_date'].nunique()}")
    print(f"null customer_id: {df['customer_id'].isna().mean():.2%}")
    print("\norders by hour:")
    print(df["order_ts"].dt.hour.value_counts().sort_index())
    print("\norders by day of week:")
    print(df["order_ts"].dt.day_name().value_counts())