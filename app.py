import streamlit as st
import json
import os
import base64
from PIL import Image
import io

# ---------------------------------------------------------
# Seitenkonfiguration: Schlankes Layout
# ---------------------------------------------------------
st.set_page_config(
    page_title="Unser Foto-Bingo",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DATA_FILE = "bingo_data.json"
GRID_SIZE = 4  # 4x4 = 16 Felder
TOTAL_TILES = GRID_SIZE * GRID_SIZE

# ---------------------------------------------------------
# Daten laden & speichern
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
                for i in range(TOTAL_TILES):
                    k = str(i)
                    if k not in data:
                        data[k] = {"title": f"Aktivität #{i+1}", "description": "", "image_b64": None, "done": False}
                return data
        except Exception:
            return get_default_data()
    return get_default_data()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if "bingo_data" not in st.session_state:
    st.session_state.bingo_data = load_data()

data = load_data()
st.session_state.bingo_data = data

# ---------------------------------------------------------
# CSS: Echtes 4x4-Gitter, Abstände & Grüner Rand
# ---------------------------------------------------------
st.markdown("""
<style>
    /* 1. Haupt-Container auf Handys maximal ausnutzen */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.3rem !important;
        padding-right: 0.3rem !important;
        max-width: 100% !important;
    }

    /* Titel-Styling */
    .bingo-header {
        text-align: center;
        font-family: 'Arial Black', Impact, sans-serif;
        font-size: clamp(2rem, 7vw, 3rem);
        letter-spacing: 4px;
        color: #1e3a5f;
        margin-top: -15px;
        margin-bottom: 2px;
    }
    .bingo-sub {
        text-align: center;
        font-size: clamp(0.75rem, 3vw, 0.95rem);
        color: #888;
        margin-bottom: 15px;
    }

    /* 2. Äußere Bingo-Reihe: 4 Spalten nebeneinander erzwingen */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important;
        width: 100% !important;
        margin-bottom: 6px !important;
    }

    /* 3. Spaltenbreite: Spalten 1-3 ca. 24%, Spalte 4 hat etwas Abstand */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        width: calc(25% - 4px) !important;
        min-width: 0 !important;
        max-width: calc(25% - 4px) !important;
        flex: 1 1 calc(25% - 4px) !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Extra Abstand für die ganz rechte 4. Spalte */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4),
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(4) {
        margin-left: 6px !important;
    }

    /* 4. Die beiden Buttons unter jeder Kachel: je genau 50% */
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] {
        gap: 2px !important;
        margin-bottom: 0 !important;
    }

    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        width: 50% !important;
        min-width: 0 !important;
        max-width: 50% !important;
        flex: 1 1 50% !important;
        margin-left: 0 !important;
    }

    /* 5. Quadratische Bildkarte (1:1 Ratio) */
    .bingo-card {
        position: relative;
        width: 100%;
        aspect-ratio: 1 / 1;
        border: 2px solid #2b3d52;
        border-radius: 6px;
        overflow: hidden;
        background-color: #f8f9fa;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        box-sizing: border-box;
    }

    /* Grüner Rand für die 4. Spalte und 4. Zeile */
    .green-border {
        border: 3.5px solid #2ecc71 !important;
        box-shadow: 0 0 7px rgba(46, 204, 113, 0.4) !important;
    }

    .bingo-card img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
        z-index: 1;
    }

    .placeholder-box {
        position: absolute;
        top: 20%;
        width: 100%;
        text-align: center;
        color: #777;
        font-size: clamp(0.7rem, 2.5vw, 0.95rem);
        line-height: 1.2;
        z-index: 1;
    }

    /* Beschriftungs-Balken für den Aktivitätsnamen */
    .card-title-bar {
        position: relative;
        z-index: 2;
        width: 100%;
        background: rgba(255, 255, 255, 0.92);
        color: #111;
        font-size: clamp(0.52rem, 1.8vw, 0.72rem);
        font-weight: 700;
        text-align: center;
        padding: 3px 2px;
        line-height: 1.15;
        border-top: 1px solid rgba(0,0,0,0.1);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    /* Trennbalken vor der 4. Zeile */
    .row-separator {
        width: 100%;
        height: 10px;
    }

    /* 6. Roter BINGO-Stempel */
    .stamp-overlay {
        position: absolute;
        top: 42%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-18deg);
        border: 2px solid #d90429;
        color: #d90429;
        font-family: 'Arial Black', Impact, sans-serif;
        font-size: clamp(0.6rem, 2.8vw, 1.1rem);
        font-weight: 900;
        text-transform: uppercase;
        padding: 2px 4px;
        border-radius: 4px;
        background-color: rgba(255, 255, 255, 0.92);
        box-shadow: 0 0 6px rgba(217, 4, 41, 0.4);
        pointer-events: none;
        z-index: 10;
        white-space: nowrap;
    }

    /* 7. Buttons kompakt & touchfreundlich */
    div[data-testid="stButton"] button, 
    div[data-testid="stPopover"] button {
        width: 100% !important;
        min-width: 0 !important;
        padding: 0px !important;
        font-size: 0.85rem !important;
        height: 30px !important;
        min-height: 30px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 5px !important;
    }

    /* Pfeil-Icon beim Stift ausblenden für maximalen Platz */
    div[data-testid="stPopover"] button svg {
        display: none !important;
    }

    /* Popover-Popup auf Mobilgeräten optimal öffnen */
    div[data-testid="stPopoverBody"] {
        max-width: 90vw !important;
        z-index: 999999 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Kopfbereich
# ---------------------------------------------------------
st.markdown("<div class='bingo-header'>B I N G O</div>", unsafe_allow_html=True)
st.markdown("<div class='bingo-sub'>Unser gemeinsames Aktivitäten-Board 💕</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4x4 Bingo-Gitter
# ---------------------------------------------------------
for row in range(GRID_SIZE):
    # Vor der letzten (4.) Zeile einen visuellen Abstandsbalken einfügen
    if row == 3:
        st.markdown("<div class='row-separator'></div>", unsafe_allow_html=True)

    cols = st.columns(GRID_SIZE)
    for col in range(GRID_SIZE):
        idx = row * GRID_SIZE + col
        k = str(idx)
        item = data[k]

        # Prüfen, ob das Feld zur 4. Zeile (row == 3) oder 4. Spalte (col == 3) gehört
        is_green_border = (row == 3 or col == 3)
        border_class = " green-border" if is_green_border else ""

        with cols[col]:
            # Stempel erzeugen, wenn erledigt
            stamp_html = "<div class='stamp-overlay'>BINGO!</div>" if item.get("done", False) else ""

            # Titel der Aktivität ermitteln
            activity_title = item.get("title", f"Aktivität #{idx+1}").strip()
            if not activity_title:
                activity_title = f"Aktivität #{idx+1}"

            title_html = f"<div class='card-title-bar' title='{activity_title}'>{activity_title}</div>"

            # Bild oder Platzhalter laden
            if item.get("image_b64"):
                img_src = f"data:image/jpeg;base64,{item['image_b64']}"
                content_html = f"<img src='{img_src}' alt='{activity_title}'>"
            else:
                content_html = "<div class='placeholder-box'>📷</div>"

            # Kachel rendern (Bild/Platzhalter + Titelbar + optionaler Stempel)
            card_html = f"<div class='bingo-card{border_class}'>{content_html}{title_html}{stamp_html}</div>"
            st.markdown(card_html, unsafe_allow_html=True)

            # Zwei Buttons nebeneinander: 🎯 zum Abhaken, ✏️ zum Bearbeiten
            btn1, btn2 = st.columns(2)
            with btn1:
                btn_symbol = "↩️" if item.get("done") else "🎯"
                if st.button(btn_symbol, key=f"done_{idx}", use_container_width=True, help="Erledigt"):
                    data[k]["done"] = not data[k].get("done", False)
                    save_data(data)
                    st.rerun()

            with btn2:
                with st.popover("✏️", use_container_width=True, help="Bearbeiten"):
                    st.markdown(f"**Feld #{idx+1} bearbeiten**")
                    new_title = st.text_input("Aktivität", value=item.get("title", ""), key=f"t_{idx}")
                    new_desc = st.text_input("Notiz (optional)", value=item.get("description", ""), key=f"d_{idx}")
                    uploaded_file = st.file_uploader("Foto hochladen", type=["png", "jpg", "jpeg", "webp"], key=f"f_{idx}")

                    if st.button("Speichern", key=f"s_{idx}", type="primary", use_container_width=True):
                        data[k]["title"] = new_title
                        data[k]["description"] = new_desc
                        if uploaded_file is not None:
                            image = Image.open(uploaded_file)
                            image.thumbnail((500, 500))
                            buf = io.BytesIO()
                            image.convert("RGB").save(buf, format="JPEG", quality=82)
                            data[k]["image_b64"] = base64.b64encode(buf.getvalue()).decode()
                        save_data(data)
                        st.success("Gespeichert!")
                        st.rerun()

st.write("---")

# ---------------------------------------------------------
# Fortschritt & Optionen
# ---------------------------------------------------------
done_count = sum(1 for v in data.values() if v.get("done"))
st.info(f"🏆 Fortschritt: **{done_count} von {TOTAL_TILES}** Feldern erledigt!")

with st.expander("⚙️ Optionen"):
    if st.button("🔄 Alle Bingo-Stempel zurücksetzen"):
        for k in data:
            data[k]["done"] = False
        save_data(data)
        st.rerun()
