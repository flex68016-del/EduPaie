# =============================================================================
# create_model_db.py - Création de la base de données modèle pour l'exécutable
# =============================================================================
# Rôle : Crée une base de données avec données de test dans le dossier du projet
# pour l'embarquer dans l'exécutable PyInstaller.
# =============================================================================
# Pourquoi ce script : La base de données modèle doit être créée dans le dossier
# du projet (pas dans user_data_dir) pour être embarquée dans l'exécutable PyInstaller.
# L'exécutable copiera ensuite cette base vers user_data_dir au premier lancement.
# =============================================================================

import sqlite3
from pathlib import Path


def create_model_database() -> None:
    """
    Crée une base de données modèle avec données de test dans le dossier du projet.
    
    Cette base sera embarquée dans l'exécutable PyInstaller et copiée vers
    user_data_dir au premier lancement par initialize_database().
    
    Pourquoi db/edupaie.db : Emplacement dans le dossier du projet pour être
    inclus par PyInstaller via le fichier .spec.
    """
    # Chemin vers la base de données modèle (dans le dossier du projet)
    db_path = Path(__file__).parent.parent / "edupaie.db"
    
    # Suppression de la base existante si elle existe
    # Pourquoi : Garantit une base propre et cohérente
    if db_path.exists():
        db_path.unlink()
    
    # Création de la base de données
    # Pourquoi : Crée une nouvelle base vide
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Lecture et exécution du schéma SQL
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = f.read()
        cursor.executescript(schema)
    
    # Insertion des données de test
    # Classes
    classes = [
        ("6ème A",), ("6ème B",), ("5ème A",), ("5ème B",), ("4ème A",), ("3ème B",)
    ]
    cursor.executemany("INSERT INTO classe (nom) VALUES (?)", classes)
    
    # Élèves
    eleves = [
        ("Dupont", "Jean", 1, "2024-2025", 50000),
        ("Martin", "Marie", 1, "2024-2025", 50000),
        ("Bernard", "Pierre", 1, "2024-2025", 50000),
        ("Dubois", "Sophie", 2, "2024-2025", 45000),
        ("Thomas", "Lucas", 2, "2024-2025", 45000),
        ("Robert", "Emma", 2, "2024-2025", 45000),
        ("Richard", "Louis", 3, "2024-2025", 60000),
        ("Petit", "Chloe", 3, "2024-2025", 60000),
        ("Leroy", "Hugo", 3, "2024-2025", 60000),
        ("Moreau", "Camille", 4, "2024-2025", 55000),
        ("Simon", "Nathan", 4, "2024-2025", 55000),
        ("Laurent", "Lola", 4, "2024-2025", 55000),
        ("Lefebvre", "Theo", 5, "2024-2025", 70000),
        ("Garcia", "Enzo", 5, "2024-2025", 70000),
        ("David", "Lea", 5, "2024-2025", 70000),
        ("Bertrand", "Antoine", 6, "2024-2025", 65000),
        ("Roux", "Manon", 6, "2024-2025", 65000),
        ("Vincent", "Mathis", 6, "2024-2025", 65000),
    ]
    cursor.executemany(
        "INSERT INTO eleve (nom, prenom, classe_id, annee_scolaire, total_du) VALUES (?, ?, ?, ?, ?)",
        eleves
    )
    
    # Paiements (numéros de reçu séquentiels pour 2024)
    paiements = [
        # Élève 1 (Dupont Jean) - Soldé
        (1, 50000, "2024-01-15", "especes", "REC-2024-000001", 0),
        # Élève 2 (Martin Marie) - Soldé
        (2, 50000, "2024-02-20", "cheque", "REC-2024-000002", 0),
        # Élève 3 (Bernard Pierre) - Partiel
        (3, 20000, "2024-03-10", "virement", "REC-2024-000003", 30000),
        # Élève 4 (Dubois Sophie) - Non payé
        # Aucun paiement
        # Élève 5 (Thomas Lucas) - Soldé
        (5, 45000, "2024-01-25", "mobile_money", "REC-2024-000004", 0),
        # Élève 6 (Robert Emma) - Partiel
        (6, 15000, "2024-04-05", "especes", "REC-2024-000005", 30000),
        # Élève 7 (Richard Louis) - Soldé
        (7, 60000, "2024-02-10", "virement", "REC-2024-000006", 0),
        # Élève 8 (Petit Chloe) - Partiel
        (8, 30000, "2024-03-15", "cheque", "REC-2024-000007", 30000),
        # Élève 9 (Leroy Hugo) - Non payé
        # Aucun paiement
        # Élève 10 (Moreau Camille) - Soldé
        (10, 55000, "2024-01-20", "especes", "REC-2024-000008", 0),
        # Élève 11 (Simon Nathan) - Partiel
        (11, 20000, "2024-04-12", "mobile_money", "REC-2024-000009", 35000),
        # Élève 12 (Laurent Lola) - Non payé
        # Aucun paiement
        # Élève 13 (Lefebvre Theo) - Soldé
        (13, 70000, "2024-02-15", "virement", "REC-2024-000010", 0),
        # Élève 14 (Garcia Enzo) - Partiel
        (14, 35000, "2024-03-20", "especes", "REC-2024-000011", 35000),
        # Élève 15 (David Lea) - Non payé
        # Aucun paiement
        # Élève 16 (Bertrand Antoine) - Soldé
        (16, 65000, "2024-01-30", "cheque", "REC-2024-000012", 0),
        # Élève 17 (Roux Manon) - Partiel
        (17, 25000, "2024-04-08", "mobile_money", "REC-2024-000013", 40000),
        # Élève 18 (Vincent Mathis) - Non payé
        # Aucun paiement
    ]
    cursor.executemany(
        "INSERT INTO paiement (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres) VALUES (?, ?, ?, ?, ?, ?)",
        paiements
    )
    
    # Validation des données
    conn.commit()
    
    # Vérification
    print(f"Base de données modèle créée : {db_path}")
    print(f"  - Classes : {cursor.execute('SELECT COUNT(*) FROM classe').fetchone()[0]}")
    print(f"  - Élèves : {cursor.execute('SELECT COUNT(*) FROM eleve').fetchone()[0]}")
    print(f"  - Paiements : {cursor.execute('SELECT COUNT(*) FROM paiement').fetchone()[0]}")
    
    conn.close()


if __name__ == "__main__":
    create_model_database()
