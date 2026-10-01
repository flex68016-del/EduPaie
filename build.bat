@echo off
REM =============================================================================
REM build.bat - Script de construction de l'exécutable EduPaie avec PyInstaller
REM =============================================================================
REM Rôle : Automatise la construction de l'exécutable Windows autonome.
REM =============================================================================
REM Pourquoi ce script : Simplifie la construction de l'exécutable en une seule
REM commande, évite d'oublier des options PyInstaller importantes.
REM Pourquoi .venv-build : Environnement de build propre pour réduire la taille
REM de l'exécutable (pas de dépendances inutiles du Python global).
REM =============================================================================
REM
REM Prérequis :
REM - Python 3.10+ installé
REM - Le script crée automatiquement .venv-build si nécessaire
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

REM Création du venv de build s'il n'existe pas
REM Pourquoi .venv-build : Environnement isolé pour éviter les dépendances inutiles
REM Pourquoi --clear : Crée un venv propre pour assurer la reproductibilité
if not exist ".venv-build" (
    echo Creation de l'environnement de build (.venv-build)...
    python -m venv .venv-build
    if %errorlevel% neq 0 (
        echo [ERREUR] Impossible de creer le venv.
        pause
        exit /b 1
    )
    echo [OK] Environnement de build cree.
    echo.
)

REM Installation des dépendances dans le venv de build
REM Pourquoi PySide6 et non PySide6-Essentials : QtPdf/QtPdfWidgets nécessaires pour l'aperçu
REM Pourquoi fpdf2 : Génération des reçus PDF
REM Pourquoi pyinstaller : Construction de l'exécutable
echo Installation des dependances dans .venv-build...
"%~dp0.venv-build\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%~dp0.venv-build\Scripts\python.exe" -m pip install PySide6 fpdf2 pyinstaller --quiet
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible d'installer les dependances.
    pause
    exit /b 1
)

echo [OK] Dependances installees.
echo.

REM Vérification de l'existence du fichier de spec
REM Pourquoi : Le fichier .spec contient toute la configuration PyInstaller
if not exist "edupaie.spec" (
    echo [ERREUR] Le fichier edupaie.spec n'existe pas.
    echo Le fichier .spec est necessaire pour construire l'executable.
    pause
    exit /b 1
)

echo [OK] Fichier edupaie.spec trouve.
echo.

REM Construction de l'exécutable avec PyInstaller
REM Pourquoi edupaie.spec : Utilise la configuration optimisée avec exclusions
REM Pourquoi --clean : Nettoie le dossier de construction avant reconstruction
REM Pourquoi --noconfirm : Confirme automatiquement le remplacement des fichiers
REM Pourquoi .venv-build : Utilise l'environnement de build propre
echo Construction de l'executable...
"%~dp0.venv-build\Scripts\python.exe" -m PyInstaller --clean --noconfirm edupaie.spec
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

REM Construction de l'installateur Inno Setup si disponible
echo Verification de l'installateur Inno Setup...
where iscc >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo Construction de l'installateur Inno Setup...
    if exist "installer\edupaie.iss" (
        iscc "installer\edupaie.iss"
        if %errorlevel% equ 0 (
            echo [OK] Installateur cree dans installer/
        ) else (
            echo [AVERTIS] Echec de la creation de l'installateur.
        )
    ) else (
        echo [AVERTIS] Fichier installer\edupaie.iss non trouve.
    )
) else (
    echo [INFO] Inno Setup non installe. L'installateur ne sera pas cree.
    echo Pour installer Inno Setup : https://jrsoftware.org/isdl.php
)

echo.
pause
