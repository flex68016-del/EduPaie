# =============================================================================
# theme.py - Thème visuel centralisé EduPaie (Premium)
# =============================================================================
# Rôle : Définit toutes les constantes de couleurs, la palette Qt et le QSS
# centralisé pour l'application. Force un mode clair cohérent quel que soit
# le thème système (Windows sombre/clair).
# Inspiration : Stripe, Linear, Notion
# =============================================================================
# Ce fichier utilise :
# - PySide6.QtGui pour QPalette, QColor, QFont, QGraphicsDropShadowEffect
# - PySide6.QtCore pour Qt
# - PySide6.QtWidgets pour QWidget
# =============================================================================
# Ce fichier est utilisé par :
# - main.py pour appliquer la palette et le QSS global
# - Tous les widgets UI pour accéder aux couleurs et formater les montants
# =============================================================================

from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from pathlib import Path


# =============================================================================
# CONSTANTES DE COULEURS PREMIUM
# =============================================================================
# Pourquoi ces couleurs : Palette inspirée de Stripe, Linear et Notion pour
# un look moderne et haut de gamme. Le mode clair est forcé pour éviter
# les problèmes de lisibilité sur Windows en mode sombre.
# =============================================================================

# Couleurs de fond et surface
BG_APP = "#F5F6FA"           # Fond principal de l'application (gris très clair)
SURFACE = "#FFFFFF"          # Surface des widgets (blanc)
BORDER = "#E6E8F0"           # Bordures (gris clair)
HOVER_ROW = "#F1F5FF"        # Survol de ligne (bleu très clair)

# Couleurs de texte
TEXT = "#0F172A"             # Texte principal (bleu gris très foncé)
TEXT_MUTED = "#475569"       # Texte secondaire (gris moyen)
TEXT_SUBTLE = "#52607A"      # Texte subtil (gris clair)

# Couleurs d'accent (dégradé ACCENT -> ACCENT_2)
ACCENT = "#4F46E5"           # Accent principal (indigo)
ACCENT_2 = "#2563EB"        # Accent secondaire (bleu royal)

# Couleurs de la barre latérale (dégradé vertical)
SIDEBAR_TOP = "#0B1220"      # Haut de la barre latérale (bleu très foncé)
SIDEBAR_BOTTOM = "#16213A"   # Bas de la barre latérale (bleu foncé)
SIDEBAR_TEXT = "#E2E8F0"     # Texte de la barre latérale (gris très clair)

# Couleurs de danger
DANGER = "#DC2626"           # Couleur de danger (rouge)

# Couleurs de statut (paire bg/fg pour contraste WCAG >= 4.5)
STATUS = {
    "Soldé": {
        "bg": "#DCFCE7",     # Vert très clair
        "fg": "#166534"      # Vert très foncé
    },
    "Partiellement payé": {
        "bg": "#FEF3C7",     # Ambre très clair
        "fg": "#92400E"      # Ambre très foncé
    },
    "Non payé": {
        "bg": "#FEE2E2",     # Rouge très clair
        "fg": "#991B1B"      # Rouge très foncé
    }
}

# Teintes des icônes de cartes (paire bg/fg pour contraste WCAG >= 4.5)
ICON_TINTS = {
    "blue": {
        "bg": "#EEF2FF",     # Bleu très clair
        "fg": "#4338CA"      # Bleu indigo foncé
    },
    "green": {
        "bg": "#DCFCE7",     # Vert très clair
        "fg": "#166534"      # Vert très foncé
    },
    "amber": {
        "bg": "#FEF3C7",     # Ambre très clair
        "fg": "#92400E"      # Ambre très foncé
    },
    "red": {
        "bg": "#FEE2E2",     # Rouge très clair
        "fg": "#991B1B"      # Rouge très foncé
    }
}


# =============================================================================
# TYPOGRAPHIE
# =============================================================================
# Pourquoi ces tailles : Hiérarchie visuelle claire pour guider l'œil
# Titre de page 24 pt, sous-titre 11 pt, corps 10 pt, KPI 26 pt
# =============================================================================

# Rayons
RADIUS_CARD = 16            # Rayon des cartes
RADIUS_FIELD = 10           # Rayon des champs et boutons
RADIUS_PILL = 999           # Rayon des pastilles (cercle complet)

# Ombre douce des cartes
def add_shadow(widget: QWidget) -> None:
    """
    Ajoute une ombre douce à un widget pour l'effet de profondeur.
    
    Utilise QGraphicsDropShadowEffect avec :
    - Flou : 28 px
    - Décalage vertical : 6 px
    - Couleur : rgba(15, 23, 42, 0.08) (bleu gris très foncé, opacité 8%)
    
    Args:
        widget: Le widget auquel ajouter l'ombre.
    
    Pourquoi cette ombre : Crée une hiérarchie visuelle et sépare les
    cartes du fond, comme Stripe et Linear.
    """
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(28)
    shadow.setOffset(0, 6)
    shadow.setColor(QColor(15, 23, 42, 8))  # rgba(15,23,42,0.08)
    widget.setGraphicsEffect(shadow)


