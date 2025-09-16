# app.py
import os, requests
from io import StringIO
from datetime import date
import pandas as pd
import streamlit as st

# ---------- Konfiguration ----------
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "45fe1f07aemshd23fb27fe996de9p12d172jsn44fe092c30ce")  # <--- HIER KEY EINTRAGEN
RAPIDAPI_HOST = "booking-com-api4.p.rapidapi.com"
API_URL = "https://booking-com-api4.p.rapidapi.com/list-hotels/"

# ---------- Streamlit Setup ----------
st.set_page_config(page_title="Simone – Travel Intake", page_icon="🧳")
st.header("🧳 Simone – Reiseanfrage mit Hotels")

# ---------- Formular ----------
with st.form("intake_form"):
    ziel = st.text_input("Reiseziel (Stadt) *", placeholder="z. B. Berlin")
    start = st.date_input("Startdatum", value=date.today())
    ende = st.date_input("Enddatum", value=date.today())
    budget = st.number_input("Budget pro Nacht in €", min_value=50, max_value=600, value=150, step=10)
    submitted = st.form_submit_button("Anfrage absenden")

# ---------- API Funktion ----------
def fetch_hotels(city_name, budget, limit=3):
    url = f"{API_URL}?city_name={city_name}&page_number=1&items_per_page={limit}"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        data = resp.json()
        hotels = []
        for h in data.get("data", [])[:limit]:
            hotels.append({
                "name": h.get("name"),
                "price": h.get("price", "n/a"),
                "url": h.get("url", "n/a")
            })
        return hotels
    except Exception as e:
        return [{"name": f"Fehler: {e}", "price": "-", "url": "-"}]

# ---------- Ergebnis ----------
if submitted:
    st.success(f"Anfrage gespeichert für {ziel} ({start} bis {ende})")

    hotels = fetch_hotels(ziel, budget)
    st.subheader("Hotelvorschläge (Booking.com via RapidAPI)")

    if not hotels:
        st.write("Keine Hotels gefunden.")
    else:
        df_hotels = pd.DataFrame(hotels)
        st.table(df_hotels)

        # CSV Download
        csv_buf = StringIO()
        df_hotels.to_csv(csv_buf, index=False, encoding="utf-8")
        st.download_button("Hotelvorschläge als CSV herunterladen",
                           data=csv_buf.getvalue().encode("utf-8"),
                           file_name=f"hotels_{ziel}.csv",
                           mime="text/csv")
