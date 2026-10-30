import streamlit as st
import json
import os
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import datetime
import random

# ---------------------------------------------------------
# Seitenkonfiguration: Schlankes Layout
# ---------------------------------------------------------
st.set_page_config(
    page_title="Nora & Dominik Aktivitäten-Board",
    page_icon="😊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DATA_FILE = "bingo_data.json"
HISTORY_FILE = "bingo_history.json"
GRID_SIZE = 4  # 4x4 = 16 Felder (3x3 Aktivitäten + 7 Belohnungen)
TOTAL_TILES = GRID_SIZE * GRID_SIZE

# ---------------------------------------------------------
# Daten laden, speichern & automatische Speicherpunkte
# ---------------------------------------------------------
def get_default_data():
    defaults = {}
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            idx = r * GRID_SIZE + c
            is_reward = (r == 3 or c == 3)
            default_title = f"🎁 Belohnung #{idx+1}" if is_reward else f"Aktivität #{idx+1}"
            defaults[str(idx)] = {
                "title": default_title,
                "description": "",
                "image_b64": None,
                "done": False
            }
    return defaults

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for i in range(TOTAL_TILES):
                    k = str(i)
                    if k not in data:
                        r = i // GRID_SIZE
                        c = i % GRID_SIZE
                        is_reward = (r == 3 or c == 3)
                        data[k] = {
                            "title": f"🎁 Belohnung" if is_reward else f"Aktivität #{i+1}",
                            "description": "",
                            "image_b64": None,
                            "done": False
                        }
                return data
        except Exception:
            return get_default_data()
    return get_default_data()

def load_history():
    """Lädt die Liste der gespeicherten Sicherungspunkte"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_backup(data_snapshot):
    """Speichert einen neuen Sicherungspunkt und behält nur die letzten 3"""
    history = load_history()
    now_str = datetime.datetime.now().strftime("%d.%m.%Y um %H:%M:%S Uhr")
    history.append({
        "timestamp": now_str,
        "data": data_snapshot
    })
    # Nur die neuesten 3 Speicherpunkte behalten
    history = history[-3:]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def save_data(data, create_backup=True):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if create_backup:
        save_backup(data)

# ---------------------------------------------------------
# Export-Funktion: Komplettes Board als Bild generieren
# ---------------------------------------------------------
def generate_board_image(board_data):
    card_size = 300
    gap = 12
    divider_size = 20
    header_height = 130
    footer_height = 40
    
    # Gesamtbreite & Gesamthöhe (mit den markanten Trennern vor Spalte 4 & Zeile 4)
    width = card_size * 4 + gap * 3 + divider_size + 40
    height = header_height + card_size * 4 + gap * 3 + divider_size + footer_height
    
    img = Image.new("RGB", (width, height), color="#0b1320")
    draw = ImageDraw.Draw(img)
    
    # Titel zeichnen
    draw.text((width // 2, 45), "B I N G O", fill="#ffffff", anchor="mm")
    draw.text((width // 2, 90), "Nora & Dominik Aktivitäten-Board", fill="#e2e8f0", anchor="mm")
    
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            idx = r * GRID_SIZE + c
            item = board_data.get(str(idx), {})
            is_reward = (r == 3 or c == 3)
            
            # Koordinaten berechnen
            extra_x = divider_size if c == 3 else 0
            extra_y = divider_size if r == 3 else 0
            x = 20 + c * (card_size + gap) + extra_x
            y = header_height + r * (card_size + gap) + extra_y
            
            # Kachel-Hintergrund
            tile_img = Image.new("RGB", (card_size, card_size), color="#ffffff")
            
            # Wenn Bild vorhanden, einpassen
            if item.get("image_b64"):
                try:
                    raw_b64 = base64.b64decode(item["image_b64"])
                    loaded = Image.open(io.BytesIO(raw_b64)).convert("RGB")
                    loaded.thumbnail((card_size, card_size))
                    # Zentriert einfügen
                    pos_x = (card_size - loaded.width) // 2
                    pos_y = (card_size - loaded.height) // 2
                    tile_img.paste(loaded, (pos_x, pos_y))
                except Exception:
                    pass
            
            tile_draw = ImageDraw.Draw(tile_img)
            
            # Beschriftungsbalken unten
            tile_draw.rectangle([0, card_size - 48, card_size, card_size], fill=(255, 255, 255, 240))
            title_text = item.get("title", f"Aktivität #{idx+1}")
            if len(title_text) > 22:
                title_text = title_text[:20] + "..."
            tile_draw.text((card_size // 2, card_size - 24), title_text, fill="#111111", anchor="mm")
            
            # BINGO-Stempel zeichnen, falls erledigt
            if item.get("done"):
                tile_draw.rectangle([35, 110, card_size - 35, 170], fill=(255, 255, 255, 230), outline="#d90429", width=4)
                tile_draw.text((card_size // 2, 140), "B I N G O !", fill="#d90429", anchor="mm")
            
            # In das Hauptbild einfügen
            img.paste(tile_img, (x, y))
            
            # Grüner Rand bei Belohnungen, sonst dunkler Rand
            border_col = "#2ecc71" if is_reward else "#2b3d52"
            border_w = 6 if is_reward else 2
            draw.rectangle([x, y, x + card_size, y + card_size], outline=border_col, width=border_w)
    
    # Vertikaler Trennbalken vor Spalte 4
    div_x = 20 + 3 * (card_size + gap) + (divider_size // 2) - 3
    draw.rectangle([div_x, header_height, div_x + 6, height - footer_height], fill="#ffffff")
    
    # Horizontaler Trennbalken vor Zeile 4
    div_y = header_height + 3 * (card_size + gap) + (divider_size // 2) - 3
    draw.rectangle([20, div_y, width - 20, div_y + 6], fill="#ffffff")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ---------------------------------------------------------
# Session State Initialisierung
# ---------------------------------------------------------
if "bingo_data" not in st.session_state:
    st.session_state.bingo_data = load_data()

data = load_data()
st.session_state.bingo_data = data

# ---------------------------------------------------------
# CSS: Responsives 4x4-Layout, Trenner & Stempel
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
        font-size: clamp(2.2rem, 7.5vw, 3.2rem);
        letter-spacing: 5px;
        color: #1e3a5f;
        margin-top: -15px;
        margin-bottom: 2px;
    }
    .bingo-sub {
        text-align: center;
        font-size: clamp(0.85rem, 3.2vw, 1.05rem);
        color: #e2e8f0;
        font-weight: 600;
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

    /* 3. Spaltenbreite: Spalten 1-4 */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        width: calc(25% - 4px) !important;
        min-width: 0 !important;
        max-width: calc(25% - 4px) !important;
        flex: 1 1 calc(25% - 4px) !important;
        padding: 0 !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }

    /* Vertikaler Trenner: Markante Trennlinie vor der 4. Spalte */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4),
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(4) {
        border-left: 5px solid #0b1320 !important;
        padding-left: 5px !important;
        margin-left: 3px !important;
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
        border-left: none !important;
        padding-left: 0 !important;
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

    /* Grüner Rand für die 4. Spalte und 4. Zeile (Belohnungsfelder) */
    .green-border {
        border: 3.5px solid #2ecc71 !important;
        box-shadow: 0 0 8px rgba(46, 204, 113, 0.5) !important;
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

    /* Beschriftungs-Balken */
    .card-title-bar {
        position: relative;
        z-index: 2;
        width: 100%;
        background: rgba(255, 255, 255, 0.93);
        color: #111;
        font-size: clamp(0.5rem, 1.8vw, 0.72rem);
        font-weight: 700;
        text-align: center;
        padding: 3px 2px;
        line-height: 1.15;
        border-top: 1px solid rgba(0,0,0,0.1);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    /* Horizontaler Trennbalken vor der 4. Zeile */
    .horizontal-divider {
        width: 100%;
        height: 8px;
        background-color: #0b1320;
        border-radius: 4px;
        margin-top: 6px;
        margin-bottom: 12px;
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

    div[data-testid="stPopover"] button svg {
        display: none !important;
    }

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
st.markdown("<div class='bingo-sub'>Nora & Dominik Aktivitäten-Board 😊</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Prüfung auf erreichte 3er-Reihen / Spalten (Belohnungen) & Ballons
# ---------------------------------------------------------
completed_rewards = []

# Zeilen 0, 1, 2 prüfen (Aktivitäten in Spalten 0, 1, 2)
for r in range(3):
    if all(data[str(r * GRID_SIZE + c)].get("done", False) for c in range(3)):
        reward_name = data[str(r * GRID_SIZE + 3)].get("title", f"Belohnung Zeile {r+1}")
        completed_rewards.append(f"🎉 **Reihe {r+1} voll:** Ihr habt die Belohnung *'{reward_name}'* (rechts) freigeschaltet!")

# Spalten 0, 1, 2 prüfen (Aktivitäten in Zeilen 0, 1, 2)
for c in range(3):
    if all(data[str(r * GRID_SIZE + c)].get("done", False) for r in range(3)):
        reward_name = data[str(3 * GRID_SIZE + c)].get("title", f"Belohnung Spalte {c+1}")
        completed_rewards.append(f"🌟 **Spalte {c+1} voll:** Ihr habt die Belohnung *'{reward_name}'* (unten) freigeschaltet!")

# Diagonale 1 (0, 5, 10)
if data["0"].get("done") and data["5"].get("done") and data["10"].get("done"):
    diag_reward = data["15"].get("title", "Hauptbelohnung")
    completed_rewards.append(f"👑 **Diagonale voll:** Haupt-Belohnung *'{diag_reward}'* (rechts unten) freigeschaltet!")

# Wenn neue Belohnungen vorhanden sind: Feier mit Ballons!
if completed_rewards:
    for msg in completed_rewards:
        st.success(msg)
    if "balloons_fired" not in st.session_state:
        st.balloons()
        st.session_state["balloons_fired"] = True

# ---------------------------------------------------------
# 4x4 Bingo-Gitter (3x3 Aktivitäten + 7 Belohnungen)
# ---------------------------------------------------------
for row in range(GRID_SIZE):
    # Vor der 4. Zeile den horizontalen Trennbalken rendern
    if row == 3:
        st.markdown("<div class='horizontal-divider'></div>", unsafe_allow_html=True)

    cols = st.columns(GRID_SIZE)
    for col in range(GRID_SIZE):
        idx = row * GRID_SIZE + col
        k = str(idx)
        item = data[k]

        is_reward = (row == 3 or col == 3)
        border_class = " green-border" if is_reward else ""

        with cols[col]:
            # Stempel erzeugen, wenn erledigt
            stamp_html = "<div class='stamp-overlay'>BINGO!</div>" if item.get("done", False) else ""

            # Titel ermitteln
            default_label = f"🎁 Belohnung" if is_reward else f"Aktivität #{idx+1}"
            title_text = item.get("title", default_label).strip()
            if not title_text:
                title_text = default_label

            title_html = f"<div class='card-title-bar' title='{title_text}'>{title_text}</div>"

            # Bild oder Platzhalter laden
            if item.get("image_b64"):
                img_src = f"data:image/jpeg;base64,{item['image_b64']}"
                content_html = f"<img src='{img_src}' alt='{title_text}'>"
            else:
                icon = "🎁" if is_reward else "📷"
                content_html = f"<div class='placeholder-box'>{icon}</div>"

            # Kachel rendern
            card_html = f"<div class='bingo-card{border_class}'>{content_html}{title_html}{stamp_html}</div>"
            st.markdown(card_html, unsafe_allow_html=True)

            # Zwei Buttons nebeneinander: 🎯 zum Abhaken, ✏️ zum Bearbeiten
            btn1, btn2 = st.columns(2)
            with btn1:
                btn_symbol = "↩️" if item.get("done") else "🎯"
                if st.button(btn_symbol, key=f"done_{idx}", use_container_width=True, help="Erledigt / Stempel"):
                    data[k]["done"] = not data[k].get("done", False)
                    # Wenn abgehakt, Ballons freischalten
                    if data[k]["done"]:
                        st.session_state.pop("balloons_fired", None)
                    save_data(data)
                    st.rerun()

            with btn2:
                pop_help = "Belohnung bearbeiten" if is_reward else "Aktivität bearbeiten"
                with st.popover("✏️", use_container_width=True, help=pop_help):
                    field_type = "🎁 Belohnung" if is_reward else "Aktivität"
                    st.markdown(f"**{field_type} #{idx+1} anpassen**")
                    new_title = st.text_input("Name", value=item.get("title", ""), key=f"t_{idx}")
                    new_desc = st.text_input("Notiz (optional)", value=item.get("description", ""), key=f"d_{idx}")
                    uploaded_file = st.file_uploader("Foto / Screenshot", type=["png", "jpg", "jpeg", "webp"], key=f"f_{idx}")

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
# Feature: 🎲 Zufalls-Date-Picker ("Was machen wir heute?")
# ---------------------------------------------------------
col_dice, col_export = st.columns(2)

with col_dice:
    if st.button("🎲 Was machen wir heute?", use_container_width=True, help="Wählt per Zufall eine offene Aktivität aus"):
        # Nur Aktivitäten aus dem 3x3 Bereich (Zeile 0-2, Spalte 0-2), die noch nicht erledigt sind
        open_activities = []
        for r in range(3):
            for c in range(3):
                idx = r * GRID_SIZE + c
                if not data[str(idx)].get("done", False):
                    act_title = data[str(idx)].get("title", f"Aktivität #{idx+1}")
                    open_activities.append(act_title)
        
        if open_activities:
            chosen = random.choice(open_activities)
            st.session_state["picked_date"] = chosen
        else:
            st.session_state["picked_date"] = "🎉 Alle 9 Aktivitäten sind bereits erledigt! Zeit für die Belohnungen!"

if "picked_date" in st.session_state:
    st.info(f"✨ **Vorschlag für euer Date:** {st.session_state['picked_date']}")

with col_export:
    board_bytes = generate_board_image(data)
    st.download_button(
        label="📥 Board als Bild laden",
        data=board_bytes,
        file_name="Nora_und_Dominik_Bingo_Board.png",
        mime="image/png",
        use_container_width=True,
        help="Speichert das komplette Board als hochauflösendes Bild auf eurem Smartphone/PC"
    )

# ---------------------------------------------------------
# Fortschritt & Optionen mit Speicherpunkten
# ---------------------------------------------------------
done_count = sum(1 for v in data.values() if v.get("done"))
st.info(f"🏆 Fortschritt: **{done_count} von {TOTAL_TILES}** Feldern erledigt!")

with st.expander("⚙️ Optionen & Speicherpunkte"):
    st.markdown("### 💾 Speicherpunkte wiederherstellen")
    history = load_history()

    if history:
        # Letzte 3 Sicherungspunkte (neuester zuerst)
        options = {
            f"Punkt {len(history) - i}: {item['timestamp']}": item["data"]
            for i, item in enumerate(reversed(history))
        }
        selected_label = st.selectbox(
            "Wähle einen der letzten 3 Speicherpunkte zum Laden:",
            options=list(options.keys()),
            key="history_selector"
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📥 Stand wiederherstellen", type="primary", use_container_width=True):
                restored_data = options[selected_label]
                save_data(restored_data, create_backup=False)
                st.success(f"{selected_label} erfolgreich wiederhergestellt!")
                st.rerun()
        with c2:
            if st.button("💾 Jetzt manuell sichern", use_container_width=True):
                save_backup(data)
                st.success("Aktueller Stand als neuer Speicherpunkt gesichert!")
                st.rerun()
    else:
        st.write("Noch keine automatischen Speicherpunkte vorhanden.")
        if st.button("💾 Jetzt ersten Speicherpunkt anlegen", use_container_width=True):
            save_backup(data)
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔄 Board zurücksetzen")
    if st.button("Alle Bingo-Stempel entfernen", use_container_width=True):
        save_backup(data)
        for k in data:
            data[k]["done"] = False
        save_data(data, create_backup=True)
        st.success("Alle Stempel wurden zurückgesetzt (vorheriger Stand wurde gesichert)!")
        st.rerun()
