# =============================================================================
# theme.py - Thème visuel centralisé EduPaie
# =============================================================================
# Rôle : Définit toutes les constantes de couleurs, la palette Qt et le QSS
# centralisé pour l'application. Force un mode clair cohérent quel que soit
# le thème système (Windows sombre/clair).
# =============================================================================
# Ce fichier utilise :
# - PySide6.QtGui pour QPalette, QColor, QFont
# - PySide6.QtCore pour Qt
# =============================================================================
# Ce fichier est utilisé par :
# - main.py pour appliquer la palette et le QSS global
# - Tous les widgets UI pour accéder aux couleurs et formater les montants
# =============================================================================

from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt


# =============================================================================
# CONSTANTES DE COULEURS
# =============================================================================
# Pourquoi ces couleurs : Palette cohérente inspirée de Tailwind CSS et
# Material Design pour une interface moderne et lisible. Le mode clair est
# forcé pour éviter les problèmes de lisibilité sur Windows en mode sombre.
# =============================================================================

# Couleurs de fond et surface
BG_APP = "#F3F5F9"           # Fond principal de l'application (gris très clair)
SURFACE = "#FFFFFF"          # Surface des widgets (blanc)
BORDER = "#D0D7E2"           # Bordures (gris moyen)
FOCUS = "#2563EB"            # Couleur de focus (bleu vif)

# Couleurs de texte
TEXT = "#1F2937"             # Texte principal (gris très foncé)
TEXT_MUTED = "#4B5563"       # Texte secondaire (gris moyen)
TEXT_DISABLED = "#6B7280"    # Texte désactivé (gris clair)

# Couleurs de la barre latérale
SIDEBAR = "#16233B"          # Fond de la barre latérale (bleu très foncé)
SIDEBAR_HOVER = "#23365A"    # Survol de la barre latérale (bleu foncé)

# Couleurs primaires
PRIMARY = "#2563EB"          # Couleur principale (bleu)
PRIMARY_HOVER = "#1D4ED8"    # Survol principal (bleu foncé)

# Couleurs de danger
DANGER = "#DC2626"           # Couleur de danger (rouge)
DANGER_HOVER = "#B91C1C"     # Survol danger (rouge foncé)

# Couleurs de sélection
SELECTION_BG = "#DBEAFE"     # Fond de sélection (bleu très clair)
ROW_ALT = "#F8FAFC"          # Fond alterné des lignes (gris très clair)
HEADER_BG = "#E8EDF5"        # Fond des en-têtes de tableau (gris clair)

# Couleurs de statut (paire bg/fg pour contraste WCAG >= 4.5)
STATUS = {
    "Soldé": {
        "bg": "#DCFCE7",     # Vert très clair
        "fg": "#166534"      # Vert très foncé
    },
    "Partiellement payé": {
        "bg": "#FEF3C7",     # Jaune très clair
        "fg": "#92400E"      # Jaune très foncé
    },
    "Non payé": {
        "bg": "#FEE2E2",     # Rouge très clair
        "fg": "#991B1B"      # Rouge très foncé
    }
}


# =============================================================================
# FONCTIONS DE FORMATAGE
# =============================================================================

def format_fcfa(montant: int) -> str:
    """
    Formate un montant en FCFA avec séparateur d'espace insécable.
    
    Args:
        montant: Le montant à formater (entier)
    
    Returns:
        Le montant formaté avec espaces (ex: 482000 -> "482 000 FCFA")
    
    Example:
        >>> format_fcfa(482000)
        "482 000 FCFA"
        >>> format_fcfa(10000)
        "10 000 FCFA"
    """
    # Utilisation de format avec l'espace comme séparateur de milliers
    formatted = f"{montant:,}".replace(",", " ")
    return f"{formatted} FCFA"


# =============================================================================
# PALETTE QT (MODE CLAIR FORCÉ)
# =============================================================================
# Pourquoi cette palette : Force un mode clair cohérent quel que soit le
# thème système de Windows. Définit explicitement tous les groupes Active,
# Inactive et Disabled pour éviter les héritages du thème système.
# =============================================================================

