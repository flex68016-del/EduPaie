#!/usr/bin/env python3
# =============================================================================
# make_icon.py - Génération de l'icône .ico à partir du SVG
# =============================================================================
# Rôle : Convertir l'icône SVG en format ICO pour l'exécutable Windows
# =============================================================================
# Ce fichier utilise :
# - PySide6.QSvgRenderer pour charger le SVG
# - PySide6.QPainter pour dessiner l'image
# - PySide6.QIcon pour créer l'icône
# =============================================================================
# Pourquoi ce script : Windows nécessite un fichier .ico pour l'icône de l'exécutable
# PyInstaller peut utiliser directement un .ico comme icône de l'exécutable
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt


def svg_to_ico(svg_path: Path, ico_path: Path, sizes: list = None) -> None:
    """
    Convertit un fichier SVG en fichier ICO avec plusieurs tailles.
    
    Args:
        svg_path: Chemin vers le fichier SVG source
        ico_path: Chemin vers le fichier ICO de destination
        sizes: Liste des tailles d'icônes à générer (défaut: [16, 32, 48, 64, 128, 256])
    
    Pourquoi plusieurs tailles : Windows utilise différentes tailles d'icônes
    selon l'affichage (barre des tâches, explorateur, bureau, etc.)
    """
    if sizes is None:
        sizes = [16, 32, 48, 64, 128, 256]
    
    # Chargement du SVG
    # Pourquoi QSvgRenderer : Permet de rendre un SVG sur un QPixmap
    renderer = QSvgRenderer(str(svg_path))
    
    if not renderer.isValid():
        raise ValueError(f"Le fichier SVG n'est pas valide : {svg_path}")
    
    # Création de l'icône avec plusieurs tailles
    # Pourquoi QIcon : Conteneur d'icônes avec plusieurs résolutions
    icon = QIcon()
    
    for size in sizes:
        # Création d'un QPixmap carré de la taille demandée
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # Dessin du SVG sur le QPixmap
        # Pourquoi QPainter : Permet de dessiner le SVG sur le pixmap
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        # Ajout de la taille à l'icône
        icon.addPixmap(pixmap)
    
    # Sauvegarde de l'icône en format ICO
    # Pourquoi .ico : Format d'icône Windows standard
    ico_path.parent.mkdir(parents=True, exist_ok=True)
    icon.write(str(ico_path))
    
    print(f"[OK] Icône générée : {ico_path}")
    print(f"[OK] Tailles incluses : {sizes}")


if __name__ == "__main__":
    # Chemins des fichiers
    # Pourquoi edupaie/assets : Dossier des ressources de l'application
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    svg_path = project_root / "edupaie" / "assets" / "edupaie-icon.svg"
    ico_path = project_root / "edupaie" / "assets" / "edupaie.ico"
    
    # Génération de l'icône
    print(f"Génération de l'icône : {svg_path} -> {ico_path}")
    svg_to_ico(svg_path, ico_path)
