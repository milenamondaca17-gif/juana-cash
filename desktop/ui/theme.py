import os
import json

# ── Paletas ────────────────────────────────────────────────────────────────────
TEMAS = {
    "violeta_calido": {
        "nombre": "🟣 Violeta Cálido",
        "bg_app":      "#F5F3FF",
        "bg_card":     "#FFFFFF",
        "bg_navbar":   "#FFFFFF",
        "bg_input":    "#F9F8FF",
        "bg_hover":    "#EDE9FE",
        "bg_selected": "#DDD6FE",
        "primary":        "#7C3AED",
        "primary_hover":  "#6D28D9",
        "primary_light":  "#EDE9FE",
        "primary_text":   "#FFFFFF",
        "accent_green":   "#10B981",
        "accent_orange":  "#F97316",
        "accent_rose":    "#EC4899",
        "accent_yellow":  "#F59E0B",
        "text_main":   "#1E1B4B",
        "text_muted":  "#6B7280",
        "border":      "#E5E7EB",
        "border_card": "#EDE9FE",
        "success":     "#10B981",
        "warning":     "#F59E0B",
        "danger":      "#EF4444",
        "navbar_text":      "#6B7280",
        "navbar_active":    "#7C3AED",
        "navbar_active_bg": "#EDE9FE",
        "navbar_border":    "#7C3AED",
        "logo_color":       "#7C3AED",
    },
    "naranja_cielo": {
        "nombre": "🟠 Naranja Cielo",
        "bg_app":      "#FFFBF5",
        "bg_card":     "#FFFFFF",
        "bg_navbar":   "#FFFFFF",
        "bg_input":    "#FFF7ED",
        "bg_hover":    "#FFEDD5",
        "bg_selected": "#FED7AA",
        "primary":        "#EA580C",
        "primary_hover":  "#C2410C",
        "primary_light":  "#FFEDD5",
        "primary_text":   "#FFFFFF",
        "accent_green":   "#0EA5E9",
        "accent_orange":  "#F97316",
        "accent_rose":    "#FB7185",
        "accent_yellow":  "#FBBF24",
        "text_main":   "#431407",
        "text_muted":  "#78716C",
        "border":      "#E7E5E4",
        "border_card": "#FED7AA",
        "success":     "#16A34A",
        "warning":     "#D97706",
        "danger":      "#DC2626",
        "navbar_text":      "#78716C",
        "navbar_active":    "#EA580C",
        "navbar_active_bg": "#FFEDD5",
        "navbar_border":    "#EA580C",
        "logo_color":       "#EA580C",
    },
    "rosa_sage": {
        "nombre": "🌸 Rosa Sage",
        "bg_app":      "#FDF2F8",
        "bg_card":     "#FFFFFF",
        "bg_navbar":   "#FFFFFF",
        "bg_input":    "#FDF2F8",
        "bg_hover":    "#FCE7F3",
        "bg_selected": "#FBCFE8",
        "primary":        "#DB2777",
        "primary_hover":  "#BE185D",
        "primary_light":  "#FCE7F3",
        "primary_text":   "#FFFFFF",
        "accent_green":   "#4ADE80",
        "accent_orange":  "#FB923C",
        "accent_rose":    "#F472B6",
        "accent_yellow":  "#FDE68A",
        "text_main":   "#500724",
        "text_muted":  "#9CA3AF",
        "border":      "#F9A8D4",
        "border_card": "#FBCFE8",
        "success":     "#22C55E",
        "warning":     "#FB923C",
        "danger":      "#DC2626",
        "navbar_text":      "#9CA3AF",
        "navbar_active":    "#DB2777",
        "navbar_active_bg": "#FCE7F3",
        "navbar_border":    "#DB2777",
        "logo_color":       "#DB2777",
    },
    "lila_sol": {
        "nombre": "💛 Lila Sol",
        "bg_app":      "#FAFAF9",
        "bg_card":     "#FFFFFF",
        "bg_navbar":   "#FFFFFF",
        "bg_input":    "#F9F5FF",
        "bg_hover":    "#F3E8FF",
        "bg_selected": "#E9D5FF",
        "primary":        "#9333EA",
        "primary_hover":  "#7E22CE",
        "primary_light":  "#F3E8FF",
        "primary_text":   "#FFFFFF",
        "accent_green":   "#84CC16",
        "accent_orange":  "#FCD34D",
        "accent_rose":    "#F9A8D4",
        "accent_yellow":  "#FDE047",
        "text_main":   "#3B0764",
        "text_muted":  "#71717A",
        "border":      "#E4E4E7",
        "border_card": "#E9D5FF",
        "success":     "#22C55E",
        "warning":     "#EAB308",
        "danger":      "#EF4444",
        "navbar_text":      "#71717A",
        "navbar_active":    "#9333EA",
        "navbar_active_bg": "#F3E8FF",
        "navbar_border":    "#9333EA",
        "logo_color":       "#9333EA",
    },
    "clasico_oscuro": {
        "nombre": "🌑 Clásico Oscuro",
        "bg_app":      "#050e1a",
        "bg_card":     "#0d1b30",
        "bg_navbar":   "#0a1628",
        "bg_input":    "#111d33",
        "bg_hover":    "#111d33",
        "bg_selected": "#1a2744",
        "primary":        "#556EE6",
        "primary_hover":  "#4458b5",
        "primary_light":  "#1a2744",
        "primary_text":   "#FFFFFF",
        "accent_green":   "#34C38F",
        "accent_orange":  "#F1B44C",
        "accent_rose":    "#e63946",
        "accent_yellow":  "#F1B44C",
        "text_main":   "#F0F0F0",
        "text_muted":  "#8D99AE",
        "border":      "#1a2744",
        "border_card": "#1a2744",
        "success":     "#34C38F",
        "warning":     "#F1B44C",
        "danger":      "#e63946",
        "navbar_text":      "#8899aa",
        "navbar_active":    "#e63946",
        "navbar_active_bg": "#111d33",
        "navbar_border":    "#e63946",
        "logo_color":       "#e63946",
    },
}

