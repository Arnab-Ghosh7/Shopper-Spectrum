"""
Training pipeline for Shopper Spectrum.

Runs the full workflow:
  1. Load + clean data
  2. EDA visualisations  -> outputs/figures
  3. RFM feature engineering + scaling
  4. KMeans clustering (elbow + silhouette to choose k)
  5. Cluster labelling (High-Value / Regular / Occasional / At-Risk)
  6. Item-based collaborative-filtering similarity matrix
  7. Persist all artifacts -> models/

Run:  python -m src.train     (from project root, with the venv active)
"""

from __future__ import annotations

import os
import json
import warnings

import joblib
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

from .data_loader import get_dataset
from .preprocessing import clean_transactions, build_rfm

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT, "models")
FIG_DIR = os.path.join(ROOT, "outputs", "figures")

SEGMENT_PALETTE = {
    "High-Value": "#2e7d32",
    "Regular": "#1565c0",
    "Occasional": "#f9a825",
    "At-Risk": "#c62828",
}


def _ensure_dirs():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)


# --------------------------------------------------------------------------- #
# EDA
# --------------------------------------------------------------------------- #
def run_eda(df: pd.DataFrame) -> dict:
    print("[eda] Generating exploratory visualisations...")
    stats = {
        "transactions": int(df["InvoiceNo"].nunique()),
        "customers": int(df["CustomerID"].nunique()),
        "products": int(df["StockCode"].nunique()),
        "countries": int(df["Country"].nunique()),
        "total_revenue": float(df["TotalPrice"].sum()),
        "date_min": str(df["InvoiceDate"].min().date()),
        "date_max": str(df["InvoiceDate"].max().date()),
    }

    # Top countries by transaction volume
    top_countries = (df.groupby("Country")["InvoiceNo"].nunique()
                       .sort_values(ascending=False).head(10))
    plt.figure(figsize=(9, 5))
    sns.barplot(x=top_countries.values, y=top_countries.index, color="#1565c0")
    plt.title("Top 10 Countries by Transaction Volume")
    plt.xlabel("Number of Invoices"); plt.ylabel("")
    plt.tight_layout(); plt.savefig(os.path.join(FIG_DIR, "top_countries.png"), dpi=110)
    plt.close()

    # Top selling products
    top_products = (df.groupby("Description")["Quantity"].sum()
                      .sort_values(ascending=False).head(10))
    plt.figure(figsize=(9, 5))
    sns.barplot(x=top_products.values, y=top_products.index, color="#2e7d32")
    plt.title("Top 10 Best-Selling Products (by Quantity)")
    plt.xlabel("Units Sold"); plt.ylabel("")
    plt.tight_layout(); plt.savefig(os.path.join(FIG_DIR, "top_products.png"), dpi=110)
    plt.close()

    # Purchase trend over time
    monthly = (df.set_index("InvoiceDate")
                 .resample("ME")["TotalPrice"].sum())
    plt.figure(figsize=(10, 4.5))
    plt.plot(monthly.index, monthly.values, marker="o", color="#6a1b9a")
    plt.fill_between(monthly.index, monthly.values, alpha=0.15, color="#6a1b9a")
    plt.title("Monthly Revenue Trend")
    plt.ylabel("Revenue"); plt.xlabel("")
    plt.tight_layout(); plt.savefig(os.path.join(FIG_DIR, "revenue_trend.png"), dpi=110)
    plt.close()

    # Monetary distribution per transaction
    inv_totals = df.groupby("InvoiceNo")["TotalPrice"].sum()
    plt.figure(figsize=(9, 4.5))
    sns.histplot(inv_totals.clip(upper=inv_totals.quantile(0.99)),
                 bins=50, color="#ef6c00")
    plt.title("Distribution of Transaction Value (99th pct capped)")
    plt.xlabel("Invoice Total"); plt.ylabel("Count")
    plt.tight_layout(); plt.savefig(os.path.join(FIG_DIR, "transaction_value.png"), dpi=110)
    plt.close()

    return stats