# =============================================================================
# CHARGEMENT DES POLICES
# =============================================================================
# Pourquoi Inter : Police moderne et lisible utilisée par Stripe et Linear
# Fallback à Segoe UI si le dossier assets/fonts/ n'existe pas
# =============================================================================

_FONT_LOADED = False
_FONT_FAMILY = "Segoe UI"  # Fallback par défaut

def load_fonts() -> None:
    """
    Charge la police Inter depuis assets/fonts/ si disponible.
    
    Si assets/fonts/Inter-*.ttf existe, charge les variantes (Regular, Medium, Bold)
    avec QFontDatabase. Sinon, utilise Segoe UI (fallback Windows).
    
    Pourquoi cette fonction : Permet d'utiliser Inter sans dépendance externe,
    avec un fallback gracieux si les fichiers ne sont pas présents.
    """
    global _FONT_LOADED, _FONT_FAMILY
    
    try:
        fonts_dir = Path(__file__).parent.parent / "assets" / "fonts"
        if fonts_dir.exists():
            from PySide6.QtGui import QFontDatabase
            
            # Charger les variantes Inter
            font_files = [
                "Inter-Regular.ttf",
                "Inter-Medium.ttf",
                "Inter-Bold.ttf"
            ]
            
            for font_file in font_files:
                font_path = fonts_dir / font_file
                if font_path.exists():
                    font_id = QFontDatabase.addApplicationFont(str(font_path))
                    if font_id >= 0 and not _FONT_LOADED:
                        _FONT_FAMILY = "Inter"
                        _FONT_LOADED = True
    except:
        pass  # Fallback à Segoe UI en cas d'erreur


