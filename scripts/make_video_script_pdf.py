"""
Generate a polished 13-minute video presentation script (PDF) for the
Shopper Spectrum project.

Output: outputs/Shopper_Spectrum_Video_Script.pdf
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "Shopper_Spectrum_Video_Script.pdf")

# ---- Palette --------------------------------------------------------------- #
NAVY = colors.HexColor("#0c343d")
TEAL = colors.HexColor("#1b9e7d")
TEAL_DK = colors.HexColor("#0f6e57")
ACCENT = colors.HexColor("#2dd4a7")
LIGHT = colors.HexColor("#eef6f4")
GREY = colors.HexColor("#5a6b70")
INK = colors.HexColor("#16313a")
BAND = colors.HexColor("#13414c")

styles = getSampleStyleSheet()

H_TITLE = ParagraphStyle("HTitle", parent=styles["Title"], fontName="Helvetica-Bold",
                         fontSize=30, textColor=colors.white, leading=34, alignment=TA_CENTER)
H_SUB = ParagraphStyle("HSub", parent=styles["Normal"], fontName="Helvetica",
                       fontSize=13, textColor=colors.HexColor("#bfe9dc"),
                       leading=18, alignment=TA_CENTER)
SECTION = ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=15,
                         textColor=colors.white, leading=18)
SECTION_T = ParagraphStyle("SectionT", fontName="Helvetica-Bold", fontSize=11,
                           textColor=ACCENT, leading=14)
LABEL = ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=8.5,
                       textColor=TEAL_DK, leading=11, spaceAfter=1)
SAY = ParagraphStyle("Say", fontName="Helvetica", fontSize=9.7,
                     textColor=INK, leading=14)
SHOW = ParagraphStyle("Show", fontName="Helvetica-Oblique", fontSize=9.2,
                      textColor=GREY, leading=13)
BODY = ParagraphStyle("Body", fontName="Helvetica", fontSize=10,
                      textColor=INK, leading=15)
BODY_C = ParagraphStyle("BodyC", parent=BODY, alignment=TA_CENTER)
TIP = ParagraphStyle("Tip", fontName="Helvetica", fontSize=9, textColor=GREY, leading=13)
CELL = ParagraphStyle("Cell", fontName="Helvetica", fontSize=9, textColor=INK, leading=12)
CELL_B = ParagraphStyle("CellB", fontName="Helvetica-Bold", fontSize=9, textColor=INK, leading=12)
CELL_W = ParagraphStyle("CellW", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.white, leading=12)


def band(text, time_str):
    """A colored section header band with title + timecode."""
    t = Table(
        [[Paragraph(text, SECTION), Paragraph(time_str, SECTION_T)]],
        colWidths=[125 * mm, 40 * mm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAND),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 10),
        ("RIGHTPADDING", (-1, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("ROUNDEDCORNERS", [5, 5, 5, 5]),
    ]))
    return t


def segment(num, title, time_str, duration, say_lines, show_lines):
    """Build one presentation segment as a keep-together block."""
    els = [band(f"{num}.  {title}", f"{time_str}  ·  {duration}")]
    els.append(Spacer(1, 4))

    say_html = "<br/>".join(say_lines)
    show_html = "<br/>".join("• " + s for s in show_lines)

    inner = Table(
        [[Paragraph("WHAT TO SAY", LABEL)],
         [Paragraph(say_html, SAY)],
         [Spacer(1, 3)],
         [Paragraph("WHAT TO SHOW ON SCREEN", LABEL)],
         [Paragraph(show_html, SHOW)]],
        colWidths=[165 * mm],
    )
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (0, 0), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 9),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
    ]))
    els.append(inner)
    els.append(Spacer(1, 9))
    return KeepTogether(els)


def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    # footer line
    canvas.setStrokeColor(colors.HexColor("#cfe0dc"))
    canvas.setLineWidth(0.6)
    canvas.line(20 * mm, 14 * mm, w - 20 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(20 * mm, 9 * mm, "Shopper Spectrum — 13-Minute Video Walkthrough Script")
    canvas.drawRightString(w - 20 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def cover(canvas, doc):
    w, h = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    # accent stripes (lower third, clear of the title block)
    canvas.setFillColor(TEAL_DK)
    canvas.rect(0, 88 * mm, w, 4 * mm, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 86.5 * mm, w, 1.2 * mm, fill=1, stroke=0)
    canvas.restoreState()


def build():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title="Shopper Spectrum - 13-Minute Video Script",
        author="Shopper Spectrum",
    )

    story = []

    # ---------------- Cover ---------------- #
    story.append(Spacer(1, 48 * mm))
    story.append(Paragraph("Shopper Spectrum", H_TITLE))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Customer Segmentation &amp; Product Recommendations<br/>in E-Commerce",
                           H_SUB))
    story.append(Spacer(1, 12 * mm))

    badge = Table([[Paragraph("13-MINUTE VIDEO PRESENTATION SCRIPT", ParagraphStyle(
        "badge", fontName="Helvetica-Bold", fontSize=12, textColor=NAVY,
        alignment=TA_CENTER, leading=15))]], colWidths=[110 * mm])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(badge)
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "A complete, time-boxed narration guide — what to say and what to show "
        "on screen — to present the entire project end to end in exactly "
        "thirteen minutes.",
        ParagraphStyle("coverbody", fontName="Helvetica", fontSize=11,
                       textColor=colors.HexColor("#cfe6df"), alignment=TA_CENTER,
                       leading=17)))
    story.append(PageBreak())

    # ---------------- Overview timeline ---------------- #
    story.append(Paragraph("Presentation Timeline at a Glance",
                           ParagraphStyle("h2", fontName="Helvetica-Bold",
                                          fontSize=17, textColor=NAVY, spaceAfter=8)))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=10))

    rows = [
        ["#", "Segment", "Timecode", "Length"],
        ["1", "Intro & Hook", "0:00 – 0:45", "45s"],
        ["2", "Problem Statement & Business Value", "0:45 – 2:00", "1m 15s"],
        ["3", "Dataset Overview", "2:00 – 3:00", "1m 00s"],
        ["4", "Data Preprocessing", "3:00 – 4:15", "1m 15s"],
        ["5", "Exploratory Data Analysis (EDA)", "4:15 – 5:45", "1m 30s"],
        ["6", "RFM Feature Engineering", "5:45 – 7:00", "1m 15s"],
        ["7", "Clustering Methodology", "7:00 – 9:00", "2m 00s"],
        ["8", "Recommendation System", "9:00 – 10:15", "1m 15s"],
        ["9", "Live Streamlit App Demo", "10:15 – 12:15", "2m 00s"],
        ["10", "Conclusion & Deliverables", "12:15 – 13:00", "45s"],
    ]
    t = Table(rows, colWidths=[10 * mm, 88 * mm, 38 * mm, 29 * mm])
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (3, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 1, NAVY),
        ("GRID", (0, 1), (-1, -1), 0.4, colors.HexColor("#d4e3df")),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            ts.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(ts))
    story.append(t)
    story.append(Spacer(1, 6))
    story.append(Paragraph("Total runtime: <b>13 minutes 00 seconds</b>", BODY_C))

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Before You Record — Quick Checklist", ParagraphStyle(
        "h3", fontName="Helvetica-Bold", fontSize=13, textColor=TEAL_DK, spaceAfter=6)))
    checklist = [
        "Run <font face='Courier'>python -m src.train</font> so all model artifacts &amp; figures exist.",
        "Launch the app: <font face='Courier'>streamlit run app.py</font> and keep the browser tab ready.",
        "Open the notebook (<font face='Courier'>notebooks/analysis.ipynb</font>) and the figures in <font face='Courier'>outputs/figures/</font>.",
        "Have one product name and one set of RFM values ready for the live demo.",
        "Record at 1080p; speak ~135 words/min to comfortably fit each segment.",
    ]
    for c in checklist:
        story.append(Paragraph("☐ " + c, ParagraphStyle(
            "chk", parent=BODY, leftIndent=6, spaceAfter=3)))
    story.append(PageBreak())

    # ---------------- Segments ---------------- #
    story.append(Paragraph("The Script, Segment by Segment", ParagraphStyle(
        "h2b", fontName="Helvetica-Bold", fontSize=17, textColor=NAVY, spaceAfter=8)))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=12))

    story.append(segment(
        "1", "Intro & Hook", "0:00 – 0:45", "45 sec",
        say_lines=[
            "&ldquo;Hi everyone. Every day, online stores collect millions of transactions — "
            "but most of that data just sits there. In this project, <b>Shopper Spectrum</b>, "
            "I turn raw e-commerce transactions into two things a business can act on: "
            "<b>who their customers really are</b>, and <b>what to recommend them next</b>.&rdquo;",
            "&ldquo;I&rsquo;ll walk you through the data, the machine learning, and a live web app — "
            "in about thirteen minutes.&rdquo;",
        ],
        show_lines=[
            "Title slide with the project name and your name.",
            "Briefly flash the running Streamlit app as a teaser.",
        ],
    ))

    story.append(segment(
        "2", "Problem Statement & Business Value", "0:45 – 2:00", "1 min 15 sec",
        say_lines=[
            "&ldquo;The goal is to analyse transaction data from an online retailer to uncover "
            "patterns in purchasing behaviour. I do this in two ways.&rdquo;",
            "&ldquo;First, <b>customer segmentation</b> using <b>RFM analysis</b> — Recency, Frequency, "
            "and Monetary value — so we can group customers by how they actually behave.&rdquo;",
            "&ldquo;Second, a <b>product recommendation system</b> using <b>collaborative filtering</b>, "
            "so when a shopper views a product, we can suggest five similar ones.&rdquo;",
            "&ldquo;Why does this matter? It powers <b>targeted marketing</b>, <b>personalised "
            "recommendations</b>, <b>win-back campaigns for at-risk customers</b>, and smarter "
            "<b>inventory and pricing</b> decisions.&rdquo;",
        ],
        show_lines=[
            "Slide listing the two ML problems: Clustering (unsupervised) + Collaborative Filtering.",
            "Bullet list of the five real-time business use cases from the brief.",
        ],
    ))

    story.append(segment(
        "3", "Dataset Overview", "2:00 – 3:00", "1 min 00 sec",
        say_lines=[
            "&ldquo;I&rsquo;m using the classic <b>Online Retail</b> dataset — around "
            "<b>540,000 transactions</b> from a UK-based retailer.&rdquo;",
            "&ldquo;Each row is one item on an invoice, with eight columns: InvoiceNo, StockCode, "
            "Description, Quantity, InvoiceDate, UnitPrice, CustomerID, and Country.&rdquo;",
            "&ldquo;So one customer can have many invoices, and one invoice many products — "
            "that structure is exactly what RFM and collaborative filtering need.&rdquo;",
        ],
        show_lines=[
            "Show df.head() in the notebook and the dataset description table.",
            "Point out the eight columns and what each represents.",
        ],
    ))

    story.append(segment(
        "4", "Data Preprocessing", "3:00 – 4:15", "1 min 15 sec",
        say_lines=[
            "&ldquo;Real transaction data is messy, so cleaning is critical. I apply three rules "
            "straight from the brief.&rdquo;",
            "&ldquo;One — <b>drop rows with a missing CustomerID</b>, because we can&rsquo;t segment an "
            "anonymous buyer. Two — <b>exclude cancelled invoices</b>, the ones whose InvoiceNo "
            "starts with &lsquo;C&rsquo;. Three — <b>remove zero or negative quantities and prices</b>.&rdquo;",
            "&ldquo;After cleaning, about <b>540k rows become ~393k</b> valid transactions. I also add a "
            "<b>TotalPrice</b> column — quantity times unit price — which I&rsquo;ll need for the Monetary "
            "value later.&rdquo;",
        ],
        show_lines=[
            "Show the clean_transactions() function in src/preprocessing.py.",
            "Display the row-count report: raw → after each cleaning step.",
        ],
    ))

    story.append(segment(
        "5", "Exploratory Data Analysis (EDA)", "4:15 – 5:45", "1 min 30 sec",
        say_lines=[
            "&ldquo;Before modelling, I explore the data to understand it.&rdquo;",
            "&ldquo;Looking at <b>transaction volume by country</b>, the UK dominates — expected for a "
            "UK retailer. The <b>top-selling products</b> chart shows our best movers, and the "
            "<b>monthly revenue trend</b> reveals clear seasonality toward the end of the year.&rdquo;",
            "&ldquo;I also look at the <b>distribution of transaction value</b> — it&rsquo;s heavily "
            "right-skewed: many small orders, a few very large ones. That skew is important, "
            "because it tells me I&rsquo;ll need to transform the data before clustering.&rdquo;",
        ],
        show_lines=[
            "Walk through outputs/figures: top_countries, top_products, revenue_trend, transaction_value.",
            "Verbally connect the skew you see to the log-transform decision in the next section.",
        ],
    ))

    story.append(segment(
        "6", "RFM Feature Engineering", "5:45 – 7:00", "1 min 15 sec",
        say_lines=[
            "&ldquo;Now the heart of segmentation — turning transactions into three numbers per "
            "customer.&rdquo;",
            "&ldquo;<b>Recency</b>: how many days since their last purchase — lower is better. "
            "<b>Frequency</b>: how many distinct invoices they&rsquo;ve placed. "
            "<b>Monetary</b>: their total spend.&rdquo;",
            "&ldquo;I compute these with a single grouped aggregation per CustomerID. Because "
            "Frequency and Monetary are so skewed, I apply a <b>log transform</b>, then "
            "<b>standardise</b> all three with a StandardScaler so no single feature dominates "
            "the distance calculation in KMeans.&rdquo;",
        ],
        show_lines=[
            "Show build_rfm() and the resulting RFM table (rfm describe()).",
            "Show the RFM distribution histograms (rfm_distributions.png).",
        ],
    ))

    story.append(segment(
        "7", "Clustering Methodology", "7:00 – 9:00", "2 min 00 sec",
        say_lines=[
            "&ldquo;With scaled RFM features, I cluster customers using <b>KMeans</b>.&rdquo;",
            "&ldquo;To choose the number of clusters I use two tools: the <b>Elbow method</b>, which "
            "plots inertia, and the <b>Silhouette score</b>, which measures how well-separated the "
            "clusters are. The project defines <b>four business segments</b>, so I anchor on "
            "<b>k = 4</b>, which the silhouette curve supports.&rdquo;",
            "&ldquo;Then I <b>label each cluster by its RFM averages</b>. The best cluster — recent, "
            "frequent, high spend — becomes <b>High-Value</b>. The others map to <b>Regular</b>, "
            "<b>Occasional</b>, and <b>At-Risk</b>, who haven&rsquo;t purchased in a long time.&rdquo;",
            "&ldquo;This scatter plot shows the four segments cleanly separated in RFM space. "
            "Finally I <b>save the model and scaler</b> so the web app can reuse them in real time.&rdquo;",
        ],
        show_lines=[
            "Show cluster_selection.png (elbow + silhouette side by side).",
            "Show cluster_2d.png / cluster_3d.png with the four colored segments.",
            "Show the segment summary table: customer counts and average R, F, M per segment.",
        ],
    ))

    story.append(segment(
        "8", "Recommendation System", "9:00 – 10:15", "1 min 15 sec",
        say_lines=[
            "&ldquo;The second engine is product recommendation, using <b>item-based collaborative "
            "filtering</b>.&rdquo;",
            "&ldquo;I build a <b>customer-by-product matrix</b> from purchase history, then compute "
            "<b>cosine similarity</b> between products. Two products are similar if the same "
            "customers tend to buy them.&rdquo;",
            "&ldquo;To recommend, I take the entered product, look up its row, and return the "
            "<b>five most similar products</b>. No personal data needed — it&rsquo;s driven purely by "
            "collective buying patterns, and it works instantly from a precomputed matrix.&rdquo;",
        ],
        show_lines=[
            "Show build_recommender() and the recommend_products() helper.",
            "Show an example: a product name and its top-5 similar products with similarity scores.",
        ],
    ))

    story.append(segment(
        "9", "Live Streamlit App Demo", "10:15 – 12:15", "2 min 00 sec",
        say_lines=[
            "&ldquo;Now let&rsquo;s see it all come together in the live app.&rdquo;",
            "&ldquo;Here&rsquo;s the dashboard with headline metrics — customers, products, transactions, "
            "and revenue. On the left is the navigation.&rdquo;",
            "&ldquo;In the <b>Product Recommendation</b> module, I type a product name, click "
            "<b>Get Recommendations</b>, and instantly get five similar products as cards.&rdquo;",
            "&ldquo;In the <b>Customer Segmentation</b> module, I enter a customer&rsquo;s Recency, "
            "Frequency, and Monetary values, click <b>Predict Cluster</b>, and the app tells me "
            "their segment — say, High-Value — with a description and segment statistics.&rdquo;",
            "&ldquo;And the <b>Insights</b> tab surfaces the EDA and clustering visuals for "
            "stakeholders. Everything is real-time, powered by the models we just trained.&rdquo;",
        ],
        show_lines=[
            "Screen-record the actual app: hero metrics, then each of the three tabs.",
            "Recommendation: type a real product → show the 5 result cards.",
            "Segmentation: enter RFM values → show the colored segment badge + stats.",
            "Click through the Insights tab charts.",
        ],
    ))

    story.append(segment(
        "10", "Conclusion & Deliverables", "12:15 – 13:00", "45 sec",
        say_lines=[
            "&ldquo;To wrap up: Shopper Spectrum takes raw e-commerce data and delivers <b>four "
            "actionable customer segments</b> and a <b>real-time product recommender</b>, served "
            "through a clean Streamlit app.&rdquo;",
            "&ldquo;The deliverables are a <b>documented analysis notebook</b>, the <b>trained models</b>, "
            "and the <b>interactive web application</b>. Together they help a retailer market "
            "smarter, retain customers, and sell more.&rdquo;",
            "&ldquo;Thanks for watching!&rdquo;",
        ],
        show_lines=[
            "Recap slide: 4 segments + recommender + app.",
            "Show the project structure / GitHub repo, then a closing thank-you slide.",
        ],
    ))

    # ---------------- Closing tips ---------------- #
    story.append(Paragraph("Delivery Tips", ParagraphStyle(
        "tips", fontName="Helvetica-Bold", fontSize=13, textColor=TEAL_DK, spaceAfter=6)))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))
    tips = [
        "<b>Pace:</b> ~135 words per minute keeps every segment on time without rushing.",
        "<b>Show, don&rsquo;t just tell:</b> keep your screen on the relevant figure or code while you speak.",
        "<b>Transitions:</b> end each segment with one sentence that sets up the next.",
        "<b>Demo safety:</b> pre-load the app and have inputs ready so nothing buffers on camera.",
        "<b>Confidence:</b> you built this — explain decisions (&ldquo;I chose k=4 because&hellip;&rdquo;), don&rsquo;t just describe steps.",
    ]
    for tp in tips:
        story.append(Paragraph("→ " + tp, ParagraphStyle("tipitem", parent=TIP,
                                                          leftIndent=6, spaceAfter=4)))

    doc.build(story, onFirstPage=cover, onLaterPages=header_footer)
    print(f"[ok] PDF written to: {OUT}")


if __name__ == "__main__":
    build()
