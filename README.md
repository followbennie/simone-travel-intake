# Simone Travel Intake (MVP)

Mini-Web-App für Simones Reiseanfragen (Streamlit).

## Start (macOS / Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Start (Windows, PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

App im Browser: http://localhost:8501

Daten liegen unter `./data/`:
- `reiseanfragen.csv`
- `requests/<YYYYMMDD_Ziel_reqid>/request.json` + `summary.md`

Optionaler HiDrive WebDAV-Upload via Umgebungsvariablen:
- HIDRIVE_DAV_BASEURL, HIDRIVE_USER, HIDRIVE_PASS, HIDRIVE_BASEPATH
