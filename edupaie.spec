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
        ('edupaie/db/schema.sql', '.'),
        # Pourquoi : L'application doit pouvoir initialiser le schéma de la base de données
        # Le '.' signifie : inclus à la racine du dossier d'extraction
        
        # Base de données modèle avec données de test
        ('edupaie/edupaie.db', 'edupaie'),
        # Pourquoi : Base de données modèle avec données de test pour la démonstration
        # L'exécutable copiera cette base vers user_data_dir au premier lancement
        # Le 'edupaie' signifie : inclus dans le sous-dossier edupaie/ (structure projet)
        
        # Script de création de la base modèle
        ('edupaie/db/create_model_db.py', '.'),
        # Pourquoi : Permet de recréer la base modèle si nécessaire
        
        # Fichiers de l'application (README, etc.)
        ('README.md', '.'),
        # Pourquoi : Permet à l'utilisateur de lire la documentation
        
        # Assets (icônes, images, etc.)
        ('edupaie/assets/*', 'assets'),
        # Pourquoi : Icônes et autres ressources visuelles de l'application
        # Le 'assets' signifie : inclus dans le sous-dossier assets/
    ],
    
    hiddenimports=[
        # Modules non détectés automatiquement par PyInstaller
        # Pourquoi hiddenimports : PyInstaller ne détecte pas tous les imports dynamiques
        # ou conditionnels, donc on les liste explicitement
        
        'PySide6.QtCore',
        # Pourquoi : Core Qt souvent manquant dans les analyses statiques
        
        'PySide6.QtGui',
        # Pourquoi : GUI Qt souvent manquant dans les analyses statiques
        
        'PySide6.QtWidgets',
        # Pourquoi : Widgets Qt souvent manquant dans les analyses statiques
        
        'fpdf',
        # Pourquoi : Bibliothèque de génération PDF, parfois non détectée
        
        'fpdf.pdf',
        # Pourquoi : Module interne de fpdf2
        
        'fpdf.fonts',
        # Pourquoi : Module interne de fpdf2 pour les polices
        
        'fpdf.syntax.tagged',
        # Pourquoi : Module interne de fpdf2 pour la syntaxe PDF
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
    
    exclude_binaries=True,
    # Exclut les binaires de l'exécutable
    # Pourquoi : Les binaires sont déjà inclus via le paramètre binaries de Analysis
    
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
    # Note : Utilise --windowed en ligne de commande, mais console=False dans le .spec
    
    icon='edupaie/assets/icon.ico',
    # Icône de l'application
    # Pourquoi icon : L'exe affiche cette icône dans l'explorateur Windows
    # Note : L'icône doit être créée manuellement ou obtenue depuis une ressource
    # Pour l'instant, commenté si l'icône n'existe pas encore
    # icon='NONE',  # Pas d'icône par défaut
)

# Collecte les fichiers à inclure dans l'exécutable
coll = COLLECT(
    exe,
    a.binaries,
    # Binaires inclus (DLL, etc.)
    # Pourquoi : Inclut les DLL nécessaires à PySide6 et à l'application
    
    a.datas,
    # Fichiers de données (SQL, assets, etc.)
    # Pourquoi : Inclut les fichiers spécifiés dans Analysis.datas
    
    strip=False,
    # Ne supprime pas les symboles de débogage
    # Pourquoi strip=False : Parfois les symboles sont nécessaires pour PySide6
)
