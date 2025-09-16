# app.py
# Simone Travel Intake (MVP)
import os, re, uuid, json
from io import StringIO
from datetime import date, time, datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Simone – Travel Intake", page_icon="🧳", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.block-container {max-width: 780px;}
.stTextInput > div > div > input {font-size: 16px;}
.stNumberInput input {font-size: 16px;}
</style>
""", unsafe_allow_html=True)

DATA_DIR = os.environ.get("INTAKE_DATA_DIR", "data")
REQUESTS_DIR = os.path.join(DATA_DIR, "requests")
CSV_PATH = os.path.join(DATA_DIR, "reiseanfragen.csv")
os.makedirs(REQUESTS_DIR, exist_ok=True)

def sanitize_slug(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text[:40] if text else "unbekannt"

def append_to_csv(row: dict, csv_path: str):
    df_row = pd.DataFrame([row])
    header_needed = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    df_row.to_csv(csv_path, mode="a", header=header_needed, index=False, encoding="utf-8")

def make_request_folder(start_dt: date, ziel: str, req_id: str) -> str:
    folder_name = f"{start_dt:%Y%m%d}_{sanitize_slug(ziel)}_{req_id[:8]}"
    folder_path = os.path.join(REQUESTS_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def write_request_files(folder: str, payload: dict):
    with open(os.path.join(folder, "request.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    md = [
        f"# Reiseanfrage {payload['request_id']}",
        f"**Erstellt:** {payload['created_at']}",
        f"**Ziel:** {payload['Ziel']}",
        f"**Zeitraum:** {payload['Start']} → {payload['Ende']}",
        f"**Terminzeit vor Ort:** {payload['Termin']}",
        f"**Verkehrsmittel:** {payload['Verkehr']}",
        f"**Hotelbudget/Nacht:** {payload['Hotelbudget']} €",
        f"**Hotel-Lage:** {payload['Lage'] or '—'}",
        f"**Flexible Storno:** {'Ja' if payload['Flexible_Storno'] else 'Nein'}",
        f"**Kostenstelle/Projekt:** {payload['Kostenstelle_Projekt'] or '—'}",
        f"**Kommentare/Wünsche:** {payload['Wunsch'] or '—'}",
        "",
        "_Anmerkung: Diese Mappe ist die Grundlage für Recherche, Vergleich und spätere Ablage (Tickets, Rechnungen)._"
    ]
    with open(os.path.join(folder, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

def try_webdav_upload(local_path: str, remote_rel_path: str) -> bool:
    import requests
    base = os.environ.get("HIDRIVE_DAV_BASEURL")
    user = os.environ.get("HIDRIVE_USER")
    pwd  = os.environ.get("HIDRIVE_PASS")
    basepath = os.environ.get("HIDRIVE_BASEPATH", "")
    if not (base and user and pwd):
        return False
    url = base.rstrip("/") + "/" + basepath.strip("/")
    remote = url.rstrip("/") + "/" + remote_rel_path.lstrip("/")
    try:
        with open(local_path, "rb") as f:
            r = requests.put(remote, data=f, auth=(user, pwd))
        return 200 <= r.status_code < 300
    except Exception:
        return False

st.header("🧳 Simone – Reiseanfrage (MVP)")
st.caption("Minimaler Intake: Simone füllt das Formular aus → Eintrag landet in CSV + Vorgangsordner. Buchung bleibt bei Simone/BDC Travel. Später erweiterbar (PDF, Ordneranlage in der Cloud, Automationen).")

with st.form("intake_form", clear_on_submit=False):
    ziel = st.text_input("Reiseziel (Stadt, Land) *", placeholder="z. B. Berlin, Deutschland")
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("Startdatum *", value=date.today())
    with col2:
        ende = st.date_input("Enddatum *", value=date.today())
    termin = st.time_input("Uhrzeit des Termins vor Ort", value=time(9, 0))
    verkehr = st.selectbox("Bevorzugtes Verkehrsmittel", ["Flug", "Bahn", "egal"], index=0)
    st.subheader("Hotelkriterien")
    hotel_budget = st.number_input("Budget pro Nacht in €", min_value=50, max_value=600, value=150, step=10)
    col3, col4 = st.columns([2, 1])
    with col3:
        hotel_lage = st.text_input("Lage (z. B. Nähe Hbf/Kunde)", placeholder="Innenstadt, Nähe Hbf, beim Kunden …")
    with col4:
        flexible_storno = st.checkbox("Flexible Storno", value=True)
    st.subheader("Zuordnung & Hinweise")
    kostenstelle = st.text_input("Kostenstelle/Projekt (optional)")
    wunsch = st.text_area("Besondere Wünsche / Hinweise (optional)")
    submitted = st.form_submit_button("Anfrage absenden")

if submitted:
    errors = []
    if not ziel.strip():
        errors.append("Bitte Reiseziel ausfüllen.")
    if ende < start:
        errors.append("Enddatum darf nicht vor dem Startdatum liegen.")
    if errors:
        for e in errors:
            st.error(e)
        st.stop()
    req_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = {
        "request_id": req_id,
        "created_at": created_at,
        "Ziel": ziel.strip(),
        "Start": f"{start:%Y-%m-%d}",
        "Ende": f"{ende:%Y-%m-%d}",
        "Termin": termin.strftime("%H:%M"),
        "Verkehr": verkehr,
        "Hotelbudget": int(hotel_budget),
        "Lage": hotel_lage.strip(),
        "Flexible_Storno": bool(flexible_storno),
        "Kostenstelle_Projekt": kostenstelle.strip(),
        "Wunsch": wunsch.strip(),
    }
    try:
        append_to_csv(record, CSV_PATH)
        folder = make_request_folder(start, ziel, req_id)
        write_request_files(folder, record)
    except Exception as ex:
        st.error(f"Speichern fehlgeschlagen: {ex}")
        st.stop()
    csv_buf = StringIO()
    pd.DataFrame([record]).to_csv(csv_buf, index=False, encoding="utf-8")
    st.success("Anfrage gespeichert ✅")
    st.write(f"• CSV-Gesamtliste: `{CSV_PATH}`")
    st.write(f"• Vorgangsordner: `{folder}`")
    st.download_button(label="Diese Anfrage als CSV herunterladen", data=csv_buf.getvalue().encode("utf-8"), file_name=f"request_{record['request_id'][:8]}.csv", mime="text/csv")
    remote_rel = f"/SimoneTravel/{os.path.basename(folder)}/request.json"
    uploaded = False
    try:
        uploaded = try_webdav_upload(os.path.join(folder, "request.json"), remote_rel)
    except Exception:
        uploaded = False
    if uploaded:
        st.info("WebDAV-Upload nach HiDrive: ✅ (request.json)")
    else:
        st.caption("Hinweis: WebDAV-Upload optional via HIDRIVE_* Umgebungsvariablen.")
