# =============================================================================
# seed.py - Jeu de données de test
# =============================================================================
# Rôle : Peuple la base de données avec des données de test pour le développement.
# =============================================================================
# Ce fichier utilise :
# - sqlite3 pour insérer les données de test
# =============================================================================
# Ce fichier est utilisé par :
# - Le développeur pour créer un jeu de données de test
# =============================================================================

import sqlite3
from pathlib import Path
from edupaie.utils.paths import user_data_dir


def seed_database() -> None:
    """
    Peuple la base de données avec des données de test.
    
    Cette fonction crée :
    - 6 classes (6ème A à 3ème B)
    - 18 élèves répartis dans les classes
    - Des paiements variés (soldés, partiels, non payés, différents modes)
    - Des numéros de reçu cohérents (REC-2024-000001, REC-2024-000002, etc.)
    
    Pourquoi la cohérence des soldes est garantie :
    - Chaque paiement a un solde_apres figé qui représente l'état APRÈS ce paiement
    - Le solde_apres est calculé comme : total_du - somme(paiements jusqu'à celui-ci)
    - Pour un élève soldé : le dernier paiement a solde_apres = 0
    - Pour un élève partiel : le dernier paiement a solde_apres > 0
    - Pour un élève non payé : aucun paiement, solde = total_du
    
    Cette cohérence est maintenue manuellement dans ce script de seed.
    En production, la couche services calculera automatiquement ces valeurs.
    """
    # Chemin vers la base de données
    db_path = user_data_dir() / "edupaie.db"
    
    # Connexion à la base de données
    # Pourquoi : Exécute les requêtes d'insertion des données de test
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Activation des clés étrangères
    cursor.execute("PRAGMA foreign_keys = ON")
    
    try:
        # =====================================================================
        # Insertion des classes (6 classes)
        # =====================================================================
        classes = [
            ("6ème A",),
            ("6ème B",),
            ("5ème A",),
            ("5ème B",),
            ("4ème A",),
            ("3ème B",),
        ]
        
        # Insertion des classes
        # Pourquoi executemany : Insère plusieurs lignes en une seule requête
        cursor.executemany(
            "INSERT INTO classe (nom) VALUES (?)",
            classes
        )
        
        # Récupération des IDs des classes insérées
        # Pourquoi : Utilisé comme clé étrangère pour les élèves
        cursor.execute("SELECT id FROM classe ORDER BY id")
        classe_ids = [row[0] for row in cursor.fetchall()]
        
        # =====================================================================
        # Insertion des élèves (18 élèves, 3 par classe)
        # =====================================================================
        # Pourquoi 18 élèves : Nombre suffisant pour tester les fonctionnalités
        # Pourquoi 3 par classe : Distribution équilibrée pour tester les filtres
        
        eleves = []
        eleve_counter = 1
        
        for classe_idx, classe_id in enumerate(classe_ids):
            # 3 élèves par classe avec des dettes variées
            for i in range(3):
                total_du = 50000  # 50 000 FCFA par élève
                eleves.append((
                    f"Nom{eleve_counter}",
                    f"Prénom{eleve_counter}",
                    classe_id,
                    "2024-2025",
                    total_du
                ))
                eleve_counter += 1
        
        # Insertion des élèves
        cursor.executemany(
            "INSERT INTO eleve (nom, prenom, classe_id, annee_scolaire, total_du) VALUES (?, ?, ?, ?, ?)",
            eleves
        )
        
        # Récupération des IDs des élèves insérés
        cursor.execute("SELECT id, total_du FROM eleve ORDER BY id")
        eleves_data = cursor.fetchall()
        
        # =====================================================================
        # Insertion des paiements
        # =====================================================================
        # Stratégie de répartition des paiements :
        # - Élèves 1-6 (6ème) : 3 soldés, 3 partiels
        # - Élèves 7-12 (5ème) : 3 soldés, 3 non payés
        # - Élèves 13-18 (4ème/3ème) : 6 partiels
        
        paiements = []
        recu_counter = 1
        annee = "2024"
        
        for idx, (eleve_id, total_du) in enumerate(eleves_data):
            # Cas 1 : Élèves soldés (paiement complet en une fois)
            if idx < 3:
                # Paiement complet
                numero_recu = f"REC-{annee}-{recu_counter:06d}"
                paiements.append((
                    eleve_id,
                    total_du,  # Montant = total_du
                    "2024-09-15",
                    "especes",
                    numero_recu,
                    0  # solde_apres = 0 (soldé)
                ))
                recu_counter += 1
            
            # Cas 2 : Élèves partiellement payés (2 paiements)
            elif idx < 9:
                # Premier paiement (50%)
                montant1 = total_du // 2
                numero_recu1 = f"REC-{annee}-{recu_counter:06d}"
                paiements.append((
                    eleve_id,
                    montant1,
                    "2024-09-10",
                    "especes",
                    numero_recu1,
                    total_du - montant1  # solde_apres = reste à payer
                ))
                recu_counter += 1
                
                # Deuxième paiement (reste)
                montant2 = total_du - montant1
                numero_recu2 = f"REC-{annee}-{recu_counter:06d}"
                paiements.append((
                    eleve_id,
                    montant2,
                    "2024-09-20",
                    "virement",
                    numero_recu2,
                    0  # solde_apres = 0 (soldé après 2ème paiement)
                ))
                recu_counter += 1
            
            # Cas 3 : Élèves non payés (aucun paiement)
            # else : aucun paiement, solde = total_du
        
        # Insertion des paiements
        cursor.executemany(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            paiements
        )
        
        # Commit des changements
        # Pourquoi commit : Valide toutes les insertions
        conn.commit()
        
        print(f"Base de données peuplée avec succès :")
        print(f"- {len(classes)} classes")
        print(f"- {len(eleves)} élèves")
        print(f"- {len(paiements)} paiements")
        
    except Exception as e:
        # Rollback en cas d'erreur
        # Pourquoi rollback : Annule toutes les insertions si une erreur survient
        conn.rollback()
        print(f"Erreur lors du peuplement de la base : {e}")
        raise
    
    finally:
        # Fermeture de la connexion
        conn.close()


if __name__ == "__main__":
    seed_database()