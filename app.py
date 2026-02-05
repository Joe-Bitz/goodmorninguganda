from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, url_for

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
RELEASES_FILE = DATA_DIR / "podcast_releases.json"


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


def make_crash_series(points: int = 64) -> list[float]:
    price = 103.0
    out = []
    drop_idx = int(points * 0.35)
    for i in range(points):
        if i == drop_idx:
            price *= random.uniform(0.18, 0.32)
        else:
            price = max(0.5, price + random.uniform(-1.4, 0.35))
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


def make_crash_metrics() -> dict:
    net = random.uniform(41.0, 5999.0)
    pnl = random.uniform(-8_500_000, -2_100_000)
    short_interest = random.uniform(0.01, 3.5)
    return {
        "net_worth": f"${net:,.2f}",
        "pnl": f"-${abs(pnl):,.2f}",
        "short_interest": f"{short_interest:.2f}%",
    }


def load_releases() -> list[dict]:
    if not RELEASES_FILE.exists():
        return []
    try:
        raw = json.loads(RELEASES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, list):
        return []

    cleaned = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        date = str(item.get("date", "")).strip()
        if not title or not date:
            continue
        cleaned.append({"title": title, "date": date})
    return cleaned


def build_terminal_state() -> dict:
    releases = load_releases()
    latest_release = releases[-1] if releases else None
    crash_mode = bool(latest_release)
    return {
        "crash_mode": crash_mode,
        "latest_release": latest_release,
        "metrics": make_crash_metrics() if crash_mode else make_metrics(),
    }


@app.context_processor
def global_context():
    return {"now": datetime.now(), "ticker": TICKER}


@app.get("/")
def index():
    state = build_terminal_state()
    seeded = [
        {"time": "08:14", "tag": "ALGO", "text": HEADLINES[0][1]},
        {"time": "09:02", "tag": "EARN", "text": HEADLINES[1][1]},
        {"time": "10:37", "tag": "HALT", "text": HEADLINES[2][1]},
    ]
    return render_template(
        "index.html",
        metrics=state["metrics"],
        headlines=seeded,
        chart_series=make_crash_series() if state["crash_mode"] else make_series(),
        app_state=state,
    )


@app.get("/index.html")
def index_html():
    return redirect(url_for("index"), code=302)


@app.get("/research")
def research():
    return render_template("research.html")


@app.get("/research.html")
def research_html():
    return redirect(url_for("research"), code=302)


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


@app.get("/sec.html")
def sec_html():
    return redirect(url_for("sec"), code=302)


@app.get("/transcript")
def transcript():
    return render_template("transcript.html")


@app.get("/transcript.html")
def transcript_html():
    return redirect(url_for("transcript"), code=302)


@app.get("/api/recalc")
def recalc():
    state = build_terminal_state()
    return jsonify(
        {
            "crash_mode": state["crash_mode"],
            "latest_release": state["latest_release"],
            "metrics": state["metrics"],
            "series": make_crash_series() if state["crash_mode"] else make_series(),
        }
    )


@app.get("/api/news")
def news():
    tag, text = random.choice(HEADLINES)
    return jsonify({"tag": tag, "text": text, "stamp": datetime.now().strftime("%H:%M")})


if __name__ == "__main__":
    app.run(debug=True)
