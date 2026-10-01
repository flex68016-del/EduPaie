# EduPaie

Application desktop de gestion des paiements scolaires pour établissements scolaires d'Afrique de l'Ouest.

## Fonctionnalités

- **Gestion des élèves** : Ajout, modification, suppression, recherche, filtrage par classe
- **Gestion des classes** : Création de nouvelles classes
- **Enregistrement des paiements** : Paiements avec numérotation automatique de reçus
- **Calcul automatique du solde** : Solde calculé automatiquement à chaque paiement
- **Statuts de paiement** : Soldé (vert), Partiellement payé (orange), Non payé (rouge)
- **Historique des paiements** : Historique complet avec réimpression de reçus
- **Génération de reçus PDF** : Reçus professionnels générés automatiquement
- **Aperçu des reçus** : Aperçu PDF intégré, enregistrement et impression
- **Tableau de bord** : Vue d'ensemble avec KPI, jauge circulaire et derniers paiements
- **Interface premium** : Design moderne inspiré de Stripe, Linear et Notion

## Installation pour le développement

### Prérequis

- Python 3.10 ou supérieur
- Git (optionnel)

### Étapes

1. Cloner le dépôt :
```bash
git clone https://github.com/flex68016-del/EduPaie.git
cd EduPaie
```

2. Créer un environnement virtuel Python :
```bash
python -m venv venv
```

3. Activer l'environnement virtuel :
- Windows : `venv\Scripts\activate`
- Linux/Mac : `source venv/bin/activate`

4. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Lancement

### En développement

Depuis le répertoire racine du projet avec l'environnement virtuel activé :

```bash
python edupaie/main.py
```

Ou directement avec l'exécutable Python du venv :

```bash
venv\Scripts\python.exe edupaie/main.py
```

### Exécutable Windows

1. Téléchargez `Edupaie.exe` depuis le dépôt GitHub
2. Placez-le dans le dossier de votre choix
3. Double-cliquez pour lancer

Au premier lancement, l'application crée automatiquement le dossier de données dans `%APPDATA%\EduPaie`.

## Tests

Exécuter la suite de tests :

```bash
pytest
```

La suite de tests couvre :
- Gestion des élèves (CRUD, validations)
- Enregistrement des paiements
- Calcul du solde et statuts
- Historique des paiements
- Génération de reçus PDF
- Tableau de bord

## Construction de l'exécutable

Pour construire l'exécutable Windows :

```bash
build.bat
```

L'exécutable sera créé dans `dist/Edupaie.exe` (environ 237 Mo).

### Création de l'installateur Windows

