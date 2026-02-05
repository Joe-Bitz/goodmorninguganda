from __future__ import annotations

import json
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
RELEASES_FILE = DATA_DIR / "podcast_releases.json"
SPOTIFY_STATE_FILE = DATA_DIR / "spotify_watch_state.json"
SPOTIFY_API_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
DEFAULT_SHOW_ID = "2LtuhlpZRS83QYg7chUEao"
SPOTIFY_CHECK_INTERVAL_SECONDS = 15 * 60


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


def save_releases(releases: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RELEASES_FILE.write_text(json.dumps(releases, indent=2), encoding="utf-8")


def append_release_if_missing(date: str, title: str) -> bool:
    releases = load_releases()
    if any(r.get("date") == date and r.get("title") == title for r in releases):
        return False
    releases.append({"date": date, "title": title})
    save_releases(releases)
    return True


def spotify_enabled() -> bool:
    return bool(os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"))


def load_spotify_state() -> dict:
    if not SPOTIFY_STATE_FILE.exists():
        return {}
    try:
        raw = json.loads(SPOTIFY_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def save_spotify_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SPOTIFY_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_spotify_token() -> str | None:
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None

    basic = f"{client_id}:{client_secret}".encode("utf-8")
    import base64

    auth = base64.b64encode(basic).decode("ascii")
    body = urlencode({"grant_type": "client_credentials"}).encode("utf-8")
    req = Request(
        SPOTIFY_API_TOKEN_URL,
        data=body,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None
    return payload.get("access_token")


def fetch_latest_spotify_episode(token: str, show_id: str) -> dict | None:
    url = f"{SPOTIFY_API_BASE}/shows/{show_id}/episodes?limit=1&market=US"
    req = Request(url, headers={"Authorization": f"Bearer {token}"}, method="GET")
    try:
        with urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    items = payload.get("items") or []
    if not items:
        return None
    item = items[0]
    episode_id = str(item.get("id", "")).strip()
    title = str(item.get("name", "")).strip()
    release_date = str(item.get("release_date", "")).strip()
    if not episode_id or not title or not release_date:
        return None
    return {"id": episode_id, "title": title, "release_date": release_date}


def _walk_json(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_json(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_json(value)


def fetch_latest_spotify_episode_public(show_id: str) -> dict | None:
    url = f"https://open.spotify.com/show/{show_id}"
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; TLCWatcher/1.0; +https://example.local)",
            "Accept": "text/html",
        },
        method="GET",
    )
    try:
        with urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError):
        return None

    ids = re.findall(r"/episode/([A-Za-z0-9]{22})", html)
    if not ids:
        return None

    episode_id = ids[0]
    fallback_title = f"Spotify episode {episode_id}"
    fallback_date = datetime.utcnow().date().isoformat()

    next_data_match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not next_data_match:
        return {"id": episode_id, "title": fallback_title, "release_date": fallback_date}

    try:
        payload = json.loads(next_data_match.group(1))
    except json.JSONDecodeError:
        return {"id": episode_id, "title": fallback_title, "release_date": fallback_date}

    for obj in _walk_json(payload):
        uri = str(obj.get("uri", ""))
        if uri == f"spotify:episode:{episode_id}" or obj.get("id") == episode_id:
            title = str(obj.get("name") or obj.get("title") or fallback_title).strip() or fallback_title
            release_date = str(
                obj.get("release_date")
                or obj.get("releaseDate")
                or obj.get("date")
                or fallback_date
            ).strip() or fallback_date
            return {"id": episode_id, "title": title, "release_date": release_date}

    return {"id": episode_id, "title": fallback_title, "release_date": fallback_date}


def maybe_sync_spotify_release() -> dict:
    public_enabled = os.getenv("SPOTIFY_PUBLIC_WATCH", "1").strip() not in {"0", "false", "False"}
    if not spotify_enabled() and not public_enabled:
        return {"enabled": False, "checked": False, "triggered": False, "reason": "watchers_disabled"}

    now = int(time.time())
    state = load_spotify_state()
    last_checked = int(state.get("last_checked_epoch", 0) or 0)
    if now - last_checked < SPOTIFY_CHECK_INTERVAL_SECONDS:
        return {"enabled": True, "checked": False, "triggered": False, "reason": "interval_guard"}

    show_id = os.getenv("SPOTIFY_SHOW_ID", DEFAULT_SHOW_ID).strip() or DEFAULT_SHOW_ID
    source = "public_page"
    latest = None

    if spotify_enabled():
        token = get_spotify_token()
        if token:
            latest = fetch_latest_spotify_episode(token, show_id)
            source = "spotify_api"

    if not latest and public_enabled:
        latest = fetch_latest_spotify_episode_public(show_id)
        source = "public_page"

    if not latest:
        return {"enabled": True, "checked": True, "triggered": False, "reason": "fetch_failed", "source": source}

    last_seen_episode_id = str(state.get("last_episode_id", "")).strip()
    triggered = False
    # Bootstrap baseline on first successful sync to avoid immediate false trigger.
    if last_seen_episode_id and latest["id"] != last_seen_episode_id:
        triggered = append_release_if_missing(latest["release_date"], latest["title"])

    save_spotify_state(
        {
            "last_checked_epoch": now,
            "last_checked_at": datetime.utcnow().isoformat() + "Z",
            "last_episode_id": latest["id"],
            "last_episode_title": latest["title"],
            "last_episode_release_date": latest["release_date"],
            "show_id": show_id,
            "source": source,
        }
    )
    return {"enabled": True, "checked": True, "triggered": triggered, "reason": "ok", "source": source}


def build_terminal_state() -> dict:
    spotify_sync = maybe_sync_spotify_release()
    releases = load_releases()
    latest_release = releases[-1] if releases else None
    crash_mode = bool(latest_release)
    total_releases = len(releases)
    base_damage = [round(58 + random.random() * 38, 2) for _ in releases]
    avg_damage = round(sum(base_damage) / len(base_damage), 2) if base_damage else 0.0
    worst_damage = max(base_damage) if base_damage else 0.0
    severity = "LOW"
    if crash_mode:
        if total_releases >= 6 or avg_damage >= 85:
            severity = "MAX"
        elif total_releases >= 3 or avg_damage >= 72:
            severity = "HIGH"
        else:
            severity = "MED"

    return {
        "crash_mode": crash_mode,
        "latest_release": latest_release,
        "metrics": make_crash_metrics() if crash_mode else make_metrics(),
        "releases": releases,
        "release_stats": {
            "total_catastrophes": total_releases,
            "avg_damage_pct": avg_damage,
            "worst_day_pct": worst_damage,
            "severity": severity,
        },
        "spotify_sync": spotify_sync,
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


@app.get("/api/spotify-status")
def spotify_status():
    sync = maybe_sync_spotify_release()
    state = load_spotify_state()
    return jsonify({"sync": sync, "state": state})


@app.route("/api/trigger-crash", methods=["GET", "POST"])
def trigger_crash():
    payload = request.get_json(silent=True) or {}
    provided_token = (
        request.args.get("token")
        or payload.get("token")
        or request.headers.get("X-Trigger-Token")
        or ""
    )
    required_token = os.getenv("MANUAL_TRIGGER_TOKEN", "").strip()
    if required_token and provided_token != required_token:
        return jsonify({"ok": False, "error": "invalid_token"}), 403

    title = str(request.args.get("title") or payload.get("title") or "Manual Episode Trigger").strip()
    date = str(
        request.args.get("date")
        or payload.get("date")
        or datetime.utcnow().date().isoformat()
    ).strip()
    if not title:
        return jsonify({"ok": False, "error": "missing_title"}), 400
    if not date:
        return jsonify({"ok": False, "error": "missing_date"}), 400

    added = append_release_if_missing(date, title)
    return jsonify(
        {
            "ok": True,
            "added": added,
            "release": {"date": date, "title": title},
            "warning": "MANUAL_TRIGGER_TOKEN is not set" if not required_token else None,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