def plot_rfm_distributions(rfm: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, col, color in zip(axes, ["Recency", "Frequency", "Monetary"],
                              ["#c62828", "#1565c0", "#2e7d32"]):
        data = rfm[col]
        if col == "Monetary":
            data = data.clip(upper=data.quantile(0.99))
        sns.histplot(data, bins=40, color=color, ax=ax)
        ax.set_title(f"{col} Distribution")
    plt.tight_layout(); plt.savefig(os.path.join(FIG_DIR, "rfm_distributions.png"), dpi=110)
    plt.close()


# --------------------------------------------------------------------------- #
# Clustering
# --------------------------------------------------------------------------- #
def choose_k(X: np.ndarray, k_range=range(2, 11), prefer_k: int = 4) -> tuple[int, dict]:
    inertias, silhouettes = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X, labels))

    # Elbow + silhouette plots
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.5))
    a1.plot(list(k_range), inertias, "o-", color="#1565c0")
    a1.set_title("Elbow Method (Inertia)"); a1.set_xlabel("k"); a1.set_ylabel("Inertia")
    a2.plot(list(k_range), silhouettes, "o-", color="#2e7d32")
    a2.set_title("Silhouette Score by k"); a2.set_xlabel("k"); a2.set_ylabel("Silhouette")
    plt.tight_layout(); plt.savefig(os.path.join(FIG_DIR, "cluster_selection.png"), dpi=110)
    plt.close()

    sil_best_k = list(k_range)[int(np.argmax(silhouettes))]
    # The project brief defines four customer segments (High-Value, Regular,
    # Occasional, At-Risk), so we anchor on k=4 when it is available, while
    # still reporting the silhouette-optimal k in the diagnostics.
    best_k = prefer_k if prefer_k in k_range else sil_best_k
    diag = {"k_range": list(k_range), "inertias": inertias,
            "silhouettes": silhouettes, "chosen_k": int(best_k),
            "silhouette_best_k": int(sil_best_k)}
    return best_k, diag


def label_clusters(rfm: pd.DataFrame, centers_df: pd.DataFrame) -> dict:
    """Map cluster ids to business segment names using RFM averages.

    Scores each cluster by (low recency good, high frequency good,
    high monetary good) and assigns the four brief segments in rank order.
    """
    c = centers_df.copy()
    # Normalised desirability score: lower recency better -> invert
    r = (c["Recency"].max() - c["Recency"]) / (c["Recency"].max() - c["Recency"].min() + 1e-9)
    f = (c["Frequency"] - c["Frequency"].min()) / (c["Frequency"].max() - c["Frequency"].min() + 1e-9)
    m = (c["Monetary"] - c["Monetary"].min()) / (c["Monetary"].max() - c["Monetary"].min() + 1e-9)
    c["score"] = 0.30 * r + 0.30 * f + 0.40 * m
    order = c.sort_values("score", ascending=False).index.tolist()

    k = len(order)
    if k == 4:
        names = ["High-Value", "Regular", "Occasional", "At-Risk"]
    else:
        # Generic fallback for any k: best -> High-Value, worst -> At-Risk
        names = ["High-Value"] + ["Regular"] * max(0, k - 2) + (["At-Risk"] if k >= 2 else [])
        names = names[:k]
        while len(names) < k:
            names.insert(1, "Occasional")

    mapping = {int(cluster_id): names[i] for i, cluster_id in enumerate(order)}
    return mapping


def plot_clusters(rfm: pd.DataFrame):
    fig = plt.figure(figsize=(8.5, 6.5))
    ax = fig.add_subplot(111, projection="3d")
    for seg, color in SEGMENT_PALETTE.items():
        sub = rfm[rfm["Segment"] == seg]
        if len(sub):
            ax.scatter(sub["Recency"], sub["Frequency"],
                       sub["Monetary"].clip(upper=rfm["Monetary"].quantile(0.98)),
                       s=18, alpha=0.6, label=seg, color=color)
    ax.set_xlabel("Recency"); ax.set_ylabel("Frequency"); ax.set_zlabel("Monetary")
    ax.set_title("Customer Segments in RFM Space")
    ax.legend()
    plt.tight_layout(); plt.savefig(os.path.join(FIG_DIR, "cluster_3d.png"), dpi=110)
    plt.close()

    # 2D snapshot: Recency vs Monetary
    plt.figure(figsize=(8, 5.5))
    for seg, color in SEGMENT_PALETTE.items():
        sub = rfm[rfm["Segment"] == seg]
        plt.scatter(sub["Recency"], sub["Monetary"].clip(upper=rfm["Monetary"].quantile(0.98)),
                    s=16, alpha=0.6, label=seg, color=color)
    plt.xlabel("Recency (days)"); plt.ylabel("Monetary")
    plt.title("Segments: Recency vs Monetary"); plt.legend()
    plt.tight_layout(); plt.savefig(os.path.join(FIG_DIR, "cluster_2d.png"), dpi=110)
    plt.close()