Pour créer un installateur Windows standard (.exe d'installation), vous devez :

1. **Installer Inno Setup** : https://jrsoftware.org/isdl.php
2. **Relancer le build** :
   ```bash
   build.bat
   ```

Si Inno Setup est installé, le script créera automatiquement l'installateur dans `installer/output/`. L'installateur inclut :
- Installation dans `Program Files\EduPaie`
- Raccourcis (Menu Démarrer + Bureau)
- Icône de l'application
- Conservation des données utilisateur dans `%APPDATA%\EduPaie`

## Architecture

Le projet suit une architecture en 3 couches stricte :

- **data/** : Couche d'accès aux données (Repository/DAO, SQL écrit à la main)
  - `database.py` : Gestion de la connexion et initialisation du schéma
  - `student_repository.py` : Opérations CRUD sur les élèves
  - `payment_repository.py` : Opérations CRUD sur les paiements

- **services/** : Couche logique métier (solde, validations, numéros de reçu)
  - `student_service.py` : Logique métier pour les élèves
  - `payment_service.py` : Logique métier pour les paiements
  - `receipt_service.py` : Génération des reçus PDF
  - `dashboard_service.py` : Calcul des statistiques
  - `exceptions.py` : Exceptions métier personnalisées

- **ui/** : Couche interface utilisateur (PySide6)
  - `main_window.py` : Fenêtre principale avec navigation
  - `students_view.py` : Liste des élèves avec recherche et filtres
  - `student_form.py` : Formulaire d'ajout/modification d'élève
  - `student_detail.py` : Fiche détaillée d'un élève
  - `payment_dialog.py` : Dialogue d'enregistrement de paiement
  - `dashboard.py` : Tableau de bord avec KPI
  - `error_handler.py` : Gestion globale des erreurs

- **utils/** : Utilitaires
  - `paths.py` : Gestion des chemins (ressources PyInstaller, données utilisateur)

- **db/** : Schéma de base de données et données de test
  - `schema.sql` : Schéma SQL de la base
  - `seed.py` : Peuplement de la base avec des données de test
  - `create_model_db.py` : Création de la base modèle pour PyInstaller

- **tests/** : Tests unitaires avec pytest
  - `test_students.py` : Tests de gestion des élèves
  - `test_payments.py` : Tests d'enregistrement des paiements
  - `test_solde.py` : Tests de calcul du solde
  - `test_historique.py` : Tests de l'historique
  - `test_recu.py` : Tests de génération de reçus
  - `test_dashboard.py` : Tests du tableau de bord

## Stack Technique

- **Python 3.10+** : Langage principal
- **PySide6 (Qt6)** : Framework d'interface desktop
- **SQLite** : Base de données (module standard sqlite3)
- **fpdf2** : Génération de PDF
- **pytest** : Framework de tests
- **PyInstaller** : Packaging Windows

## Choix techniques

### Pourquoi SQLite et pas d'ORM ?

- SQLite est inclus dans la bibliothèque standard Python
- Pas de dépendance externe pour la base de données
- SQL écrit à la main pour un contrôle total et de la performance
- Parfait pour une application desktop mono-utilisateur

### Pourquoi les montants en entiers (FCFA) ?

- Évite les erreurs d'arrondi des nombres flottants
- Le franc CFA n'a pas de sous-unités (cents)
- Calculs exacts pour les montants monétaires

### Pourquoi l'architecture en 3 couches ?

- Séparation claire des responsabilités
- Facilite les tests (mock des repositories)
- Maintenance améliorée
- UI peut être modifiée sans impacter la logique métier

## Workflow de Développement

Le projet suit un workflow Git strict :

1. **Branches de développement** : Une branche par fonctionnalité
   - `feature/<nom>` : Nouvelles fonctionnalités
   - `fix/<nom>` : Corrections de bugs
   - `build/<nom>` : Configuration et packaging

2. **Commits fréquents** : Commits atomiques et significatifs

3. **Fusion avec --no-ff** : Pour conserver l'historique des branches
   ```bash
   git checkout main
   git merge --no-ff feature/<nom>
   ```

4. **Tags de version** : Pour chaque version livrable
   ```bash
   git tag v0.x-<nom>
   git push origin v0.x-<nom>
   ```

## Structure du projet

```
EduPaie/
├── edupaie/              # Package principal
│   ├── ui/              # Interface utilisateur (PySide6)
│   ├── services/        # Logique métier
│   ├── data/            # Accès aux données (SQLite)
│   ├── utils/           # Utilitaires
│   ├── db/              # Schéma et seed
│   ├── tests/           # Tests pytest
│   └── main.py          # Point d'entrée
├── docs/                # Documentation
├── dist/                # Exécutable construit
├── edupaie.spec         # Configuration PyInstaller
├── build.bat            # Script de build Windows
├── requirements.txt     # Dépendances Python
└── README.md            # Ce fichier
```

## Versions

- **v0.1-fondations** : Structure du projet, base de données, interface de base
- **v0.2-eleves** : Gestion complète des élèves (CRUD, recherche, filtre)
- **v0.3-solde** : Calcul automatique du solde et statuts de paiement
- **v0.4-paiement** : Enregistrement des paiements avec numérotation de reçus
- **v0.5-historique** : Historique des paiements par élève
- **v0.6-recu** : Génération et impression de reçus PDF
- **v0.7-dashboard** : Tableau de bord avec KPI
- **v0.8-exe** : Packaging Windows (exécutable autonome)
- **v0.8.1-fix** : Correction des erreurs de syntaxe
- **v0.8.2-fix2** : Correction des erreurs d'exécution (slots Qt, couleurs)
- **v0.8.3-fix3** : Correction du slot montant et noms réalistes
- **v0.9-apercu** : Aperçu PDF intégré, enregistrement et impression
- **v0.10-design** : Refonte visuelle premium (inspiré de Stripe, Linear, Notion)
- **v0.11-design** : Refonte visuelle complète + création de classes + derniers paiements
- **v0.12-exe-leger** : Optimisation de l'exécutable (237 Mo, -22 Mo)

## Documentation

Documentation détaillée disponible dans le dossier `docs/` :

- `modelisation.md` : MCD/MLD et choix de modélisation
- `documentation.md` : Architecture technique et choix justifiés
- `manuel_utilisateur.md` : Guide d'utilisation
- `guide_installation.md` : Guide d'installation
- `soutenance.md` : Plan de démo et questions/réponses probables

## Données utilisateur

Les données utilisateur sont stockées dans :
- **Windows** : `%APPDATA%\EduPaie\`
- **Linux** : `~/.config/EduPaie/`
- **macOS** : `~/Library/Application Support/EduPaie/`

Ce dossier contient :
- `edupaie.db` : Base de données SQLite
- `edupaie.log` : Fichier de log
- `receipts/` : Reçus PDF générés

## Licence

Ce projet est développé à des fins éducatives et de démonstration.