_CONFIG_PATH = os.path.join(os.path.expanduser("~"), "JuanaCash_Data", "app_config.json")


def get_tema_key() -> str:
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("tema", "violeta_calido")
    except Exception:
        pass
    return "violeta_calido"


def guardar_tema(key: str):
    try:
        os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
        config = {}
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        config["tema"] = key
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_tema() -> dict:
    return TEMAS.get(get_tema_key(), TEMAS["violeta_calido"])


def get_qss(t: dict | None = None) -> str:
    if t is None:
        t = get_tema()
    return f"""
/* ── Base ── */
QMainWindow, QDialog, QWidget {{
    background-color: {t['bg_app']};
    color: {t['text_main']};
    font-family: 'Segoe UI', Arial, sans-serif;
}}

/* ── Frame / Card ── */
QFrame {{
    background-color: {t['bg_card']};
    border: none;
}}

/* ── Inputs ── */
QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit {{
    background: {t['bg_input']};
    color: {t['text_main']};
    border: 1.5px solid {t['border']};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    selection-background-color: {t['primary']};
    selection-color: white;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
    border-color: {t['primary']};
    background: {t['bg_card']};
}}
QLineEdit:disabled, QTextEdit:disabled {{
    background: {t['border']};
    color: {t['text_muted']};
}}

/* ── ComboBox ── */
QComboBox {{
    background: {t['bg_input']};
    color: {t['text_main']};
    border: 1.5px solid {t['border']};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
}}
QComboBox:focus {{ border-color: {t['primary']}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {t['bg_card']};
    color: {t['text_main']};
    selection-background-color: {t['primary']};
    selection-color: white;
    border: 1px solid {t['border']};
}}

/* ── Tables ── */
QTableWidget {{
    background: {t['bg_card']};
    gridline-color: {t['border']};
    border: none;
    color: {t['text_main']};
    font-size: 13px;
    border-radius: 10px;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background: {t['bg_selected']};
    color: {t['text_main']};
}}
QTableWidget::item:hover {{
    background: {t['bg_hover']};
}}
QHeaderView::section {{
    background: {t['bg_app']};
    color: {t['text_muted']};
    font-weight: bold;
    font-size: 11px;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid {t['border']};
}}

/* ── Buttons ── */
QPushButton {{
    background: {t['primary']};
    color: {t['primary_text']};
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton:hover {{
    background: {t['primary_hover']};
}}
QPushButton:pressed {{
    background: {t['primary_hover']};
}}
QPushButton:disabled {{
    background: {t['border']};
    color: {t['text_muted']};
}}

/* ── Scrollbar ── */
QScrollBar:vertical {{
    background: {t['bg_app']};
    width: 7px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t['primary_light']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t['primary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {t['bg_app']};
    height: 7px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {t['primary_light']};
    border-radius: 4px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── CheckBox ── */
QCheckBox {{
    color: {t['text_main']};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 2px solid {t['border']};
    background: {t['bg_input']};
}}
QCheckBox::indicator:checked {{
    background: {t['primary']};
    border-color: {t['primary']};
}}

/* ── GroupBox ── */
QGroupBox {{
    border: 1.5px solid {t['border']};
    border-radius: 10px;
    margin-top: 16px;
    padding: 12px;
    color: {t['text_main']};
    font-weight: bold;
    background: {t['bg_card']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {t['primary']};
}}

/* ── Tooltip ── */
QToolTip {{
    background: {t['bg_card']};
    color: {t['text_main']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── MessageBox ── */
QMessageBox {{
    background: {t['bg_card']};
    color: {t['text_main']};
}}
QMessageBox QLabel {{
    color: {t['text_main']};
    background: transparent;
    border: none;
}}
QMessageBox QPushButton {{
    min-width: 80px;
    min-height: 32px;
}}
"""