def build_palette() -> QPalette:
    """
    Construit et retourne une palette Qt pour forcer le mode clair.
    
    Définit explicitement tous les groupes de rôles de couleur :
    - Active : widgets actifs
    - Inactive : widgets inactifs
    - Disabled : widgets désactivés
    
    Returns:
        La palette Qt configurée.
    """
    palette = QPalette()
    
    # Conversion des hexadécimaux en QColor
    bg_app = QColor(BG_APP)
    surface = QColor(SURFACE)
    border = QColor(BORDER)
    focus = QColor(FOCUS)
    text = QColor(TEXT)
    text_muted = QColor(TEXT_MUTED)
    text_disabled = QColor(TEXT_DISABLED)
    selection_bg = QColor(SELECTION_BG)
    row_alt = QColor(ROW_ALT)
    
    # ===== Groupe Active =====
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, bg_app)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.AlternateBase, row_alt)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, surface)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, selection_bg)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, text)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, text_disabled)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipText, text)
    
    # ===== Groupe Inactive =====
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, bg_app)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, text_muted)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.AlternateBase, row_alt)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, text_muted)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, surface)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, text_muted)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, selection_bg)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, text_muted)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, text_disabled)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipText, text_muted)
    
    # ===== Groupe Disabled =====
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, bg_app)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, text_disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.AlternateBase, row_alt)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, text_disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, surface)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, text_disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, selection_bg)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, text_disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, text_disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipText, text_disabled)
    
    return palette


# =============================================================================
# QSS CENTRALISÉ
# =============================================================================
# Pourquoi ce QSS : Définit tous les styles visuels en un seul endroit
# pour une cohérence totale. Évite les setStyleSheet locaux et les styles
# disparates. Le style Fusion est utilisé pour neutraliser le thème système.
# =============================================================================

