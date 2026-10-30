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
# CSS: Garantiert echtes 4x4-Gitter auf Mobilgeräten
# ---------------------------------------------------------
st.markdown("""
<style>
    /* 1. Haupt-Container auf Handys maximal ausnutzen */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
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

    /* 3. Jede der 4 Kacheln bekommt exakt 25% Breite (auch auf dem Handy!) */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        width: calc(25% - 3px) !important;
        min-width: 0 !important;
        max-width: calc(25% - 3px) !important;
        flex: 1 1 25% !important;
        padding: 0 !important;
        margin: 0 !important;
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
        align-items: center;
        justify-content: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .bingo-card img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }

    .placeholder-box {
        text-align: center;
        color: #777;
        font-size: clamp(0.55rem, 2vw, 0.75rem);
        padding: 2px;
        line-height: 1.2;
    }

    /* 6. Roter BINGO-Stempel */
    .stamp-overlay {
        position: absolute;
        top: 50%;
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
        background-color: rgba(255, 255, 255, 0.9);
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
    cols = st.columns(GRID_SIZE)
    for col in range(GRID_SIZE):
        idx = row * GRID_SIZE + col
        k = str(idx)
        item = data[k]

        with cols[col]:
            # Stempel erzeugen, wenn erledigt
            stamp_html = "<div class='stamp-overlay'>BINGO!</div>" if item.get("done", False) else ""

            # Nur das Bild (oder sauberer Platzhalter)
            if item.get("image_b64"):
                img_src = f"data:image/jpeg;base64,{item['image_b64']}"
                content_html = f"<img src='{img_src}' alt='Feld {idx+1}'>"
            else:
                title_preview = item.get("title", f"#{idx+1}")[:8]
                content_html = f"<div class='placeholder-box'>📷<br><b>{title_preview}</b></div>"

            # Kachel rendern
            card_html = f"<div class='bingo-card'>{content_html}{stamp_html}</div>"
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
