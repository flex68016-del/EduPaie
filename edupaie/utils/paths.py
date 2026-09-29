# =============================================================================
# paths.py - Gestion des chemins de ressources
# =============================================================================
# Rôle : Fournit des fonctions pour gérer les chemins de fichiers et de ressources.
# =============================================================================
# Ce fichier utilise :
# - sys pour détecter l'environnement d'exécution (dev ou PyInstaller)
# - os.path pour la manipulation des chemins
# =============================================================================
# Ce fichier est utilisé par :
# - L'application pour localiser les fichiers de configuration, la base de données, etc.
# =============================================================================

import sys
import os
from pathlib import Path
from typing import Union


def resource_path(relative_path: Union[str, Path]) -> Path:
    """
    Retourne le chemin absolu d'une ressource, que l'application soit en dev ou packagée.
    
    Cette fonction gère deux cas :
    1. En développement : les ressources sont dans le répertoire du script
    2. Avec PyInstaller : les ressources sont extraites dans sys._MEIPASS
    
    Pourquoi cette fonction : PyInstaller extrait toutes les ressources dans un
    répertoire temporaire (sys._MEIPASS) lors de l'exécution, donc les chemins
    relatifs ne fonctionnent plus. Cette fonction adapte automatiquement le chemin.
    
    Args:
        relative_path: Chemin relatif vers la ressource (ex: "db/schema.sql")
    
    Returns:
        Le chemin absolu vers la ressource.
    
    Example:
        # En dev : resource_path("db/schema.sql") -> /home/user/edupaie/db/schema.sql
        # Avec PyInstaller : resource_path("db/schema.sql") -> /tmp/_MEI123/db/schema.sql
    """
    # Conversion en Path pour une manipulation plus facile
    relative_path = Path(relative_path)
    
    # Détection de l'environnement d'exécution
    # Pourquoi sys._MEIPASS : Cette variable est définie uniquement par PyInstaller
    # lors de l'exécution de l'exécutable packagé
    if hasattr(sys, '_MEIPASS'):
        # Cas PyInstaller : les ressources sont dans le répertoire d'extraction
        base_path = Path(sys._MEIPASS)
    else:
        # Cas développement : les ressources sont dans le répertoire du script
        # Pourquoi __file__ : Donne le chemin absolu du fichier en cours d'exécution
        base_path = Path(__file__).parent.parent
    
    # Construction du chemin absolu
    # Pourquoi resolve : Normalise le chemin (résout les .. et les liens symboliques)
    absolute_path = (base_path / relative_path).resolve()
    
    return absolute_path


def user_data_dir() -> Path:
    """
    Retourne le répertoire des données utilisateur de l'application.
    
    Ce répertoire est utilisé pour stocker :
    - La base de données SQLite
    - Les fichiers de configuration
    - Les logs
    - Les fichiers temporaires
    
    Pourquoi un répertoire séparé : Sépare les données de l'application du code,
    permet de mettre à jour l'application sans perdre les données utilisateur,
    et respecte les conventions de chaque OS (AppData sur Windows, ~/.config sur Linux).
    
    Returns:
        Le chemin vers le répertoire des données utilisateur.
    
    Example:
        # Windows : C:\Users\Jean\AppData\Roaming\EduPaie
        # Linux : /home/jean/.config/edupaie
        # macOS : /Users/jean/Library/Application Support/EduPaie
    """
    # Nom de l'application
    app_name = "EduPaie"
    
    # Détection du système d'exploitation
    # Pourquoi : Chaque OS a son propre emplacement pour les données utilisateur
    if sys.platform == "win32":
        # Windows : AppData\Roaming
        # Pourquoi APPDATA : Variable d'environnement standard de Windows
        base_path = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    elif sys.platform == "darwin":
        # macOS : Library/Application Support
        # Pourquoi : Convention macOS pour les données utilisateur
        base_path = Path.home() / 'Library' / 'Application Support'
    else:
        # Linux et autres : ~/.config
        # Pourquoi XDG_CONFIG_HOME : Standard Linux pour les données utilisateur
        base_path = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    
    # Construction du chemin complet
    data_dir = base_path / app_name
    
    # Création du répertoire s'il n'existe pas
    # Pourquoi mkdir(parents=True) : Crée tous les répertoires parents si nécessaire
    # Pourquoi exist_ok=True : Ne déclenche pas d'erreur si le répertoire existe déjà
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir
