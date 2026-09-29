# =============================================================================
# payment_repository.py - Repository pour les paiements
# =============================================================================
# Rôle : Fournit les opérations de lecture et d'écriture pour les paiements.
# =============================================================================
# Ce fichier utilise :
# - data.database.Database pour la connexion à la base de données
# - sqlite3 pour l'exécution des requêtes SQL
# =============================================================================
# Ce fichier est utilisé par :
# - services.student_service pour le calcul du solde et du statut
# - services.payment_service pour l'enregistrement des paiements
# =============================================================================

import sys
from pathlib import Path
from typing import Dict, Any

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/data/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from edupaie.data.database import Database


class PaymentRepository:
    """
    Repository pour la lecture des paiements (calcul du solde).
    
    Responsabilité : Fournir les opérations de lecture nécessaires pour calculer
    le solde d'un élève (total payé, nombre de paiements).
    
    Pourquoi un repository séparé : Sépare la logique d'accès aux données des paiements
    de celle des élèves, respectant le principe de responsabilité unique.
    
    Note : Ce repository est en lecture seule dans cette version. Les opérations
    d'écriture (create, update, delete) seront ajoutées dans la fonctionnalité
    d'enregistrement des paiements.
    """
    
    def __init__(self, database: Database) -> None:
        """
        Initialise le repository avec une connexion à la base de données.
        
        Args:
            database: Instance de la classe Database pour la connexion.
        """
        self.database = database
    
    def total_paye(self, eleve_id: int) -> int:
        """
        Calcule le total des paiements effectués par un élève.
        
        Args:
            eleve_id: Identifiant de l'élève
        
        Returns:
            Le montant total payé par l'élève (en FCFA, entier).
            Retourne 0 si l'élève n'a aucun paiement.
        
        Pourquoi COALESCE(SUM(montant), 0) : Si l'élève n'a aucun paiement,
        SUM(montant) retourne NULL. COALESCE remplace NULL par 0, ce qui
        évite des erreurs de calcul (NULL - total_du = NULL).
        
        Pourquoi SUM(montant) : Agrégation SQL qui additionne tous les montants
        des paiements de l'élève.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : somme des montants des paiements de l'élève
            # Pourquoi le paramètre "?" : Protection contre les injections SQL
            cursor.execute(
                """SELECT COALESCE(SUM(montant), 0) as total
                   FROM paiement
                   WHERE eleve_id = ?""",
                (eleve_id,)
            )
            
            result = cursor.fetchone()
            return result['total'] if result else 0
    
    def nombre_paiements(self, eleve_id: int) -> int:
        """
        Compte le nombre de paiements effectués par un élève.
        
        Args:
            eleve_id: Identifiant de l'élève
        
        Returns:
            Le nombre de paiements effectués par l'élève.
            Retourne 0 si l'élève n'a aucun paiement.
        
        Pourquoi COUNT(*) : Compte le nombre de lignes (paiements) correspondant
        à la condition WHERE eleve_id = ?.
        
        Pourquoi cette méthode : Permet de distinguer le cas "Non payé"
        (0 paiements) du cas "Partiellement payé" (au moins 1 paiement).
        """
        with self.database.transaction() as cursor:
            # Requête SQL : comptage des paiements de l'élève
            # Pourquoi le paramètre "?" : Protection contre les injections SQL
            cursor.execute(
                """SELECT COUNT(*) as nombre
                   FROM paiement
                   WHERE eleve_id = ?""",
                (eleve_id,)
            )
            
            result = cursor.fetchone()
            return result['nombre'] if result else 0
    
    def list_by_student(self, eleve_id: int) -> list:
        """
        Récupère la liste chronologique des paiements d'un élève.
        
        Args:
            eleve_id: Identifiant de l'élève
        
        Returns:
            Liste de dictionnaires contenant les informations des paiements.
            Chaque dictionnaire contient : id, montant, date_paiement, mode, numero_recu, solde_apres.
            La liste est triée par date croissante puis par ID croissant.
        
        Pourquoi cette méthode : Permet d'afficher l'historique chronologique
        des paiements dans l'ordre où ils ont été effectués.
        
        Pourquoi ORDER BY date_paiement ASC, id ASC : Trie d'abord par date (du plus
        ancien au plus récent) pour voir l'évolution chronologique, puis par ID pour
        garantir un ordre stable si plusieurs paiements ont été effectués le même jour.
        L'ID est incrémenté séquentiellement, donc trier par ID après la date garantit
        que les paiements du même jour sont dans l'ordre de création.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : sélection des paiements de l'élève triés chronologiquement
            # Pourquoi le paramètre "?" : Protection contre les injections SQL
            cursor.execute(
                """SELECT id, montant, date_paiement, mode, numero_recu, solde_apres
                   FROM paiement
                   WHERE eleve_id = ?
                   ORDER BY date_paiement ASC, id ASC""",
                (eleve_id,)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ===== Section : Opérations d'écriture =====
    
    def add(self, eleve_id: int, montant: int, date_paiement: str, 
            mode: str, numero_recu: str, solde_apres: int) -> int:
        """
        Ajoute un nouveau paiement dans la base de données.
        
        Args:
            eleve_id: Identifiant de l'élève
            montant: Montant du paiement (en FCFA, entier)
            date_paiement: Date du paiement (format ISO YYYY-MM-DD)
            mode: Mode de paiement ('especes', 'cheque', 'virement', 'mobile_money')
            numero_recu: Numéro unique du reçu (format REC-AAAA-NNNNNN)
            solde_apres: Solde après ce paiement (en FCFA, entier)
        
        Returns:
            L'identifiant du paiement créé.
        
        Raises:
            sqlite3.IntegrityError: Si le numéro de reçu existe déjà (UNIQUE constraint).
        
        Pourquoi le paramètre solde_apres : Le solde après paiement est calculé
        et figé au moment du paiement. Cela permet de suivre l'historique de l'évolution
        du solde et de détecter des erreurs de calcul si nécessaire.
        
        Pourquoi la contrainte UNIQUE sur numero_recu : Empêche d'avoir deux paiements
        avec le même numéro de reçu, ce qui serait une erreur administrative.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : insertion d'un nouveau paiement
            # Pourquoi les paramètres "?" : Protection contre les injections SQL
            cursor.execute(
                """INSERT INTO paiement 
                   (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
            )
            
            return cursor.lastrowid
    
    def get_by_id(self, paiement_id: int) -> Dict[str, Any]:
        """
        Récupère un paiement par son identifiant.
        
        Args:
            paiement_id: Identifiant du paiement
        
        Returns:
            Dictionnaire contenant les informations du paiement, ou None si non trouvé.
        
        Pourquoi cette méthode : Permet de récupérer les détails d'un paiement
        pour affichage ou vérification.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : sélection d'un paiement par son ID
            # Pourquoi le paramètre "?" : Protection contre les injections SQL
            cursor.execute(
                """SELECT id, eleve_id, montant, date_paiement, mode, numero_recu, solde_apres
                   FROM paiement
                   WHERE id = ?""",
                (paiement_id,)
            )
            
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_by_receipt_number(self, numero_recu: str) -> Dict[str, Any]:
        """
        Récupère un paiement par son numéro de reçu.
        
        Args:
            numero_recu: Numéro unique du reçu (format REC-AAAA-NNNNNN)
        
        Returns:
            Dictionnaire contenant les informations du paiement, ou None si non trouvé.
        
        Pourquoi cette méthode : Permet de vérifier si un numéro de reçu existe déjà
        avant de générer un nouveau numéro (évite les doublons).
        """
        with self.database.transaction() as cursor:
            # Requête SQL : sélection d'un paiement par son numéro de reçu
            # Pourquoi le paramètre "?" : Protection contre les injections SQL
            cursor.execute(
                """SELECT id, eleve_id, montant, date_paiement, mode, numero_recu, solde_apres
                   FROM paiement
                   WHERE numero_recu = ?""",
                (numero_recu,)
            )
            
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def next_sequence(self, annee: str, cursor=None) -> int:
        """
        Génère le prochain numéro de séquence pour une année donnée.
        
        Args:
            annee: Année sous forme de chaîne (ex: "2024")
            cursor: Curseur SQLite optionnel (si fourni, utilise ce curseur au lieu
                    de créer une nouvelle transaction)
        
        Returns:
            Le prochain numéro de séquence (commence à 1 si aucun paiement pour cette année).
        
        Pourquoi ce format : Les numéros de reçu sont au format REC-AAAA-NNNNNN
        où AAAA est l'année et NNNNNN est un numéro séquentiel sur 6 chiffres.
        Cette méthode génère le prochain NNNNNN pour une année donnée.
        
        Pourquoi le paramètre cursor optionnel : Permet d'appeler cette méthode
        depuis une transaction existante (enregistrer_paiement) sans créer
        une transaction imbriquée (ce que SQLite n'accepte pas).
        
        Pourquoi MAX(...) + 1 : Récupère le plus grand numéro de séquence existant
        pour l'année et ajoute 1 pour obtenir le prochain. S'il n'y a aucun paiement
        pour cette année, retourne 1.
        """
        if cursor is not None:
            # Utilisation du curseur fourni (pas de nouvelle transaction)
            # Pourquoi : Évite les transactions imbriquées
            cursor.execute(
                """SELECT MAX(CAST(substr(numero_recu, 10) AS INTEGER)) as max_seq
                   FROM paiement
                   WHERE numero_recu LIKE ?""",
                (f"REC-{annee}-%",)
            )
            result = cursor.fetchone()
            max_seq = result['max_seq'] if result and result['max_seq'] else 0
            return max_seq + 1
    
    # ===== Section : Requêtes d'agrégation pour le tableau de bord =====
    
    def sum_all_payments(self) -> int:
        """
        Calcule la somme totale de tous les paiements enregistrés.
        
        Returns:
            La somme totale des paiements (en FCFA, entier).
            Retourne 0 s'il n'y a aucun paiement.
        
        Pourquoi COALESCE(SUM(montant), 0) : Si la base est vide ou si le SUM
        retourne NULL, COALESCE remplace NULL par 0.
        
        Pourquoi cette méthode : Permet d'afficher le total encaissé
        dans le tableau de bord.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : somme de tous les montants de paiements
            cursor.execute("SELECT COALESCE(SUM(montant), 0) as total FROM paiement")
            result = cursor.fetchone()
            return result['total'] if result else 0
        else:
            # Création d'une nouvelle transaction (cas d'appel isolé)
            with self.database.transaction() as cursor:
                cursor.execute(
                    """SELECT MAX(CAST(substr(numero_recu, 10) AS INTEGER)) as max_seq
                       FROM paiement
                       WHERE numero_recu LIKE ?""",
                    (f"REC-{annee}-%",)
                )
                result = cursor.fetchone()
                max_seq = result['max_seq'] if result and result['max_seq'] else 0
                return max_seq + 1