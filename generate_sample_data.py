"""Generate a realistic ~1500-row e-commerce sales dataset for demos."""
import os
import random
from datetime import date, timedelta
import pandas as pd
import numpy as np

random.seed(42)
np.random.seed(42)

PRODUCTS = ["Laptop Pro", "Wireless Mouse", "USB-C Hub", "Mechanical Keyboard",
            "4K Monitor", "Webcam HD", "Noise-Cancel Headphones", "Standing Desk",
            "Ergonomic Chair", "Smartphone", "Tablet", "Smartwatch"]
CATEGORIES = {
    "Laptop Pro": "Electronics", "Wireless Mouse": "Accessories",
    "USB-C Hub": "Accessories", "Mechanical Keyboard": "Accessories",
    "4K Monitor": "Electronics", "Webcam HD": "Accessories",
    "Noise-Cancel Headphones": "Audio", "Standing Desk": "Furniture",
    "Ergonomic Chair": "Furniture", "Smartphone": "Electronics",
    "Tablet": "Electronics", "Smartwatch": "Wearables",
}
REGIONS = ["North America", "Europe", "APAC", "LATAM"]
CHANNELS = ["Online", "Retail", "Partner"]
PRICES = {p: round(random.uniform(30, 1500), 2) for p in PRODUCTS}

rows = []
start = date.today() - timedelta(days=120)
for i in range(1500):
    d = start + timedelta(days=random.randint(0, 119))
    p = random.choice(PRODUCTS)
    qty = random.randint(1, 5)
    unit = PRICES[p] * random.uniform(0.85, 1.1)
    revenue = round(unit * qty, 2)
    rows.append({
        "order_id": 10000 + i,
        "order_date": d.isoformat(),
        "product": p,
        "category": CATEGORIES[p],
        "region": random.choice(REGIONS),
        "channel": random.choice(CHANNELS),
        "customer_id": f"CUST-{random.randint(1, 400):04d}",
        "quantity": qty,
        "unit_price": round(unit, 2),
        "revenue": revenue,
    })

# Inject some missing values & duplicates to exercise ETL
df = pd.DataFrame(rows)
for col in ("unit_price", "region"):
    idx = df.sample(frac=0.03).index
    df.loc[idx, col] = None
df = pd.concat([df, df.sample(15)], ignore_index=True)

out = os.path.join(os.path.dirname(__file__), "..", "data", "sample_data.csv")
out = os.path.abspath(out)
os.makedirs(os.path.dirname(out), exist_ok=True)
df.to_csv(out, index=False)
print(f"Wrote {len(df)} rows to {out}")
