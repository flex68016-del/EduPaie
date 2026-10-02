# Guide d'installation EduPaie

## Installation de l'exécutable

### Prérequis

- Windows 10 ou Windows 11
- Aucune installation de Python requise

### Installation

1. Téléchargez le fichier `Edupaie.exe` depuis le dépôt GitHub
2. Placez le fichier dans le dossier de votre choix (ex: `C:\Program Files\EduPaie\`)
3. Créez un raccourci sur le bureau si nécessaire
4. Lancez l'application en double-cliquant sur `Edupaie.exe`

### Premier lancement

Au premier lancement, l'application :
- Crée automatiquement le dossier de données dans `%APPDATA%\EduPaie`
- Copie la base de données modèle dans ce dossier
- Initialise le fichier de log `edupaie_errors.log`

### Taille de l'exécutable

- **Version optimisée** : ~237 Mo (v0.12-exe-leger)
- **Réduction** : -22 Mo (-8.5%) par rapport à la version originale (259 Mo)

Note : La taille reste importante car PySide6 complet est nécessaire pour les fonctionnalités d'aperçu PDF (QtPdf, QtPdfWidgets). L'installateur Inno Setup peut être utilisé pour une distribution compressée (~30-40 Mo).

### Interface utilisateur

L'interface utilise un design premium inspiré de Stripe, Linear et Notion :
- Palette de couleurs claire forcée (indépendante du thème Windows)
- Typographie Inter ou Segoe UI
- Cartes avec ombres douces et rayons premium
- Navigation par barre latérale avec transitions fluides
- Tableau de bord avec KPI, jauge circulaire et derniers paiements

### Emplacement des données

Les données utilisateur sont stockées dans :
```
%APPDATA%\EduPaie\
├── edupaie.db           # Base de données (élèves, paiements)
├── edupaie.log          # Fichier de log
└── receipts/            # Reçus PDF générés
```

Pour accéder à ce dossier :
1. Appuyez sur `Win + R`
2. Tapez `%APPDATA%` et appuyez sur Entrée
3. Naviguez vers le dossier `EduPaie`

### Sauvegarde des données

Pour sauvegarder vos données :
1. Copiez le dossier `%APPDATA%\EduPaie`
2. Collez-le dans un emplacement de sauvegarde (ex: clé USB, cloud)

### Restauration des données

Pour restaurer vos données :
1. Fermez EduPaie
2. Copiez le dossier sauvegardé dans `%APPDATA%\EduPaie`
3. Relancez EduPaie

## Installation pour le développement

### Prérequis

- Python 3.10 ou supérieur
- Git (optionnel, pour cloner le dépôt)

### Installation du code source

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/flex68016-del/EduPaie.git
   cd EduPaie
   ```

2. Créez un environnement virtuel :
   ```bash
   python -m venv venv
   ```

3. Activez l'environnement virtuel :
   - Windows : `venv\Scripts\activate`
   - Linux/Mac : `source venv/bin/activate`

4. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

### Lancer l'application en développement

```bash
python edupaie/main.py
```

### Exécuter les tests

```bash
pytest
```

### Construire l'exécutable

```bash
build.bat
```

L'exécutable sera créé dans le dossier `dist/Edupaie.exe` (environ 237 Mo).

### Créer l'installateur Windows

Pour créer un installateur Windows standard (.exe d'installation) :

1. **Installer Inno Setup** : https://jrsoftware.org/isdl.php
2. **Relancer le build** :
   ```bash
   build.bat
   ```

Si Inno Setup est installé, le script créera automatiquement l'installateur dans `installer/installer/Edupaie-Setup.exe` (environ 235 Mo).

L'installateur inclut :
- Installation dans `Program Files\EduPaie`
- Raccourcis (Menu Démarrer + Bureau)
- Icône de l'application
- Conservation des données utilisateur dans `%APPDATA%\EduPaie`
- Assistant d'installation Windows standard

### Distribution

Pour distribuer l'application, vous avez deux options :

1. **Installateur complet** (recommandé) : `installer/installer/Edupaie-Setup.exe` (235 Mo)
   - Assistant d'installation guidé
   - Création automatique des raccourcis
   - Désinstallation propre via le Panneau de configuration

2. **Exécutable autonome** : `dist/Edupaie.exe` (237 Mo)
   - À copier directement dans le dossier de l'utilisateur
   - Pas d'installation requise
   - Les données seront créées dans `%APPDATA%\EduPaie` au premier lancement

## Structure du projet

```
EduPaie/
├── edupaie/              # Package principal
│   ├── ui/              # Interface utilisateur (PySide6)
│   ├── services/        # Logique métier
│   ├── data/            # Accès aux données (SQLite)
│   ├── utils/           # Utilitaires
│   ├── db/              # Schéma et seed
│   ├── tests/           # Tests unitaires
│   └── main.py          # Point d'entrée
├── docs/                # Documentation
├── dist/                # Exécutable construit
├── installer/           # Scripts et output de l'installateur
│   ├── edupaie.iss      # Script Inno Setup
│   └── installer/       # Installateur final (Edupaie-Setup.exe)
├── edupaie.spec         # Configuration PyInstaller
├── build.bat            # Script de build Windows
├── requirements.txt     # Dépendances Python
└── README.md            # Documentation du projet
```

## Dépendances

```
PySide6==6.8.0
fpdf2==2.7.7
pytest==8.3.4
```

## Dépannage

### L'application ne se lance pas

1. Vérifiez que Windows Defender ne bloque pas l'exécutable
2. Essayez de lancer en tant qu'administrateur
3. Consultez le fichier `edupaie_errors.log` dans `%APPDATA%\EduPaie`

### Erreur de base de données

1. Supprimez le dossier `%APPDATA%\EduPaie`
2. Relancez l'application (la base sera recréée automatiquement)

### Reçu PDF ne s'ouvre pas

1. Vérifiez que vous avez un visualiseur PDF installé (Adobe Reader, etc.)
2. Vérifiez les permissions du dossier `%APPDATA%\EduPaie\receipts`
