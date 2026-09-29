@echo off
REM =============================================================================
REM build.bat - Script de construction de l'exécutable EduPaie avec PyInstaller
REM =============================================================================
REM Rôle : Automatise la construction de l'exécutable Windows autonome.
REM =============================================================================
REM Pourquoi ce script : Simplifie la construction de l'exécutable en une seule
REM commande, évite d'oublier des options PyInstaller importantes.
REM =============================================================================
REM
REM Prérequis :
REM - Python 3.10+ installé
REM - PyInstaller installé : pip install pyinstaller
REM - Dependencies installées : pip install -r requirements.txt
REM =============================================================================
REM
REM Commande d'exécution :
REM build.bat
REM =============================================================================
REM
REM Sortie :
REM - dist/Edupaie.exe : Exécutable Windows autonome
REM - build/ : Dossier de construction PyInstaller (peut être supprimé)
REM =============================================================================

echo ========================================================================
echo Construction de l'exécutable EduPaie avec PyInstaller
echo ========================================================================
echo.

REM Vérification de l'installation de PyInstaller
REM Pourquoi : Si PyInstaller n'est pas installé, la construction échouera
REM Pourquoi utiliser le venv : Utilise l'environnement virtuel du projet
REM Pourquoi pip show avec venv : Vérifie si PyInstaller est installé dans le venv
"%~dp0venv\Scripts\python.exe" -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] PyInstaller n'est pas installe dans le venv.
    echo Installation en cours...
    "%~dp0venv\Scripts\python.exe" -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERREUR] Impossible d'installer PyInstaller.
        echo Veuillez executer : venv\Scripts\python.exe -m pip install pyinstaller
        pause
        exit /b 1
    )
)

echo [OK] PyInstaller est installe.
echo.

REM Vérification de l'existence du fichier de spec
REM Pourquoi : Le fichier .spec contient toute la configuration PyInstaller
REM Pourquoi --onefile : Crée un seul fichier .exe (plus facile à distribuer)
REM Pourquoi --windowed : Crée une application graphique (pas de console DOS)
if not exist "edupaie.spec" (
    echo [ERREUR] Le fichier edupaie.spec n'existe pas.
    echo Le fichier .spec est necessaire pour construire l'executable.
    pause
    exit /b 1
)

echo [OK] Fichier edupaie.spec trouve.
echo.

REM Construction de l'exécutable avec PyInstaller
REM Pourquoi sans .spec : Utiliser la ligne de commande avec --collect-all pour inclure tous les modules
REM Pourquoi --onefile : Crée un seul fichier .exe (plus facile à distribuer)
REM Pourquoi --windowed : Crée une application graphique sans console DOS
REM Pourquoi --name Edupaie : Nom de l'exécutable
REM Pourquoi --clean : Nettoie le dossier de construction avant reconstruction
REM Pourquoi --noconfirm : Confirme automatiquement le remplacement des fichiers
REM Pourquoi --collect-all edupaie : Inclut automatiquement tous les sous-modules du package edupaie
REM Pourquoi --collect-all PySide6 : Inclut automatiquement tous les plugins et sous-modules de PySide6
REM Pourquoi --add-data : Inclut les fichiers de données (SQL, base modèle, README)
REM Pourquoi utiliser le venv : Utilise l'environnement virtuel du projet
echo Construction de l'executable...
"%~dp0venv\Scripts\python.exe" -m PyInstaller --onefile --windowed --name Edupaie --clean --noconfirm --collect-all edupaie --collect-all PySide6 --add-data "edupaie/db/schema.sql;edupaie/db" --add-data "edupaie/edupaie.db;edupaie" --add-data "edupaie/db/create_model_db.py;edupaie/db" --add-data "README.md;." edupaie/main.py
if %errorlevel% neq 0 (
    echo [ERREUR] La construction a echoue.
    echo Verifiez les erreurs ci-dessus.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo [OK] Construction reussie !
echo ========================================================================
echo.
echo L'executable se trouve dans : dist\Edupaie.exe
echo.
echo Pour tester l'executable :
echo   cd dist
echo   Edupaie.exe
echo.
echo Pour distribuer l'executable :
echo   - Copiez uniquement dist\Edupaie.exe
echo   - Le dossier build peut etre supprime
echo.

pause
