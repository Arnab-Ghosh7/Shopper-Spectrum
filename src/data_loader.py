"""
Data loading utilities for Shopper Spectrum.

The pipeline works with the classic "Online Retail" transactional schema:
    InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice,
    CustomerID, Country

If a real dataset is dropped into the ``data/`` folder (``.csv`` or ``.xlsx``)
it is used automatically. Otherwise a realistic synthetic dataset is generated
so the whole project runs end-to-end out of the box.
"""

from __future__ import annotations

import os
import glob
import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

EXPECTED_COLUMNS = [
    "InvoiceNo", "StockCode", "Description", "Quantity",
    "InvoiceDate", "UnitPrice", "CustomerID", "Country",
]


def find_dataset() -> str | None:
    """Return the path to a user-provided dataset if one exists in data/."""
    if not os.path.isdir(DATA_DIR):
        return None
    candidates = []
    for ext in ("*.csv", "*.xlsx", "*.xls"):
        candidates.extend(glob.glob(os.path.join(DATA_DIR, ext)))
    # Ignore the synthetic file we generate ourselves
    candidates = [c for c in candidates if "synthetic" not in os.path.basename(c).lower()]
    return candidates[0] if candidates else None


def load_real_dataset(path: str) -> pd.DataFrame:
    """Load a user-provided Online Retail dataset from CSV or Excel."""
    if path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path)
    else:
        # The UCI file is latin-1 encoded; fall back gracefully.
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin-1")
    # Normalise common column-name variants.
    rename = {
        "Invoice": "InvoiceNo",
        "Customer ID": "CustomerID",
        "Price": "UnitPrice",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    return df


# --------------------------------------------------------------------------- #
# Synthetic data generation
# --------------------------------------------------------------------------- #
PRODUCT_CATALOG = [
    ("85123A", "WHITE HANGING HEART T-LIGHT HOLDER", 2.55),
    ("71053", "WHITE METAL LANTERN", 3.39),
    ("84406B", "CREAM CUPID HEARTS COAT HANGER", 2.75),
    ("84029G", "KNITTED UNION FLAG HOT WATER BOTTLE", 3.39),
    ("84029E", "RED WOOLLY HOTTIE WHITE HEART", 3.39),
    ("22752", "SET 7 BABUSHKA NESTING BOXES", 7.65),
    ("21730", "GLASS STAR FROSTED T-LIGHT HOLDER", 4.25),
    ("22633", "HAND WARMER UNION JACK", 1.85),
    ("22632", "HAND WARMER RED POLKA DOT", 1.85),
    ("84879", "ASSORTED COLOUR BIRD ORNAMENT", 1.69),
    ("22745", "POPPY'S PLAYHOUSE BEDROOM", 2.10),
    ("22748", "POPPY'S PLAYHOUSE KITCHEN", 2.10),
    ("22749", "FELTCRAFT PRINCESS CHARLOTTE DOLL", 3.75),
    ("22310", "IVORY KNITTED MUG COSY", 1.65),
    ("84969", "BOX OF 6 ASSORTED COLOUR TEASPOONS", 4.25),
    ("22623", "BOX OF VINTAGE JIGSAW BLOCKS", 5.95),
    ("22622", "BOX OF VINTAGE ALPHABET BLOCKS", 9.95),
    ("21754", "HOME BUILDING BLOCK WORD", 5.95),
    ("21755", "LOVE BUILDING BLOCK WORD", 5.95),
    ("21777", "RECIPE BOX WITH METAL HEART", 7.95),
    ("48187", "DOORMAT NEW ENGLAND", 7.95),
    ("22960", "JAM MAKING SET WITH JARS", 4.25),
    ("22961", "JAM MAKING SET PRINTED", 1.45),
    ("22912", "YELLOW COAT RACK PARIS FASHION", 4.95),
    ("22913", "RED COAT RACK PARIS FASHION", 4.95),
    ("22914", "BLUE COAT RACK PARIS FASHION", 4.95),
    ("21703", "BAG 125g SWIRLY MARBLES", 0.85),
    ("21704", "BAG 250g SWIRLY MARBLES", 1.65),
    ("84970S", "HANGING HEART ZINC T-LIGHT HOLDER", 0.85),
    ("22086", "PAPER CHAIN KIT 50'S CHRISTMAS", 2.55),
    ("21824", "PAINTED METAL STAR WITH HOLLY BELLS", 0.39),
    ("21731", "RED TOADSTOOL LED NIGHT LIGHT", 1.65),
    ("22466", "FAIRY TALE COTTAGE NIGHT LIGHT", 4.95),
    ("85099B", "JUMBO BAG RED RETROSPOT", 1.95),
    ("85099C", "JUMBO BAG BAROQUE BLACK WHITE", 1.95),
    ("20725", "LUNCH BAG RED RETROSPOT", 1.65),
    ("20727", "LUNCH BAG BLACK SKULL", 1.65),
    ("22384", "LUNCH BAG PINK POLKADOT", 1.65),
    ("23203", "JUMBO BAG VINTAGE DOILY", 2.08),
    ("47566", "PARTY BUNTING", 4.95),
    ("23084", "RABBIT NIGHT LIGHT", 2.08),
    ("22693", "GROW A FLYTRAP OR SUNFLOWER IN TIN", 1.25),
    ("15036", "ASSORTED COLOURS SILK FAN", 0.85),
    ("22697", "GREEN REGENCY TEACUP AND SAUCER", 2.95),
    ("22698", "PINK REGENCY TEACUP AND SAUCER", 2.95),
    ("22699", "ROSES REGENCY TEACUP AND SAUCER", 2.95),
    ("23298", "SPOTTY BUNTING", 4.95),
    ("22423", "REGENCY CAKESTAND 3 TIER", 12.75),
    ("48194", "DOORMAT HEARTS", 7.95),
    ("21212", "PACK OF 72 RETROSPOT CAKE CASES", 0.55),
]

COUNTRIES = [
    ("United Kingdom", 0.70), ("Germany", 0.06), ("France", 0.05),
    ("EIRE", 0.04), ("Spain", 0.03), ("Netherlands", 0.03),
    ("Belgium", 0.02), ("Switzerland", 0.02), ("Portugal", 0.02),
    ("Australia", 0.015), ("Norway", 0.015), ("Italy", 0.01),
    ("Channel Islands", 0.01), ("Finland", 0.01),
]


def generate_synthetic_dataset(n_customers: int = 1500,
                               seed: int = 42) -> pd.DataFrame:
    """Generate a realistic Online-Retail-style transactional dataset.

    Customers are drawn from latent behavioural archetypes (loyal, regular,
    occasional, at-risk, one-off) so that downstream RFM clustering finds
    genuine, interpretable structure.
    """
    rng = np.random.default_rng(seed)

    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2023-12-31")
    span_days = (end - start).days

    countries, country_p = zip(*COUNTRIES)
    country_p = np.array(country_p) / np.sum(country_p)

    # Behavioural archetypes: (n_orders_lambda, recency_bias, basket_size, qty_scale)
    archetypes = {
        "loyal":      dict(weight=0.18, orders=(8, 20),  recency=(0, 40),   basket=(4, 9),  qty=(4, 14)),
        "regular":    dict(weight=0.30, orders=(4, 9),   recency=(0, 120),  basket=(3, 7),  qty=(2, 9)),
        "occasional": dict(weight=0.27, orders=(2, 4),   recency=(120, 400),basket=(2, 5),  qty=(1, 6)),
        "at_risk":    dict(weight=0.15, orders=(3, 8),   recency=(300, 700),basket=(3, 6),  qty=(2, 8)),
        "one_off":    dict(weight=0.10, orders=(1, 2),   recency=(0, 700),  basket=(1, 3),  qty=(1, 4)),
    }
    names = list(archetypes.keys())
    weights = np.array([archetypes[n]["weight"] for n in names])
    weights = weights / weights.sum()

    rows = []
    invoice_no = 536000
    prod_codes = [p[0] for p in PRODUCT_CATALOG]
    prod_desc = {p[0]: p[1] for p in PRODUCT_CATALOG}
    prod_price = {p[0]: p[2] for p in PRODUCT_CATALOG}
    # Make some products much more popular (long-tail demand)
    pop = rng.power(0.35, size=len(prod_codes)) + 0.02
    pop = pop / pop.sum()

    for cust_idx in range(n_customers):
        customer_id = 12000 + cust_idx
        arch_name = rng.choice(names, p=weights)
        arch = archetypes[arch_name]
        country = rng.choice(countries, p=country_p)

        n_orders = rng.integers(arch["orders"][0], arch["orders"][1] + 1)
        # Most recent order date implied by recency bias
        last_recency = rng.integers(arch["recency"][0], arch["recency"][1] + 1)
        last_order_date = end - pd.Timedelta(days=int(min(last_recency, span_days)))

        # Spread the earlier orders backwards in time
        if n_orders > 1:
            offsets = np.sort(rng.integers(0, max(span_days - last_recency, 1), size=n_orders - 1))[::-1]
            order_dates = [last_order_date - pd.Timedelta(days=int(o)) for o in offsets]
            order_dates.append(last_order_date)
        else:
            order_dates = [last_order_date]

        for od in order_dates:
            invoice_no += 1
            is_cancelled = rng.random() < 0.015  # ~1.5% cancelled invoices
            inv = ("C" + str(invoice_no)) if is_cancelled else str(invoice_no)
            # random time of day
            ts = od + pd.Timedelta(hours=int(rng.integers(7, 20)),
                                   minutes=int(rng.integers(0, 60)))
            basket = rng.integers(arch["basket"][0], arch["basket"][1] + 1)
            chosen = rng.choice(prod_codes, size=basket, replace=False, p=pop)
            for code in chosen:
                qty = int(rng.integers(arch["qty"][0], arch["qty"][1] + 1))
                if is_cancelled:
                    qty = -qty
                # small price jitter
                price = round(prod_price[code] * rng.uniform(0.95, 1.1), 2)
                rows.append((inv, code, prod_desc[code], qty, ts, price,
                             customer_id, country))

    # Inject a little realistic dirtiness: missing CustomerIDs and zero prices
    df = pd.DataFrame(rows, columns=EXPECTED_COLUMNS)
    dirty_idx = rng.choice(df.index, size=int(len(df) * 0.02), replace=False)
    df.loc[dirty_idx[: len(dirty_idx) // 2], "CustomerID"] = np.nan
    df.loc[dirty_idx[len(dirty_idx) // 2:], "UnitPrice"] = 0.0

    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def get_dataset(verbose: bool = True) -> pd.DataFrame:
    """Return the working dataset (real if available, else synthetic)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    real = find_dataset()
    if real:
        if verbose:
            print(f"[data] Using real dataset: {real}")
        return load_real_dataset(real)

    synth_path = os.path.join(DATA_DIR, "online_retail_synthetic.csv")
    if os.path.exists(synth_path):
        if verbose:
            print(f"[data] Using cached synthetic dataset: {synth_path}")
        return pd.read_csv(synth_path, parse_dates=["InvoiceDate"])

    if verbose:
        print("[data] No dataset found - generating synthetic Online Retail data...")
    df = generate_synthetic_dataset()
    df.to_csv(synth_path, index=False)
    if verbose:
        print(f"[data] Synthetic dataset written to {synth_path} "
              f"({len(df):,} rows)")
    return df


if __name__ == "__main__":
    data = get_dataset()
    print(data.head())
    print(data.shape)
