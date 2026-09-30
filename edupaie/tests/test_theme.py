# =============================================================================
# test_theme.py - Tests du thème visuel
# =============================================================================
# Rôle : Vérifier le contraste WCAG des couleurs et l'absence de styles locaux
# =============================================================================
# Ce fichier utilise :
# - pytest pour les tests
# - edupaie.ui.theme pour accéder aux constantes de couleurs
# =============================================================================
# Ce fichier est utilisé par :
# - pytest pour vérifier la qualité du thème
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from edupaie.ui.theme import STATUS, TEXT, TEXT_MUTED, TEXT_DISABLED, BG_APP, SURFACE, SIDEBAR_TEXT, SIDEBAR


def wcag_contrast_ratio(hex_fg: str, hex_bg: str) -> float:
    """
    Calcule le ratio de contraste WCAG entre deux couleurs hexadécimales.
    
    Args:
        hex_fg: Couleur du texte (hexadécimal, ex: "#166534")
        hex_bg: Couleur du fond (hexadécimal, ex: "#DCFCE7")
    
    Returns:
        Le ratio de contraste (entre 1 et 21)
    
    Reference:
        https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
    """
    def hex_to_rgb(hex_color: str) -> tuple:
        """Convertit une couleur hexadécimale en RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def relative_luminance(rgb: tuple) -> float:
        """Calcule la luminance relative selon la formule WCAG."""
        r, g, b = rgb
        # Normalisation et conversion linéaire
        def normalize(c: float) -> float:
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r_norm = normalize(r)
        g_norm = normalize(g)
        b_norm = normalize(b)
        
        # Luminance relative
        return 0.2126 * r_norm + 0.7152 * g_norm + 0.0722 * b_norm
    
    fg_rgb = hex_to_rgb(hex_fg)
    bg_rgb = hex_to_rgb(hex_bg)
    
    fg_luminance = relative_luminance(fg_rgb)
    bg_luminance = relative_luminance(bg_rgb)
    
    lighter = max(fg_luminance, bg_luminance)
    darker = min(fg_luminance, bg_luminance)
    
    return (lighter + 0.05) / (darker + 0.05)


def test_status_colors_contrast():
    """Vérifie que les couleurs de statut ont un contraste WCAG >= 4.5."""
    for statut, colors in STATUS.items():
        ratio = wcag_contrast_ratio(colors["fg"], colors["bg"])
        assert ratio >= 4.5, f"Contraste insuffisant pour {statut}: {ratio:.2f} (>= 4.5 requis)"


def test_text_on_background_contrast():
    """Vérifie le contraste du texte sur les fonds principaux."""
    # Texte principal sur fond d'application
    ratio = wcag_contrast_ratio(TEXT, BG_APP)
    assert ratio >= 4.5, f"Contraste insuffisant TEXT/BG_APP: {ratio:.2f}"
    
    # Texte principal sur fond de surface
    ratio = wcag_contrast_ratio(TEXT, SURFACE)
    assert ratio >= 4.5, f"Contraste insuffisant TEXT/SURFACE: {ratio:.2f}"
    
    # Texte atténué sur fond de surface
    ratio = wcag_contrast_ratio(TEXT_MUTED, SURFACE)
    assert ratio >= 4.5, f"Contraste insuffisant TEXT_MUTED/SURFACE: {ratio:.2f}"


def test_sidebar_text_contrast():
    """Vérifie le contraste du texte de la barre latérale sur son fond."""
    # Texte de la barre latérale (blanc) sur fond de la barre latérale (bleu foncé)
    ratio = wcag_contrast_ratio(SIDEBAR_TEXT, SIDEBAR)
    assert ratio >= 4.5, f"Contraste insuffisant SIDEBAR_TEXT/SIDEBAR: {ratio:.2f}"


def test_no_local_styles_in_ui_files():
    """Vérifie qu'aucun fichier UI (hors theme.py) ne contient setStyleSheet avec des couleurs en dur."""
    import os
    import re
    
    ui_dir = "edupaie/ui"
    excluded_files = ["theme.py", "__init__.py"]
    
    # Patterns à rechercher
    patterns = [
        r'setStyleSheet\s*\([^)]*\#[0-9A-Fa-f]{6}',  # setStyleSheet avec couleur hex en dur
    ]
    
    for filename in os.listdir(ui_dir):
        if not filename.endswith('.py'):
            continue
        if filename in excluded_files:
            continue
        
        filepath = os.path.join(ui_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                pytest.fail(f"{filename} contient des styles locaux avec couleurs en dur (pattern: {pattern}, {len(matches)} occurrences)")
