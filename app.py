import streamlit as st
import json
import os
import base64
from PIL import Image
import io

# ---------------------------------------------------------
# Seitenkonfiguration für optimale Handy- und Browseransicht
# ---------------------------------------------------------
st.set_page_config(
    page_title="Unser Aktivitäten-Bingo",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_FILE = "bingo_data.json"
GRID_SIZE = 4  # 4x4 Gitter = 16 Felder
TOTAL_TILES = GRID_SIZE * GRID_SIZE

# ---------------------------------------------------------
# Hilfsfunktionen: Laden und Speichern der Daten
# ---------------------------------------------------------
def get_default_data():
    return {
        str(i): {
            "title": f"Aktivität #{i+1}",
            "description": "",
            "image_b64": None,
            "done": False
        }
        for i in range(TOTAL_TILES)
    }

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Fehlende Felder ergänzen, falls Gitter geändert wurde
                for i in range(TOTAL_TILES):
                    k = str(i)
                    if k not in data:
                        data[k] = {
                            "title": f"Aktivität #{i+1}",
                            "description": "",
                            "image_b64": None,
                            "done": False
                        }
                return data
        except Exception:
            return get_default_data()
    return get_default_data()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Session State initialisieren
if "bingo_data" not in st.session_state:
    st.session_state.bingo_data = load_data()

# Immer neuesten Stand von Festplatte abgleichen
data = load_data()
st.session_state.bingo_data = data

# ---------------------------------------------------------
# CSS: Styling für Überschrift, Karten und Bingo-Stempel
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Hauptüberschrift */
    .main-title {
        text-align: center;
        font-family: 'Arial Black', Impact, sans-serif;
        font-size: 3rem;
        letter-spacing: 5px;
        color: #12284c;
        margin-bottom: 5px;
        text-transform: uppercase;
    }
    .sub-title {
        text-align: center;
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 25px;
    }

    /* Kachel Container */
    .bingo-card {
        position: relative;
        border: 2px solid #222;
        border-radius: 8px;
        overflow: hidden;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 230px;
    }

    /* Bildbereich */
    .img-box {
        position: relative;
        width: 100%;
        height: 140px;
        background-color: #f0f2f6;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .img-box img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .img-placeholder {
        color: #999;
        font-size: 0.9rem;
        font-style: italic;
    }

    /* Textbereich unter dem Bild */
    .card-info {
        padding: 8px 6px;
        text-align: center;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border-top: 2px solid #222;
        background-color: #fdfdfd;
    }
    .card-title {
        font-weight: 800;
        font-size: 0.95rem;
        color: #1a2a44;
        line-height: 1.2;
        margin-bottom: 2px;
    }
    .card-desc {
        font-size: 0.75rem;
        color: #555;
    }

    /* DER BINGO STEMPEL */
    .stamp-overlay {
        position: absolute;
        top: 25%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-15deg);
        border: 4px solid #d90429;
        color: #d90429;
        font-family: 'Arial Black', sans-serif;
        font-size: 1.6rem;
        font-weight: 900;
        text-transform: uppercase;
        padding: 4px 14px;
        border-radius: 6px;
        background-color: rgba(255, 255, 255, 0.85);
        box-shadow: 0 0 10px rgba(217, 4, 41, 0.4);
        pointer-events: none;
        z-index: 10;
        letter-spacing: 2px;
    }

    /* Button-Abstände anpassen */
    div[data-testid="stButton"] button {
        margin-top: 4px;
        font-size: 0.8rem;
        padding: 2px 6px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Titelbereich
# ---------------------------------------------------------
st.markdown("<div class='main-title'>B I N G O</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Unser gemeinsames Aktivitäten-Board 💕</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4x4 Spielfeld generieren
# ---------------------------------------------------------
for row in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for col in range(GRID_SIZE):
        idx = row * GRID_SIZE + col
        k = str(idx)
        item = data[k]

        with cols[col]:
            # Stempel-HTML generieren, falls erledigt
            stamp_html = "<div class='stamp-overlay'>BINGO!</div>" if item.get("done", False) else ""

            # Bild-HTML erstellen
            if item.get("image_b64"):
                img_src = f"data:image/jpeg;base64,{item['image_b64']}"
                img_tag = f"<img src='{img_src}' alt='{item['title']}'>"
            else:
                img_tag = "<div class='img-placeholder'>📷 Noch kein Bild</div>"

            # Kachel rendern
            desc_text = f"<div class='card-desc'>{item.get('description', '')}</div>" if item.get('description') else ""
            card_html = f"""
            <div class='bingo-card'>
                <div class='img-box'>
                    {img_tag}
                    {stamp_html}
                </div>
                <div class='card-info'>
                    <div class='card-title'>{item.get('title', 'Aktivität')}</div>
                    {desc_text}
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            # Steuerungs-Buttons für das Feld
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                done_btn_label = "↩️ Reset" if item.get("done") else "🎯 Bingo!"
                if st.button(done_btn_label, key=f"toggle_{idx}", use_container_width=True):
                    data[k]["done"] = not data[k].get("done", False)
                    save_data(data)
                    st.rerun()

            with btn_col2:
                # Expander / Popover zum Bearbeiten des Feldes
                with st.popover("✏️ Edit", use_container_width=True):
                    st.write(f"**Feld #{idx+1} bearbeiten**")
                    new_title = st.text_input("Titel / Aktivität", value=item.get("title", ""), key=f"t_{idx}")
                    new_desc = st.text_input("Beschreibung / Notiz", value=item.get("description", ""), key=f"d_{idx}")
                    uploaded_file = st.file_uploader("Bild / Screenshot hochladen", type=["png", "jpg", "jpeg", "webp"], key=f"f_{idx}")

                    if st.button("Speichern", key=f"save_{idx}", type="primary"):
                        data[k]["title"] = new_title
                        data[k]["description"] = new_desc
                        if uploaded_file is not None:
                            image = Image.open(uploaded_file)
                            # Automatische Bildskalierung für schnelle Ladezeiten
                            image.thumbnail((600, 600))
                            buffered = io.BytesIO()
                            image.convert("RGB").save(buffered, format="JPEG", quality=80)
                            data[k]["image_b64"] = base64.b64encode(buffered.getvalue()).decode()
                        save_data(data)
                        st.success("Aktualisiert!")
                        st.rerun()

st.write("---")

# ---------------------------------------------------------
# Hilfsfunktionen & Gesamtstatus
# ---------------------------------------------------------
done_count = sum(1 for v in data.values() if v.get("done"))
st.info(f"🏆 Fortschritt: **{done_count} von {TOTAL_TILES}** Aktivitäten als BINGO abgehakt!")
