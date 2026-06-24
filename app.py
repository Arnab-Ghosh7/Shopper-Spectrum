"""
Shopper Spectrum - Streamlit web application.

Two modules:
  1. Product Recommendation  - item-based collaborative filtering
  2. Customer Segmentation    - RFM -> KMeans cluster prediction

Run:  streamlit run app.py
"""

from __future__ import annotations

import os
import json

import joblib
import numpy as np
import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ROOT, "models")
FIG_DIR = os.path.join(ROOT, "outputs", "figures")

st.set_page_config(
    page_title="Shopper Spectrum",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Styling
# --------------------------------------------------------------------------- #
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(160deg, #0f2027 0%, #16313a 55%, #1b3a4b 100%); }
    .block-container { padding-top: 2rem; max-width: 1180px; }
    h1, h2, h3, h4, p, label, span, div { color: #e9f1f4; }
    .hero {
        background: linear-gradient(110deg, #0c343d 0%, #1b6e7d 100%);
        border-radius: 18px; padding: 26px 34px; margin-bottom: 22px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    }
    .hero h1 { font-size: 2.35rem; margin: 0; font-weight: 800; letter-spacing:.5px; }
    .hero p { font-size: 1.02rem; opacity: .9; margin: 6px 0 0 0; }
    .metric-card {
        background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
        border-radius: 14px; padding: 16px 18px; text-align:center;
    }
    .metric-card .v { font-size: 1.7rem; font-weight: 800; color:#7fe3c0; }
    .metric-card .l { font-size: .82rem; opacity:.8; text-transform:uppercase; letter-spacing:1px; }
    .reco-card {
        background: rgba(255,255,255,0.07); border-left: 5px solid #2dd4a7;
        border-radius: 12px; padding: 14px 18px; margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25); transition: transform .15s ease;
    }
    .reco-card:hover { transform: translateX(4px); }
    .reco-card .rank { color:#2dd4a7; font-weight:800; margin-right:8px; }
    .reco-card .sim  { float:right; color:#9fb4bd; font-size:.85rem; }
    .seg-badge {
        display:inline-block; padding: 18px 30px; border-radius: 16px;
        font-size: 1.9rem; font-weight: 800; color:#fff; margin-top:8px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    }
    .stButton>button {
        background: linear-gradient(100deg,#2dd4a7,#1b9e7d); color:#06251f;
        font-weight:700; border:none; border-radius:10px; padding:.55rem 1.4rem;
    }
    .stButton>button:hover { filter:brightness(1.08); }
    div[data-testid="stSidebar"] { background:#0b2530; }
    </style>
    """,
    unsafe_allow_html=True,
)

SEGMENT_STYLE = {
    "High-Value":  {"color": "#2e7d32", "emoji": "💎",
                    "desc": "Regular, frequent, recent and big spenders. Your best customers — reward and retain them."},
    "Regular":     {"color": "#1565c0", "emoji": "🔄",
                    "desc": "Steady purchasers but not premium. Nurture with loyalty perks to move them up."},
    "Occasional":  {"color": "#f9a825", "emoji": "🌙",
                    "desc": "Rare, occasional purchases. Re-engage with targeted offers and reminders."},
    "At-Risk":     {"color": "#c62828", "emoji": "⚠️",
                    "desc": "Haven't purchased in a long time. Win-back campaigns are a priority."},
}


# --------------------------------------------------------------------------- #
# Artifact loading
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def load_artifacts():
    paths = {
        "scaler": "rfm_scaler.pkl",
        "kmeans": "kmeans_model.pkl",
        "labels": "cluster_labels.pkl",
        "sim": "product_similarity.pkl",
    }
    art = {}
    for key, fn in paths.items():
        fp = os.path.join(MODELS_DIR, fn)
        if not os.path.exists(fp):
            return None
        art[key] = joblib.load(fp)
    meta_fp = os.path.join(MODELS_DIR, "metadata.json")
    art["meta"] = json.load(open(meta_fp)) if os.path.exists(meta_fp) else {}
    rfm_fp = os.path.join(MODELS_DIR, "rfm_table.csv")
    art["rfm"] = pd.read_csv(rfm_fp) if os.path.exists(rfm_fp) else None
    return art


def predict_segment(art, recency, frequency, monetary):
    feats = pd.DataFrame(
        [[recency, np.log1p(frequency), np.log1p(monetary)]],
        columns=["Recency", "Frequency", "Monetary"],
    )
    X = art["scaler"].transform(feats)
    cluster = int(art["kmeans"].predict(X)[0])
    return art["labels"].get(cluster, f"Cluster {cluster}")


def recommend(art, product, n=5):
    sim = art["sim"]
    if product not in sim.index:
        return []
    scores = sim[product].drop(labels=[product]).sort_values(ascending=False)
    return list(zip(scores.head(n).index, scores.head(n).values))


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
def hero():
    st.markdown(
        """
        <div class="hero">
            <h1>🛒 Shopper Spectrum</h1>
            <p>Customer Segmentation &amp; Product Recommendations for E-Commerce</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(meta):
    s = meta.get("eda_stats", {})
    if not s:
        return
    cols = st.columns(4)
    cards = [
        ("Customers", f"{s.get('customers', 0):,}"),
        ("Products", f"{s.get('products', 0):,}"),
        ("Transactions", f"{s.get('transactions', 0):,}"),
        ("Revenue", f"£{s.get('total_revenue', 0):,.0f}"),
    ]
    for col, (label, val) in zip(cols, cards):
        col.markdown(
            f'<div class="metric-card"><div class="v">{val}</div>'
            f'<div class="l">{label}</div></div>',
            unsafe_allow_html=True,
        )


def page_recommend(art):
    st.subheader("🎯 Product Recommendation")
    st.caption("Enter a product name to get **5 similar products** based on "
               "item-based collaborative filtering (cosine similarity).")

    products = list(art["sim"].index)
    col1, col2 = st.columns([3, 1])
    with col1:
        product = st.selectbox("Product name", options=products,
                               index=0, placeholder="Choose a product...")
    with col2:
        st.write("")
        st.write("")
        go = st.button("Get Recommendations", use_container_width=True)

    if go and product:
        recs = recommend(art, product, n=5)
        if not recs:
            st.warning("No recommendations available for that product.")
            return
        st.markdown(f"#### Because customers bought **{product}**, they also liked:")
        for i, (name, score) in enumerate(recs, 1):
            st.markdown(
                f'<div class="reco-card"><span class="rank">#{i}</span>{name}'
                f'<span class="sim">similarity {score:.2f}</span></div>',
                unsafe_allow_html=True,
            )


def page_segment(art):
    st.subheader("👥 Customer Segmentation")
    st.caption("Enter a customer's RFM values to predict which behavioural "
               "segment they belong to.")

    c1, c2, c3 = st.columns(3)
    recency = c1.number_input("Recency (days since last purchase)",
                              min_value=0, max_value=1000, value=30, step=1)
    frequency = c2.number_input("Frequency (number of purchases)",
                                min_value=1, max_value=500, value=8, step=1)
    monetary = c3.number_input("Monetary (total spend)",
                               min_value=0.0, max_value=1_000_000.0,
                               value=1500.0, step=50.0)

    if st.button("Predict Cluster", use_container_width=False):
        seg = predict_segment(art, recency, frequency, monetary)
        style = SEGMENT_STYLE.get(seg, {"color": "#555", "emoji": "❓", "desc": ""})
        st.markdown(
            f'<div class="seg-badge" style="background:{style["color"]}">'
            f'{style["emoji"]} {seg}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f"**What this means:** {style['desc']}")

        if art["rfm"] is not None:
            seg_df = art["rfm"][art["rfm"]["Segment"] == seg]
            if len(seg_df):
                m1, m2, m3 = st.columns(3)
                m1.metric("Segment size", f"{len(seg_df):,} customers")
                m2.metric("Avg. frequency", f"{seg_df['Frequency'].mean():.1f}")
                m3.metric("Avg. monetary", f"£{seg_df['Monetary'].mean():,.0f}")


def page_insights(art):
    st.subheader("📊 Data & Model Insights")
    meta = art.get("meta", {})

    if art["rfm"] is not None:
        seg_counts = art["rfm"]["Segment"].value_counts()
        order = ["High-Value", "Regular", "Occasional", "At-Risk"]
        seg_counts = seg_counts.reindex([s for s in order if s in seg_counts.index])
        st.markdown("#### Customer segment distribution")
        st.bar_chart(seg_counts)

    figs = [
        ("Cluster selection (Elbow & Silhouette)", "cluster_selection.png"),
        ("Customer segments in RFM space", "cluster_2d.png"),
        ("RFM distributions", "rfm_distributions.png"),
        ("Monthly revenue trend", "revenue_trend.png"),
        ("Top countries", "top_countries.png"),
        ("Top products", "top_products.png"),
    ]
    cols = st.columns(2)
    for i, (title, fn) in enumerate(figs):
        fp = os.path.join(FIG_DIR, fn)
        if os.path.exists(fp):
            with cols[i % 2]:
                st.markdown(f"**{title}**")
                st.image(fp, use_container_width=True)


def main():
    hero()
    art = load_artifacts()

    if art is None:
        st.error("⚠️ Model artifacts not found. Please run the training "
                 "pipeline first:")
        st.code("python -m src.train", language="bash")
        st.stop()

    render_metrics(art.get("meta", {}))
    st.write("")

    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        page = st.radio(
            "Go to",
            ["🎯 Product Recommendation", "👥 Customer Segmentation", "📊 Insights"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown("### About")
        st.caption(
            "Shopper Spectrum analyses e-commerce transaction data to segment "
            "customers via **RFM + KMeans** and recommend products via "
            "**item-based collaborative filtering**."
        )
        meta = art.get("meta", {})
        if meta.get("cluster_diagnostics"):
            st.caption(f"Clusters (k): **{meta['cluster_diagnostics']['chosen_k']}**")
        if meta.get("n_products_in_recommender"):
            st.caption(f"Products in recommender: **{meta['n_products_in_recommender']:,}**")

    if page.startswith("🎯"):
        page_recommend(art)
    elif page.startswith("👥"):
        page_segment(art)
    else:
        page_insights(art)

    st.markdown("---")
    st.caption("Shopper Spectrum · Customer Segmentation & Product "
               "Recommendations · Built with Streamlit & scikit-learn")


if __name__ == "__main__":
    main()
