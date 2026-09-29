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
