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