def refresh_style(widget: QWidget) -> None:
    """
    Force Qt à réappliquer le QSS après un changement de propriété dynamique.
    
    Sans cela, le nouveau style n'est pas pris en compte par Qt.
    
    Args:
        widget: Le widget dont le style doit être rafraîchi.
    
    Pourquoi cette fonction : Quand on change une propriété dynamique
    (property) sur un widget, Qt ne rafraîchit pas automatiquement le style.
    Il faut appeler unpolish() puis polish() pour forcer le recalcul.
    """
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def build_stylesheet() -> str:
    """
    Construit et retourne le QSS (Qt Style Sheet) centralisé.
    
    Définit les styles pour tous les widgets :
    - Police Segoe UI 10pt
    - Couleurs centralisées depuis les constantes
    - États hover, focus, disabled
    - Variantes de boutons (primary, secondary, danger)
    
    Returns:
        Le QSS complet sous forme de chaîne.
    """
    return f"""
    /* ===== Styles globaux ===== */
    QWidget {{
        color: {TEXT};
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 10pt;
    }}
    
    QMainWindow, QDialog {{
        background: {BG_APP};
    }}
    
    QLabel {{
        color: {TEXT};
        background: transparent;
    }}
    
    /* ===== Filtres et libellés ===== */
    QLabel[isFilter="true"] {{
        font-weight: bold;
        color: {TEXT};
    }}
    
    /* ===== Champs de saisie ===== */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {{
        background: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        min-height: 34px;
    }}
    
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {{
        border: 1px solid {FOCUS};
    }}
    
    QComboBox QAbstractItemView {{
        background: {SURFACE};
        color: {TEXT};
        selection-background-color: {SELECTION_BG};
        selection-color: {TEXT};
        border: 1px solid {BORDER};
    }}
    
    /* ===== Boutons ===== */
    QPushButton {{
        border-radius: 6px;
        min-height: 36px;
        padding: 5px 15px;
        font-weight: bold;
    }}
    
    QPushButton[variant="primary"] {{
        background: {PRIMARY};
        color: white;
        border: none;
    }}
    
    QPushButton[variant="primary"]:hover {{
        background: {PRIMARY_HOVER};
    }}
    
    QPushButton[variant="primary"]:pressed {{
        background: {PRIMARY};
    }}
    
    QPushButton[variant="secondary"] {{
        background: {SURFACE};
        color: {PRIMARY_HOVER};
        border: 1px solid {PRIMARY};
    }}
    
    QPushButton[variant="secondary"]:hover {{
        background: {SELECTION_BG};
    }}
    
    QPushButton[variant="secondary"]:pressed {{
        background: {PRIMARY};
        color: white;
    }}
    
    QPushButton[variant="danger"] {{
        background: {DANGER};
        color: white;
        border: none;
    }}
    
    QPushButton[variant="danger"]:hover {{
        background: {DANGER_HOVER};
    }}
    
    QPushButton[variant="danger"]:pressed {{
        background: {DANGER};
    }}
    
    QPushButton:disabled {{
        background: #E5E7EB;
        color: {TEXT_DISABLED};
        border: 1px solid #D1D5DB;
    }}
    
    /* ===== Tableaux ===== */
    QTableView, QTableWidget {{
        background: {SURFACE};
        alternate-background-color: {ROW_ALT};
        color: {TEXT};
        gridline-color: #E5E7EB;
        border: 1px solid {BORDER};
        selection-background-color: {SELECTION_BG};
        selection-color: {TEXT};
    }}
    
    QHeaderView::section {{
        background: {HEADER_BG};
        color: {TEXT};
        font-weight: bold;
        padding: 8px;
        border: none;
        border-bottom: 1px solid {BORDER};
        border-right: 1px solid {BORDER};
    }}
    
    QHeaderView::section:first {{
        border-left: none;
    }}
    
    /* ===== Barre de défilement ===== */
    QScrollBar:vertical {{
        background: {BG_APP};
        width: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 5px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_MUTED};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background: {BG_APP};
        height: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        border-radius: 5px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {TEXT_MUTED};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* ===== Tooltips ===== */
    QToolTip {{
        background: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 4px;
    }}
    
    /* ===== Group boxes ===== */
    QGroupBox {{
        background: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 10px;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    
    /* ===== Barre latérale ===== */
    QWidget#sidebar {{
        background: {SIDEBAR};
    }}
    
    QWidget#sidebar QPushButton {{
        background: transparent;
        color: white;
        border: none;
        text-align: left;
        padding: 10px 15px;
        border-radius: 6px;
    }}
    
    QWidget#sidebar QPushButton:hover {{
        background: {SIDEBAR_HOVER};
    }}
    
    QWidget#sidebar QPushButton[active="true"] {{
        background: {PRIMARY};
    }}
    
    QWidget#sidebar QLabel#sidebar_title {{
        color: white;
        font-size: 16pt;
        font-weight: bold;
        padding: 15px;
    }}
    
    /* ===== Barre d'état ===== */
    QStatusBar {{
        background: {SURFACE};
        color: {TEXT};
        border-top: 1px solid {BORDER};
    }}
    
    QStatusBar::item {{
        border: none;
    }}
    
    QStatusBar QLabel[status="success"] {{
        color: #166534;
        background: #DCFCE7;
        padding: 2px 8px;
        border-radius: 4px;
    }}
    
    QStatusBar QLabel[status="error"] {{
        color: #991B1B;
        background: #FEE2E2;
        padding: 2px 8px;
        border-radius: 4px;
    }}
    
    /* ===== Cartes KPI ===== */
    QFrame[card_type="kpi"] {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 15px;
    }}
    
    QLabel[label_type="kpi_title"] {{
        color: {TEXT_MUTED};
        font-size: 12pt;
    }}
    
    QLabel[label_type="kpi_value"] {{
        color: {TEXT};
        font-size: 22pt;
        font-weight: bold;
    }}
    
    /* ===== Barre latérale ===== */
    QWidget#sidebar {{
        background: {SIDEBAR};
    }}
    
    QWidget#sidebar QPushButton {{
        background: transparent;
        color: white;
        border: none;
        text-align: left;
        padding: 10px 15px;
        border-radius: 6px;
    }}
    
    QWidget#sidebar QPushButton:hover {{
        background: {SIDEBAR_HOVER};
    }}
    
    QWidget#sidebar QPushButton[active="true"] {{
        background: {PRIMARY};
    }}
    
    QWidget#sidebar QLabel#sidebar_title {{
        color: white;
        font-size: 16pt;
        font-weight: bold;
        padding: 15px;
    }}
    
    /* ===== Labels de statut ===== */
    QLabel[statut_bg] {{
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }}
    
    /* ===== Labels avec setProperty dynamique ===== */
    QLabel[hasDynamicStyle="true"] {{
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }}
    """
