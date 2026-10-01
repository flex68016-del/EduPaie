# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
# edupaie.spec - Configuration PyInstaller optimisée pour EduPaie
# =============================================================================
# Pourquoi cette configuration :
# - Réduit la taille de l'exécutable en excluant les modules PySide6 inutiles
# - Garde uniquement les fonctionnalités nécessaires (Widgets, Svg, Pdf, PrintSupport)
# - Filtre les plugins et DLL inutiles
# - Optimisation bytecode avec optimize=2
# =============================================================================
# Pourquoi ces exclusions :
# - WebEngine, QML, 3D, Multimedia : non utilisés par EduPaie
# - Charts, DataVisualization, Bluetooth : non utilisés
# - Sql : EduPaie utilise sqlite3 standard (pas QtSql)
# - Test, pytest : non nécessaires en production
# - unittest : gardé car fpdf2 en a besoin (fpdf/sign.py)
# - tkinter, numpy, pandas, matplotlib : non utilisés
# =============================================================================

from PyInstaller.utils.hooks import collect_all

# Données à inclure (schéma, base modèle, assets)
datas = [
    ('edupaie/db/schema.sql', 'edupaie/db'),
    ('edupaie/edupaie.db', 'edupaie'),
    ('edupaie/db/create_model_db.py', 'edupaie/db'),
    ('edupaie/assets', 'edupaie/assets'),
    ('README.md', '.')
]
binaries = []
hiddenimports = []

# Collecter le module edupaie
tmp_ret = collect_all('edupaie')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Collecter PySide6 avec collect_all (revient à l'approche originale)
# Pourquoi collect_all : Garantit que tous les plugins et dépendances nécessaires sont inclus
# collect_submodules ne collecte pas les plugins nécessaires (imageformats, platforms, etc.)
tmp_ret = collect_all('PySide6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Filtrer les données pour exclure les éléments inutiles
# Pourquoi qml, include, metatypes : Non utilisés par EduPaie (pas de QML)
# Pourquoi translations : Non nécessaires (interface uniquement en français)
def filter_datas(datas):
    """Filtre les données inutiles pour réduire la taille."""
    patterns_to_exclude = [
        'PySide6/qml',  # EduPaie n'utilise pas QML
        'PySide6/include',  # Headers non nécessaires en production
        'translations',  # Non nécessaires (interface uniquement en français)
    ]
    filtered = []
    for data in datas:
        exclude = False
        for pattern in patterns_to_exclude:
            if pattern.lower() in str(data[0]).lower():
                exclude = True
                break
        if not exclude:
            filtered.append(data)
    return filtered

datas = filter_datas(datas)


a = Analysis(
    ['edupaie/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclusion des modules PySide6 inutiles pour réduire la taille
    # Pourquoi WebEngine, QML, 3D, Multimedia : Non utilisés par EduPaie
    # Pourquoi Charts, DataVisualization, Bluetooth : Non utilisés
    # Pourquoi Sql : EduPaie utilise sqlite3 standard (pas QtSql)
    # Pourquoi Test, Designer, Help : Non nécessaires en production
    excludes=[
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuickWidgets",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtBluetooth",
        "PySide6.QtSql",
        "PySide6.QtTest",
        "PySide6.QtDesigner",
        "PySide6.QtHelp",
        "PySide6.QtNfc",
        "PySide6.QtScxml",
        "PySide6.QtSerialPort",
        "PySide6.QtSerialBus",
        "PySide6.QtSensors",
        "PySide6.QtSpatialAudio",
        "PySide6.QtRemoteObjects",
        "PySide6.QtTextToSpeech",
        "PySide6.QtUiTools",
        "PySide6.QtAxContainer",
        "PySide6.QtAxServer",
        "PySide6.QtGraphs",
        "PySide6.QtGraphsWidgets",
        "PySide6.QtLocation",
        "PySide6.QtPositioning",
        "PySide6.QtNetworkAuth",
        "PySide6.QtOpc",
        "PySide6.QtHttpServer",
        "PySide6.QtWebSockets",
        "PySide6.QtWebChannel",
        "PySide6.QtWebView",
        "PySide6.QtXml",
        # Modules Python standard inutiles
        "tkinter",
        "numpy",
        "pandas",
        "matplotlib",
        "scipy",
        # "unittest",  # Gardé : fpdf2 en a besoin pour fpdf/sign.py
        "pytest",
        "pydoc",
        "doctest",
        "test",
    ],
    noarchive=False,
    optimize=2,  # Optimisation bytecode (sans docstrings) pour réduire la taille
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Edupaie',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Windows : strip peut causer des problèmes avec certains antivirus
    upx=True,
    # UPX exclusions : vcruntime*.dll, Qt6Core.dll, python3*.dll, qwindows.dll
    # Pourquoi ces exclusions : Évite les faux positifs antivirus et les crashs au démarrage
    upx_exclude=[
        'vcruntime*.dll',
        'msvcp*.dll',
        'api-ms-win-crt*.dll',
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'python3*.dll',
        'qwindows.dll',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='edupaie/assets/edupaie-icon.ico'
)
