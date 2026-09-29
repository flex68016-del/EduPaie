# =============================================================================
# edupaie.spec - Configuration PyInstaller pour EduPaie
# =============================================================================
# Rôle : Configuration pour créer un exécutable Windows autonome avec PyInstaller.
# =============================================================================
# Pourquoi ce fichier : PyInstaller utilise ce fichier .spec pour savoir quels
# fichiers inclure, comment empaqueter l'application, et quelles options utiliser.
# =============================================================================
#
# Options principales expliquées :
# - onefile : Crée un seul fichier .exe (plus facile à distribuer)
# - windowed : Crée une application graphique (pas de console DOS en arrière-plan)
# - datas : Inclut les fichiers de données (images, icônes, fichiers SQL)
# - hiddenimports : Inclut les modules non détectés automatiquement
# - icon : Icône de l'application
# =============================================================================
#
# Commande de construction :
# pyinstaller edupaie.spec
# ou
# pyinstaller --onefile --windowed --icon=icon.ico edupaie/main.py
# =============================================================================

# Analyse de l'application pour détecter les imports
# Pourquoi : PyInstaller analyse le code pour trouver toutes les dépendances
a = Analysis(
    ['edupaie/main.py'],
    # Chemin du fichier principal de l'application
    # Pourquoi main.py : Point d'entrée de l'application PySide6
    
    pathex=[],
    # Analyse récursive de tous les imports
    # Pourquoi : Inclut toutes les dépendances directes et indirectes
    
    binaries=[],
    # Binaires à inclure (DLL, etc.)
    # Pourquoi vide : Pas de binaires externes nécessaires pour EduPaie
    
    datas=[
        # Inclusion des fichiers de données et ressources
        # Pourquoi datas : Fichiers non Python qui doivent être inclus dans l'exécutable
        
        # Schéma SQL de la base de données
        ('edupaie/db/schema.sql', 'edupaie/db'),
        # Pourquoi : L'application doit pouvoir initialiser le schéma de la base de données
        # Le 'edupaie/db' signifie : inclus dans le sous-dossier edupaie/db/
        
        # Base de données modèle avec données de test
        ('edupaie/edupaie.db', 'edupaie'),
        # Pourquoi : Base de données modèle avec données de test pour la démonstration
        # L'exécutable copiera cette base vers user_data_dir au premier lancement
        # Le 'edupaie' signifie : inclus dans le sous-dossier edupaie/ (structure projet)
        
        # Script de création de la base modèle
        ('edupaie/db/create_model_db.py', 'edupaie/db'),
        # Pourquoi : Permet de recréer la base modèle si nécessaire
        # Le 'edupaie/db' signifie : inclus dans le sous-dossier edupaie/db/
        
        # Fichiers de l'application (README, etc.)
        ('README.md', '.'),
        # Pourquoi : Permet à l'utilisateur de lire la documentation
        # Le '.' signifie : inclus à la racine du dossier d'extraction
        
        # Assets (icônes, images, etc.)
        # ('edupaie/assets/*', 'assets'),
        # Pourquoi : Icônes et autres ressources visuelles de l'application
        # Commenté : Le dossier assets n'existe pas encore dans le projet
        # Pour décommenter : Créer le dossier edupaie/assets/ et ajouter des icônes
    ],
    
    hiddenimports=[
        # Option pour collecter tous les sous-modules de PySide6
        # Pourquoi --collect-all : Inclut automatiquement tous les plugins et sous-modules
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        
        # Option pour collecter tous les sous-modules de fpdf2
        'fpdf',
        
        # Module paths (critique pour PyInstaller)
        'edupaie.utils.paths',
    ],
    
    hookspath=[],
    # Chemins vers les hooks personnalisés
    # Pourquoi vide : Pas de hooks personnalisés nécessaires pour EduPaie
    
    hooksconfig={},
    # Configuration des hooks
    # Pourquoi vide : Configuration par défaut suffisante
    
    runtime_hooks=[],
    # Hooks exécutés au runtime
    # Pourquoi vide : Pas de hooks runtime nécessaires pour EduPaie
)

# Configuration de l'exécutable
pyz = PYZ(
    a.pure,
    # Archive PYZ optimisée
    # Pourquoi pure : Inclut uniquement les modules nécessaires, optimise la taille
    
    a.zipped_data,
    # Données compressées
    # Pourquoi : Réduit la taille de l'exécutable
    
)
exe = EXE(
    pyz,
    a.scripts,
    # Scripts de l'application
    # Pourquoi : Inclut le script principal et ses dépendances
    
    a.binaries,
    # Binaires inclus (DLL, etc.)
    # Pourquoi : Inclut les DLL nécessaires à PySide6 et à l'application
    
    a.datas,
    # Fichiers de données (SQL, assets, etc.)
    # Pourquoi : Inclut les fichiers spécifiés dans Analysis.datas
    
    [],
    # Exclusion des binaires (vide)
    # Pourquoi : Pas de binaires à exclure spécifiquement
    
    name='Edupaie',
    # Nom de l'exécutable généré
    # Pourquoi : Nom de l'application sans extension .exe
    
    debug=False,
    # Mode debug désactivé
    # Pourquoi : Optimise l'exécutable pour la production (pas de console de debug)
    
    console=False,
    # Pas de console DOS
    # Pourquoi windowed : Crée une application graphique sans console en arrière-plan
    # Pourquoi console=False : Application GUI, pas besoin de console visible
    
    icon='NONE',
    # Icône de l'application
    # Pourquoi icon : L'exe affiche cette icône dans l'explorateur Windows
    # Pourquoi NONE : Le dossier assets n'existe pas encore dans le projet
    # Pour utiliser une icône : Créer edupaie/assets/icon.ico et décommenter ci-dessous
    # icon='edupaie/assets/icon.ico',
)
