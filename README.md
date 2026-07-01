# 🛒 Shopper Spectrum
### Customer Segmentation and Product Recommendations in E-Commerce


---

## 📁 Project structure

```
Shopper Spectrum/
├── app.py                     # Streamlit web application (2 modules + insights)
├── requirements.txt           # Python dependencies
├── venv/                      # Virtual environment (created locally)
├── data/                      # Dataset (auto-generated synthetic, or drop your own)
├── models/                    # Saved artifacts (scaler, kmeans, labels, similarity)
├── outputs/figures/           # EDA & clustering visualisations
├── notebooks/
│   └── analysis.ipynb         # Walk-through notebook
└── src/
    ├── data_loader.py         # Loads real data or generates realistic synthetic data
    ├── preprocessing.py       # Cleaning + RFM feature engineering
    └── train.py               # Full pipeline: EDA → RFM → KMeans → recommender
```

---

## 🚀 Quick start

The virtual environment and dependencies are already set up. From the project folder:

### 1. Activate the environment

PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
Command Prompt:
```cmd
venv\Scripts\activate.bat
```

> If you ever need to recreate it: `python -m venv venv` then
> `pip install -r requirements.txt`

### 2. Train the models (already done once, re-run any time)

```powershell
python -m src.train
```

This cleans the data, runs EDA, builds the RFM table, picks the best `k` via
the elbow method + silhouette score, labels the clusters, builds the
recommender, and saves everything to `models/` and `outputs/figures/`.

### 3. Launch the web app

```powershell
streamlit run app.py
```

Then open the URL it prints (default `http://localhost:8501`).

---

## 📊 Dataset

The project is trained on the real **Online Retail** dataset referenced in the
project brief (~542k transactions). It lives at `data/online_retail.csv`.

To re-download it from the brief's Google Drive link:

```powershell
pip install gdown
python -c "import gdown; gdown.download(id='1rzRwxm_CJxcRzfoo9Ix37A2JTlMummY-', output='data/online_retail.csv', quiet=False)"
```

The loader auto-detects any `.csv`/`.xlsx` in `data/`. If no real file is
present, it falls back to **generating a realistic synthetic dataset** so the
project still runs out of the box. Either way the expected schema is:

| Column | Description |
|--------|-------------|
| `InvoiceNo` | Transaction number |
| `StockCode` | Unique product/item code |
| `Description` | Name of the product |
| `Quantity` | Number of products purchased |
| `InvoiceDate` | Date and time of transaction |
| `UnitPrice` | Price per product |
| `CustomerID` | Unique identifier for each customer |
| `Country` | Country where the customer is based |

Then re-run `python -m src.train`. The loader picks up your file automatically.

---

## 🧮 Methodology

**Data preprocessing**
- Remove rows with missing `CustomerID`
- Exclude cancelled invoices (`InvoiceNo` starting with `C`)
- Remove negative or zero quantities and prices

**RFM feature engineering**
- `Recency`  = snapshot date − customer's last purchase date
- `Frequency` = number of distinct invoices per customer
- `Monetary`  = total amount spent by customer
- `log1p` transform on Frequency & Monetary, then `StandardScaler`

**Clustering** — KMeans. The elbow and silhouette curves are computed and saved
for reference; the model is anchored to **k = 4** to match the brief's four
business segments. Clusters are scored on RFM desirability and mapped to
High-Value / Regular / Occasional / At-Risk.

**Recommendation** — item-based collaborative filtering: a customer × product
purchase matrix → cosine similarity between products → top-5 most similar items.

---

## 🎯 Streamlit app features

- **Product Recommendation** — type a product name → get 5 similar products as styled cards.
- **Customer Segmentation** — enter Recency / Frequency / Monetary → predicts the customer's segment with a description and segment statistics.
- **Insights** — segment distribution plus the EDA & clustering visualisations.

---

## 🛠 Tech stack
`pandas` · `numpy` · `scikit-learn` · `scipy` · `matplotlib` · `seaborn` · `plotly` · `streamlit` · `joblib`
