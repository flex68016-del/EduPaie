# =============================================================================
# paths.py - Gestion des chemins de ressources et de données utilisateur
# =============================================================================
# Rôle : Fournit les fonctions pour gérer les chemins de fichiers, de ressources
# et de données utilisateur, ainsi que l'initialisation de la base de données.
# =============================================================================
# Ce fichier utilise :
# - sys pour détecter l'environnement d'exécution (dev ou PyInstaller)
# - os.path pour la manipulation des chemins
# - shutil pour copier des fichiers
# - logging pour la gestion des logs
# =============================================================================
# Ce fichier est utilisé par :
# - L'application pour localiser les fichiers de configuration, la base de données, etc.
# - L'initialisation de la base de données au premier lancement
# =============================================================================

import sys
import os
import shutil
import logging
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
        # En dev : resource_path("db/schema.sql") -> /home/user/edupaie/edupaie/db/schema.sql
        # Avec PyInstaller : resource_path("db/schema.sql") -> /tmp/_MEI123/edupaie/db/schema.sql
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
    - Les reçus PDF générés
    
    Pourquoi un répertoire séparé : Sépare les données de l'application du code,
    permet de mettre à jour l'application sans perdre les données utilisateur,
    et respecte les conventions de chaque OS.
    
    Pourquoi %APPDATA% sur Windows : C'est le dossier standard pour les données
    applications (Roaming AppData est synchronisé entre les machines si l'utilisateur
    utilise un profil itinérant). L'application y stocke ses données de manière persistante.
    
    Returns:
        Le chemin vers le répertoire des données utilisateur.
    
    Raises:
        OSError: Si le répertoire ne peut pas être créé (droits insuffisants, etc.)
    
    Example:
        # Windows : C:/Users/Jean/AppData/Roaming/EduPaie
        # Linux : /home/jean/.config/edupaie
        # macOS : /Users/jean/Library/Application Support/EduPaie
    """
    # Nom de l'application
    app_name = "EduPaie"
    
    # Détection du système d'exploitation
    # Pourquoi : Chaque OS a son propre emplacement pour les données utilisateur
    if sys.platform == "win32":
        # Windows : AppData\Roaming
        # Pourquoi %APPDATA% : Variable d'environnement standard de Windows
        # Pourquoi APPDATA au lieu de LOCALAPPDATA : AppData/Roaming est synchronisé
        # entre les machines via les profils itinérants, ce qui est souhaitable pour
        # une application de gestion de paiements accessibles sur plusieurs postes
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
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        # Si la création échoue (droits insuffisants, etc.), lever une erreur claire
        raise OSError(
            f"Impossible de créer le répertoire des données utilisateur : {data_dir}\n"
            f"Erreur : {e}\n"
            f"Vérifiez que vous avez les droits d'écriture dans ce répertoire."
        ) from e
    
    return data_dir


def initialize_database():
    """
    Initialise la base de données au premier lancement de l'application.
    
    Au premier lancement, cette fonction :
    1. Copie la base de données modèle (edupaie.db avec données de test) depuis
       les ressources vers le dossier utilisateur
    2. Si la base modèle n'existe pas, crée une base vide via schema.sql
    
    Pourquoi cette fonction : Permet à l'application de démarrer avec des données
    de test pour la démonstration, tout en garantissant que les données sont stockées
    dans un dossier persistant (pas dans le dossier temporaire de PyInstaller).
    
    Pourquoi ne pas écrire dans le dossier PyInstaller : PyInstaller extrait l'application
    dans un dossier temporaire (sys._MEIPASS) qui est supprimé à la fermeture de l'application.
    Les données écrites dans ce dossier seraient perdues à chaque fermeture, ce qui n'est
    pas acceptable pour une application de gestion de paiements.
    
    Pourquoi user_data_dir : Ce dossier est persistant et respecte les conventions OS,
    garantissant que les données survivent aux mises à jour de l'application.
    """
    # Import local pour éviter les imports circulaires
    from edupaie.data.database import Database
    
    # Chemin de la base de données persistante
    db_path = user_data_dir() / "edupaie.db"
    
    # Chemin de la base de données modèle (embarquée dans les ressources)
    # Pourquoi edupaie.db : La base modèle est dans le dossier edupaie/ du projet
    db_model_path = resource_path("edupaie.db")
    
    # Chemin du schema SQL (embarqué dans les ressources)
    # Pourquoi edupaie/db/schema.sql : Le schema est dans edupaie/db/ du projet
    schema_path = resource_path("edupaie/db/schema.sql")
    
    # Si la base persistante n'existe pas, l'initialiser
    if not db_path.exists():
        if db_model_path.exists():
            # Copie de la base modèle vers le dossier utilisateur
            shutil.copy2(db_model_path, db_path)
        else:
            # Si la base modèle n'existe pas, créer une base vide via schema.sql
            # Pourquoi lire le schema.sql : Le schema est nécessaire pour créer les tables
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                # Création de la base avec le schema
                # Pourquoi connect() : Établit la connexion et initialise le schéma si vide
                Database(str(db_path)).connect()
            else:
                # Fallback : créer une base vide avec connect() qui utilisera le schema interne
                Database(str(db_path)).connect()
    
    # Configuration du logging pour écrire dans le dossier utilisateur
    # Pourquoi logging : Permet de tracer les erreurs et le comportement de l'application
    # Pourquoi dossier utilisateur : Les logs sont persistants et accessibles pour le support
    # Note : La configuration est déjà faite dans error_handler.py, donc on configure seulement
    # le niveau INFO ici si ce n'est pas déjà configuré
    log_file = user_data_dir() / "edupaie.log"
    
    if not logging.getLogger().handlers:
        logging.basicConfig(
            filename=str(log_file),
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    logging.info("Application EduPaie démarrée")
    logging.info(f"Base de données : {db_path}")
    logging.info(f"Fichier de logs : {log_file}")