# --------------------------------------------------------------------------- #
# Recommender
# --------------------------------------------------------------------------- #
def build_recommender(df: pd.DataFrame, max_products: int = 800):
    """Item-based collaborative filtering on a Customer x Product matrix."""
    print("[reco] Building item-based collaborative-filtering model...")
    # Keep the most popular products to bound memory / noise.
    top = (df.groupby("Description")["Quantity"].sum()
             .sort_values(ascending=False).head(max_products).index)
    sub = df[df["Description"].isin(top)]

    # Customer x Product purchase matrix (binary-ish quantities)
    pivot = sub.pivot_table(index="CustomerID", columns="Description",
                            values="Quantity", aggfunc="sum", fill_value=0)
    # Item vectors = columns
    item_matrix = csr_matrix(pivot.T.values)
    sim = cosine_similarity(item_matrix)
    products = list(pivot.columns)
    sim_df = pd.DataFrame(sim, index=products, columns=products)
    return sim_df


def recommend_products(sim_df: pd.DataFrame, product: str, n: int = 5):
    if product not in sim_df.index:
        return []
    scores = sim_df[product].drop(labels=[product]).sort_values(ascending=False)
    return list(zip(scores.head(n).index, scores.head(n).values))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    _ensure_dirs()
    print("=" * 64)
    print(" SHOPPER SPECTRUM - Training pipeline")
    print("=" * 64)

    raw = get_dataset()
    df = clean_transactions(raw)
    print(f"[clean] {df.attrs['clean_report']}")

    eda_stats = run_eda(df)
    print(f"[eda] {eda_stats}")

    # RFM
    rfm = build_rfm(df)
    plot_rfm_distributions(rfm)

    # Log-transform skewed features before scaling for stabler clusters
    rfm_features = rfm[["Recency", "Frequency", "Monetary"]].copy()
    rfm_log = rfm_features.copy()
    rfm_log["Frequency"] = np.log1p(rfm_log["Frequency"])
    rfm_log["Monetary"] = np.log1p(rfm_log["Monetary"])

    scaler = StandardScaler()
    X = scaler.fit_transform(rfm_log)

    best_k, diag = choose_k(X)
    print(f"[cluster] chosen k = {best_k} "
          f"(brief's 4-segment scheme; silhouette-optimal k = {diag['silhouette_best_k']})")

    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    rfm["Cluster"] = km.fit_predict(X)

    # Cluster centers back in original RFM units
    centers_df = rfm.groupby("Cluster")[["Recency", "Frequency", "Monetary"]].mean()
    mapping = label_clusters(rfm, centers_df)
    rfm["Segment"] = rfm["Cluster"].map(mapping)

    plot_clusters(rfm)

    seg_summary = (rfm.groupby("Segment")
                      .agg(Customers=("CustomerID", "count"),
                           Avg_Recency=("Recency", "mean"),
                           Avg_Frequency=("Frequency", "mean"),
                           Avg_Monetary=("Monetary", "mean"))
                      .round(1))
    print("\n[segments]\n", seg_summary)

    # Recommender
    sim_df = build_recommender(df)

    # ------------------------------------------------------------------ #
    # Persist artifacts
    # ------------------------------------------------------------------ #
    joblib.dump(scaler, os.path.join(MODELS_DIR, "rfm_scaler.pkl"))
    joblib.dump(km, os.path.join(MODELS_DIR, "kmeans_model.pkl"))
    joblib.dump(mapping, os.path.join(MODELS_DIR, "cluster_labels.pkl"))
    joblib.dump(sim_df, os.path.join(MODELS_DIR, "product_similarity.pkl"))
    rfm.to_csv(os.path.join(MODELS_DIR, "rfm_table.csv"), index=False)

    metadata = {
        "eda_stats": eda_stats,
        "cluster_diagnostics": diag,
        "segment_summary": json.loads(seg_summary.reset_index().to_json(orient="records")),
        "segment_order": ["High-Value", "Regular", "Occasional", "At-Risk"],
        "n_products_in_recommender": int(sim_df.shape[0]),
        "feature_transform": "log1p on Frequency & Monetary, then StandardScaler",
    }
    with open(os.path.join(MODELS_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    # Quick sanity demo
    demo_product = sim_df.index[0]
    print(f"\n[reco] Example recommendations for '{demo_product}':")
    for name, score in recommend_products(sim_df, demo_product):
        print(f"    - {name}  ({score:.3f})")

    print("\n[done] All artifacts saved to models/ and figures to outputs/figures/")


if __name__ == "__main__":
    main()
