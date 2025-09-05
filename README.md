# XSD → XML Generator (Flask)

A small web tool where users upload an XSD and an Excel file and receive an XML file generated from the Excel rows. Optionally validates against the XSD.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

## Deploy (Render.com)

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Set environment variables (optional):
  - `SECRET_KEY` for Flask sessions
  - `MAX_CONTENT_LENGTH_MB` (default 50)
```
