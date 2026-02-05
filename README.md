# goodmorninguganda

Parody site rebuilt as an actual HTML/CSS/Python app.

## Stack
- Python 3.11+
- Flask
- Jinja templates (HTML)
- Shared CSS + page JS

## Run
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Routes
- `/` terminal dashboard
- `/research` analyst page
- `/sec` parody filings
- `/transcript` parody earnings transcript

## Episode Crash Trigger
When a new podcast episode drops, add it to `data/podcast_releases.json` and the terminal will flip into crash mode automatically.

Example:
```json
[
  {
    "date": "2026-02-05",
    "title": "Episode 12 - We Actually Recorded"
  }
]
```

Notes:
- Keep the file as a JSON array.
- Add newer releases at the end of the array.
- Remove all entries to return to normal (non-crash) mode.

## Auto Trigger From Spotify
You can auto-trigger crash mode from the live Spotify show feed.

Set these env vars:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_SHOW_ID` (optional, default is `2LtuhlpZRS83QYg7chUEao`)
- `SPOTIFY_PUBLIC_WATCH` (optional, default `1`; set `0` to disable public page watcher)

How it works:
- App checks Spotify episodes periodically (15-minute guard).
- On first successful sync, it stores a baseline episode (no trigger).
- On later checks, if a new latest episode ID appears, it appends that episode to `data/podcast_releases.json` automatically.
- If API credentials are unavailable, it falls back to parsing the public Spotify show page.

Debug endpoint:
- `GET /api/spotify-status`

## Manual Trigger Endpoint
You can manually trigger crash mode from phone/laptop without editing JSON.

Optional env var:
- `MANUAL_TRIGGER_TOKEN` (recommended for safety)

Endpoint:
- `GET /api/trigger-crash?token=YOUR_TOKEN&title=Episode+Name&date=2026-02-05`
- `POST /api/trigger-crash` with JSON body:
```json
{
  "token": "YOUR_TOKEN",
  "title": "Episode Name",
  "date": "2026-02-05"
}
```
