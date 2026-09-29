# EduPaie

Application desktop de gestion des paiements scolaires.

## Installation

1. Créer un environnement virtuel Python :
```bash
python -m venv venv
```

2. Activer l'environnement virtuel :
- Windows : `venv\Scripts\activate`
- Linux/Mac : `source venv/bin/activate`

3. Installer les dépendances :
```bash
pip install -r edupaie/requirements.txt
```

## Lancement

Depuis le répertoire racine du projet :

```bash
python edupaie/main.py
```

Ou avec l'environnement virtuel activé :

```bash
venv/Scripts/python.exe edupaie/main.py
```

## Architecture

- `data/` : Couche d'accès aux données (Repository/DAO, SQL)
- `services/` : Couche logique métier (solde, validations, numéros de reçu)
- `ui/` : Couche interface utilisateur (PySide6)
- `utils/` : Utilitaires (chemins de ressources)
- `db/` : Schéma de base de données et données de test

## Stack Technique

- Python 3.10+
- PySide6 (Qt6) pour l'interface desktop
- SQLite pour la base de données
- fpdf2 pour la génération de PDF
- pytest pour les tests

## Workflow de Développement

Le projet suit un workflow Git strict :
- `main` contient toujours une version qui fonctionne
- Une branche par fonctionnalité (feature/<nom>)
- Commits fréquents et significatifs
- Fusion avec `--no-ff` pour conserver l'historique
- Tags pour chaque version (v0.1-fondations, v0.2-eleves, etc.)

## Versions

- v0.1-fondations : Structure du projet, base de données, interface de base
- v0.2-eleves : Gestion complète des élèves (CRUD, recherche, filtre)
