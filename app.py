from __future__ import annotations

import random
from datetime import datetime

from flask import Flask, jsonify, render_template

app = Flask(__name__)


HEADLINES = [
    ("ALGO", "Models confirm friends talking is still an illiquid asset class."),
    ("EARN", "Earnings call delayed pending someone finding the group chat link."),
    ("HALT", "PODCST halted pending fresh episode guidance."),
    ("MACRO", "Rates unchanged. Vibes slightly higher."),
    ("RISK", "Risk team submits memo titled this is a joke right."),
    ("FLOW", "Unusual options flow detected in silence futures."),
    ("GUID", "Management guides maybe next week for episode release."),
]

TICKER = [
    {"symbol": "PODCST", "value": "+12.4%", "class": "up"},
    {"symbol": "SILNCE", "value": "+999.0%", "class": "up"},
    {"symbol": "HYPE", "value": "-2.1%", "class": "down"},
    {"symbol": "VIBES", "value": "+0.7%", "class": "up"},
    {"symbol": "NFA", "value": "NOT ADVICE", "class": "flat"},
]


def make_series(points: int = 64) -> list[float]:
    price = 100.0
    out = []
    for _ in range(points):
        shock = random.uniform(-2.4, 1.8)
        reversion = (100 - price) * 0.07
        price = max(10.0, price + shock + reversion)
        out.append(round(price, 2))
    return out


def make_metrics() -> dict:
    net = 8_000_000 + random.random() * 9_000_000
    pnl = random.uniform(-40_000, 160_000)
    short_interest = random.uniform(220, 720)
    return {
        "net_worth": f"${net:,.2f}",
        "pnl": f"{'+' if pnl >= 0 else '-'}${abs(pnl):,.2f}",
        "short_interest": f"{short_interest:.2f}%",
    }


@app.context_processor
def global_context():
    return {"now": datetime.now(), "ticker": TICKER}


@app.get("/")
def index():
    seeded = [
        {"time": "08:14", "tag": "ALGO", "text": HEADLINES[0][1]},
        {"time": "09:02", "tag": "EARN", "text": HEADLINES[1][1]},
        {"time": "10:37", "tag": "HALT", "text": HEADLINES[2][1]},
    ]
    return render_template(
        "index.html",
        metrics=make_metrics(),
        headlines=seeded,
        chart_series=make_series(),
    )


@app.get("/research")
def research():
    return render_template("research.html")


@app.get("/sec")
def sec():
    filings = [
        {
            "form": "FORM POD-420",
            "date": "2026-01-20",
            "description": "Notice of material event: they stopped recording.",
        },
        {
            "form": "10-Q (Vibes)",
            "date": "2026-01-19",
            "description": "Quarterly report for cash flow, snacks, and friendship goodwill.",
        },
        {
            "form": "8-K (Actually Kidding)",
            "date": "2026-01-18",
            "description": "Current report confirming you cannot short a podcast.",
        },
    ]
    return render_template("sec.html", filings=filings)


@app.get("/transcript")
def transcript():
    return render_template("transcript.html")


@app.get("/api/recalc")
def recalc():
    return jsonify({"metrics": make_metrics(), "series": make_series()})


@app.get("/api/news")
def news():
    tag, text = random.choice(HEADLINES)
    return jsonify({"tag": tag, "text": text, "stamp": datetime.now().strftime("%H:%M")})


if __name__ == "__main__":
    app.run(debug=True)
