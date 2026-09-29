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
        # Modules non détectés automatiquement par PyInstaller
        # Pourquoi hiddenimports : PyInstaller ne détecte pas tous les imports dynamiques
        # ou conditionnels, donc on les liste explicitement
        
        # Modules PySide6
        'PySide6.QtCore',
        # Pourquoi : Core Qt souvent manquant dans les analyses statiques
        
        'PySide6.QtGui',
        # Pourquoi : GUI Qt souvent manquant dans les analyses statiques
        
        'PySide6.QtWidgets',
        # Pourquoi : Widgets Qt souvent manquant dans les analyses statiques
        
        # Modules fpdf2
        'fpdf',
        # Pourquoi : Bibliothèque de génération PDF, parfois non détectée
        
        # Modules UI (tous les fichiers du dossier ui/)
        'edupaie.ui.students_view',
        # Pourquoi : Importé par main_window.py, non détecté automatiquement
        
        'edupaie.ui.student_form',
        # Pourquoi : Importé par students_view.py, non détecté automatiquement
        
        'edupaie.ui.student_detail',
        # Pourquoi : Importé par students_view.py, non détecté automatiquement
        
        'edupaie.ui.payment_dialog',
        # Pourquoi : Importé par student_detail.py, non détecté automatiquement
        
        'edupaie.ui.dashboard',
        # Pourquoi : Importé par main_window.py, non détecté automatiquement
        
        'edupaie.ui.error_handler',
        # Pourquoi : Importé par main.py, non détecté automatiquement
        
        # Modules services
        'edupaie.services.student_service',
        # Pourquoi : Importé par main_window.py, non détecté automatiquement
        
        'edupaie.services.payment_service',
        # Pourquoi : Importé par student_detail.py, non détecté automatiquement
        
        'edupaie.services.dashboard_service',
        # Pourquoi : Importé par main_window.py, non détecté automatiquement
        
        'edupaie.services.receipt_service',
        # Pourquoi : Importé par payment_dialog.py, non détecté automatiquement
        
        'edupaie.services.exceptions',
        # Pourquoi : Importé par tous les services, non détecté automatiquement
        
        # Modules data
        'edupaie.data.database',
        # Pourquoi : Importé par tous les services, non détecté automatiquement
        
        'edupaie.data.student_repository',
        # Pourquoi : Importé par student_service.py, non détecté automatiquement
        
        'edupaie.data.payment_repository',
        # Pourquoi : Importé par payment_service.py, non détecté automatiquement
        
        # Modules utils
        'edupaie.utils.paths',
        # Pourquoi : Importé par database.py et initialize_database(), non détecté automatiquement
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