# Charger les polices au démarrage
load_fonts()


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
    text = QColor(TEXT)
    text_muted = QColor(TEXT_MUTED)
    text_subtle = QColor(TEXT_SUBTLE)
    accent = QColor(ACCENT)
    
    # ===== Groupe Active =====
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, bg_app)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.AlternateBase, QColor(HOVER_ROW))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, surface)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, text_subtle)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipText, text)
    
    # ===== Groupe Inactive =====
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, bg_app)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, text_muted)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.AlternateBase, QColor(HOVER_ROW))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, text_muted)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, surface)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, text_muted)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, text_subtle)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipText, text_muted)
    
    # ===== Groupe Disabled =====
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, bg_app)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, text_subtle)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.AlternateBase, QColor(HOVER_ROW))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, text_subtle)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, surface)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, text_subtle)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, text_subtle)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipText, text_subtle)
    
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
    - Police Inter ou Segoe UI selon disponibilité
    - Couleurs centralisées depuis les constantes premium
    - États hover, focus, disabled
    - Variantes de boutons (primary avec dégradé, secondary, danger, ghost)
    - Rayons modernes (16px pour cartes, 10px pour champs, 999px pour pastilles)
    - Scrollbars fines (8px)
    
    Returns:
        Le QSS complet sous forme de chaîne.
    """
    return f"""
    /* ===== Styles globaux ===== */
    QWidget {{
        color: {TEXT};
        font-family: "{_FONT_FAMILY}", Arial, sans-serif;
        font-size: 10pt;
    }}
    
    QMainWindow, QDialog {{
        background: {BG_APP};
    }}
    
    QLabel {{
        color: {TEXT};
        background: transparent;
    }}
    
    /* ===== Champs de saisie ===== */
    QLineEdit, QComboBox, QDateEdit, QSpinBox {{
        background: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_FIELD}px;
        padding: 8px 12px;
        min-height: 40px;
    }}
    
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {{
        border: 1.5px solid {ACCENT};
    }}
    
    QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QSpinBox:disabled {{
        background: {BG_APP};
        color: {TEXT_SUBTLE};
        border: 1px solid {BORDER};
    }}
    
    QComboBox QAbstractItemView {{
        background: {SURFACE};
        color: {TEXT};
        selection-background-color: {ACCENT};
        selection-color: white;
        border: 1px solid {BORDER};
        border-radius: {RADIUS_FIELD}px;
    }}
    
    /* ===== Boutons ===== */
    QPushButton {{
        border-radius: {RADIUS_FIELD}px;
        min-height: 40px;
        padding: 8px 20px;
        font-weight: 600;
    }}
    
    /* Bouton primary avec dégradé ACCENT -> ACCENT_2 */
    QPushButton[variant="primary"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_2});
        color: white;
        border: none;
    }}
    
    QPushButton[variant="primary"]:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_2}, stop:1 {ACCENT});
    }}
    
    QPushButton[variant="primary"]:pressed {{
        background: {ACCENT};
    }}
    
    /* Bouton secondary */
    QPushButton[variant="secondary"] {{
        background: {SURFACE};
        color: {ACCENT};
        border: 1px solid {ACCENT};
    }}
    
    QPushButton[variant="secondary"]:hover {{
        background: {HOVER_ROW};
    }}
    
    QPushButton[variant="secondary"]:pressed {{
        background: {ACCENT};
        color: white;
    }}
    
    /* Bouton danger */
    QPushButton[variant="danger"] {{
        background: {DANGER};
        color: white;
        border: none;
    }}
    
    QPushButton[variant="danger"]:hover {{
        background: #B91C1C;
    }}
    
    QPushButton[variant="danger"]:pressed {{
        background: {DANGER};
    }}
    
    /* Bouton ghost */
    QPushButton[variant="ghost"] {{
        background: transparent;
        color: {TEXT};
        border: none;
    }}
    
    QPushButton[variant="ghost"]:hover {{
        background: {HOVER_ROW};
    }}
    
    QPushButton:disabled {{
        background: {BG_APP};
        color: {TEXT_SUBTLE};
        border: 1px solid {BORDER};
    }}
    
    /* ===== Tableaux ===== */
    QTableView, QTableWidget {{
        background: {SURFACE};
        alternate-background-color: {HOVER_ROW};
        color: {TEXT};
        gridline-color: {BORDER};
        border: none;
        border-radius: {RADIUS_CARD}px;
        selection-background-color: {HOVER_ROW};
        selection-color: {TEXT};
    }}
    
    QHeaderView::section {{
        background: {BG_APP};
        color: {TEXT_SUBTLE};
        font-weight: 700;
        font-size: 9pt;
        text-transform: uppercase;
        padding: 12px 16px;
        border: none;
        border-bottom: 1px solid {BORDER};
        border-right: none;
    }}
    
    QHeaderView::section:first {{
        border-left: none;
    }}
    
    /* ===== Barre de défilement (fines, 8px) ===== */
    QScrollBar:vertical {{
        background: {BG_APP};
        width: 8px;
        border-radius: 4px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 4px;
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
        height: 8px;
        border-radius: 4px;
        margin: 0px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        border-radius: 4px;
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
        background: {TEXT};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 9pt;
    }}
    
    /* ===== Group boxes ===== */
    QGroupBox {{
        background: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: {RADIUS_CARD}px;
        margin-top: 12px;
        padding-top: 16px;
        font-weight: 600;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
    }}
    
    /* ===== Barre latérale ===== */
    QWidget#sidebar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {SIDEBAR_TOP}, stop:1 {SIDEBAR_BOTTOM});
    }}
    
    QWidget#sidebar QPushButton {{
        background: transparent;
        color: {SIDEBAR_TEXT};
        border: none;
        text-align: left;
        padding: 12px 16px;
        border-radius: 10px;
        font-weight: 500;
    }}
    
    QWidget#sidebar QPushButton:hover {{
        background: rgba(255, 255, 255, 0.1);
    }}
    
    QWidget#sidebar QPushButton[active="true"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_2});
        color: white;
    }}
    
    QWidget#sidebar QLabel#sidebar_title {{
        color: white;
        font-size: 18pt;
        font-weight: 700;
        padding: 20px 16px 10px;
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
    
    /* ===== Cartes KPI ===== */
    QFrame[card_type="kpi"] {{
        background: {SURFACE};
        border: none;
        border-radius: {RADIUS_CARD}px;
        padding: 20px;
    }}
    
    QLabel[label_type="kpi_title"] {{
        color: {TEXT_MUTED};
        font-size: 11pt;
        font-weight: 500;
    }}
    
    QLabel[label_type="kpi_value"] {{
        color: {TEXT};
        font-size: 26pt;
        font-weight: 700;
    }}
    
    QLabel[label_type="kpi_context"] {{
        color: {TEXT_SUBTLE};
        font-size: 10pt;
    }}
    
    /* ===== Labels de statut ===== */
    QLabel[statut_bg] {{
        padding: 6px 12px;
        border-radius: 999px;
        font-weight: 600;
        font-size: 9pt;
    }}
    
    /* ===== Labels avec setProperty dynamique ===== */
    QLabel[hasDynamicStyle="true"] {{
        padding: 6px 12px;
        border-radius: 999px;
        font-weight: 600;
        font-size: 9pt;
    }}
    
    /* ===== QMessageBox ===== */
    QMessageBox {{
        background: {SURFACE};
    }}
    
    QMessageBox QPushButton {{
        min-height: 36px;
        padding: 8px 20px;
        border-radius: {RADIUS_FIELD}px;
        font-weight: 600;
    }}
    
    /* ===== Labels avec setProperty dynamique ===== */
    QLabel[hasDynamicStyle="true"] {{
        padding: 6px 12px;
        border-radius: 999px;
        font-weight: 600;
        font-size: 9pt;
    }}
    
    QLabel[hasDynamicStyle="true"][statut_bg="#DCFCE7"] {{
        background: #DCFCE7;
        color: #166534;
    }}
    
    QLabel[hasDynamicStyle="true"][statut_bg="#FEF3C7"] {{
        background: #FEF3C7;
        color: #92400E;
    }}
    
    QLabel[hasDynamicStyle="true"][statut_bg="#FEE2E2"] {{
        background: #FEE2E2;
        color: #991B1B;
    }}
    
    QLabel[hasDynamicStyle="true"][statut_bg="#FFFFFF"] {{
        background: #FFFFFF;
        color: {TEXT};
    }}
    """
