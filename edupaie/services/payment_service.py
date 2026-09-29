# =============================================================================
# payment_service.py - Service pour la logique métier des paiements
# =============================================================================
# Rôle : Fournit la logique métier pour l'enregistrement des paiements.
# =============================================================================
# Ce fichier utilise :
# - data.payment_repository.PaymentRepository pour l'accès aux données
# - data.student_repository.StudentRepository pour récupérer les infos élève
# - services.exceptions pour les erreurs métier
# =============================================================================
# Ce fichier est utilisé par :
# - ui.payment_dialog pour l'enregistrement des paiements
# =============================================================================

import sys
import re
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/services/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from edupaie.data.payment_repository import PaymentRepository
from edupaie.data.database import Database
from edupaie.services.student_service import StudentService
from edupaie.services.exceptions import ValidationError, NotFoundError


class PaymentService:
    """
    Service pour la gestion des paiements avec validation des règles métier.
    
    Responsabilité : Fournir les opérations métier sur les paiements en appliquant
    toutes les validations nécessaires avant d'interagir avec la base de données.
    
    Pourquoi un service : Sépare la logique métier de l'accès aux données et de l'interface.
    Le service valide les données, applique les règles métier, et lève des exceptions
    appropriées que l'interface peut afficher à l'utilisateur.
    
    Règles métier implémentées :
    - Montant entier > 0
    - Date valide (format YYYY-MM-DD, pas dans le futur)
    - Mode autorisé (especes, cheque, virement, mobile_money)
    - Paiement ne peut pas dépasser le solde restant
    - Numéro de reçu unique (format REC-AAAA-NNNNNN)
    - Solde après paiement figé (historique)
    """
    
    # Modes de paiement autorisés
    MODES_AUTORISES = ['especes', 'cheque', 'virement', 'mobile_money']
    
    def __init__(self, database: Database) -> None:
        """
        Initialise le service avec une connexion à la base de données.
        
        Args:
            database: Instance de la classe Database pour la connexion.
        """
        self.database = database
        self.payment_repository = PaymentRepository(database)
        self.student_service = StudentService(database)
    
    # ===== Section : Validations =====
    
    def _validate_montant(self, montant: int) -> None:
        """
        Valide le montant du paiement.
        
        Règle : Le montant doit être un entier strictement positif.
        
        Args:
            montant: Montant à valider
        
        Raises:
            ValidationError: Si le montant est <= 0.
        
        Pourquoi cette validation : Un montant nul ou négatif n'a pas de sens
        pour un paiement.
        """
        if montant <= 0:
            raise ValidationError("Le montant doit être strictement positif.")
    
    def _validate_date(self, date_paiement: str) -> None:
        """
        Valide la date du paiement.
        
        Règle : La date doit être au format YYYY-MM-DD et ne pas être dans le futur.
        
        Args:
            date_paiement: Date à valider (format YYYY-MM-DD)
        
        Raises:
            ValidationError: Si le format est incorrect ou si la date est dans le futur.
        
        Pourquoi cette validation : Une date future n'a pas de sens pour un paiement
        déjà effectué. Le format YYYY-MM-DD est requis pour la cohérence avec la base.
        """
        # Vérification du format avec regex
        # Pourquoi regex : Valide précisément le format YYYY-MM-DD
        pattern = r'^(\d{4})-(\d{2})-(\d{2})$'
        match = re.match(pattern, date_paiement)
        
        if not match:
            raise ValidationError(
                "La date doit être au format YYYY-MM-DD (ex: 2024-09-15)."
            )
        
        # Vérification que la date est valide (ex: pas 2024-02-30)
        try:
            date_obj = datetime.strptime(date_paiement, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("La date n'est pas valide.")
        
        # Vérification que la date n'est pas dans le futur
        today = datetime.now().date()
        if date_obj > today:
            raise ValidationError("La date ne peut pas être dans le futur.")
    
    def _validate_mode(self, mode: str) -> None:
        """
        Valide le mode de paiement.
        
        Règle : Le mode doit être l'un des modes autorisés.
        
        Args:
            mode: Mode de paiement à valider
        
        Raises:
            ValidationError: Si le mode n'est pas autorisé.
        
        Pourquoi cette validation : Restreint les modes de paiement à ceux
        définis dans le système pour éviter les erreurs de saisie.
        """
        if mode not in self.MODES_AUTORISES:
            modes_str = ", ".join(self.MODES_AUTORISES)
            raise ValidationError(
                f"Le mode de paiement doit être l'un des suivants : {modes_str}."
            )
    
    def _validate_solde_suffisant(self, eleve_id: int, montant: int) -> None:
        """
        Valide que le montant ne dépasse pas le solde restant.
        
        Règle : Le paiement ne peut pas dépasser le solde restant de l'élève.
        
        Args:
            eleve_id: Identifiant de l'élève
            montant: Montant du paiement
        
        Raises:
            ValidationError: Si le montant dépasse le solde restant.
        
        Pourquoi cette validation : Empêche de payer plus que ce qui est dû,
        ce qui créerait un solde négatif (remboursement dû) qui doit être traité
        par un processus différent.
        
        Note : Cette validation utilise StudentService.solde() qui crée une transaction.
        Elle doit être appelée AVANT la transaction d'enregistrement pour éviter
        les transactions imbriquées (SQLite ne les accepte pas).
        """
        # Utilisation du student_service pour calculer le solde
        # Pourquoi réutiliser la logique existante : Évite la duplication du calcul du solde
        solde_actuel = self.student_service.solde(eleve_id)
        
        # Vérification que le montant ne dépasse pas le solde
        if montant > solde_actuel:
            raise ValidationError(
                f"Le montant ({montant:,} FCFA) dépasse le solde restant ({solde_actuel:,} FCFA)."
            )
    
    # ===== Section : Opérations métier =====
    
    def enregistrer_paiement(self, eleve_id: int, montant: int, 
                             date_paiement: str, mode: str) -> Dict[str, Any]:
        """
        Enregistre un nouveau paiement pour un élève.
        
        Cette méthode effectue toutes les validations nécessaires, génère un numéro
        de reçu unique, calcule le solde après paiement, et insère le paiement
        dans une transaction atomique.
        
        Args:
            eleve_id: Identifiant de l'élève
            montant: Montant du paiement (en FCFA, entier)
            date_paiement: Date du paiement (format YYYY-MM-DD)
            mode: Mode de paiement ('especes', 'cheque', 'virement', 'mobile_money')
        
        Returns:
            Dictionnaire contenant les informations du paiement créé.
        
        Raises:
            ValidationError: Si une validation échoue.
            NotFoundError: Si l'élève n'existe pas.
            sqlite3.IntegrityError: Si le numéro de reçu existe déjà (conflit rare).
        
        Pourquoi une transaction atomique : Toutes les opérations (validation,
        génération du numéro, insertion) doivent réussir ensemble ou échouer ensemble.
        Si une étape échoue, tout est annulé (rollback) pour éviter l'incohérence.
        
        Pourquoi BEGIN IMMEDIATE : Verrouille la base en mode écriture immédiatement,
        ce qui empêche d'autres transactions de modifier les données pendant
        l'enregistrement. Cela évite les conflits de numéros de reçu (doublons).
        
        Pourquoi le format REC-AAAA-NNNNNN : Format standardisé pour les numéros
        de reçu avec l'année et un numéro séquentiel sur 6 chiffres. Facilite
        le tri chronologique et l'identification.
        
        Pourquoi solde_apres est figé : Le solde après paiement est calculé au moment
        du paiement et stocké figé. Cela permet de suivre l'historique de l'évolution
        du solde et de détecter des erreurs de calcul rétrospectivement.
        """
        # ===== Étape 1 : Validation des données =====
        self._validate_montant(montant)
        self._validate_date(date_paiement)
        self._validate_mode(mode)
        # Note : _validate_solde_suffisant est appelée DANS la transaction
        # pour éviter les transactions imbriquées (SQLite ne les accepte pas)
        
        # ===== Étape 2 : Transaction atomique =====
        # Pourquoi une transaction explicite : Garantit l'atomicité de l'opération
        # Pourquoi BEGIN IMMEDIATE dans Database.transaction() : Verrouille la base
        # en écriture immédiatement, évitant les conflits de numéros de reçu entre utilisateurs
        with self.database.transaction() as cursor:
            # ===== Calcul du solde avant paiement =====
            # Pourquoi calculer dans la transaction : Évite d'appeler student_service.solde()
            # qui créerait une transaction imbriquée (SQLite ne l'accepte pas)
            cursor.execute(
                """SELECT total_du FROM eleve WHERE id = ?""",
                (eleve_id,)
            )
            student = cursor.fetchone()
            if student is None:
                raise NotFoundError(f"Aucun élève trouvé avec l'identifiant {eleve_id}.")
            
            total_du = student['total_du']
            
            # Récupération du total payé
            cursor.execute(
                """SELECT COALESCE(SUM(montant), 0) as total
                   FROM paiement
                   WHERE eleve_id = ?""",
                (eleve_id,)
            )
            result = cursor.fetchone()
            total_paye = result['total'] if result else 0
            
            solde_avant = total_du - total_paye
            
            # ===== Étape 3 : Validation du solde suffisant =====
            if montant > solde_avant:
                raise ValidationError(
                    f"Le montant ({montant:,} FCFA) dépasse le solde restant ({solde_avant:,} FCFA)."
                )
            
            # ===== Étape 4 : Génération du numéro de reçu =====
            # Pourquoi passer cursor : Évite de créer une transaction imbriquée (SQLite ne l'accepte pas)
            annee = date_paiement[:4]
            sequence = self.payment_repository.next_sequence(annee, cursor)
            numero_recu = f"REC-{annee}-{sequence:06d}"
            
            # ===== Étape 5 : Calcul du solde après paiement =====
            solde_apres = solde_avant - montant
            
            # ===== Étape 6 : Insertion du paiement =====
            cursor.execute(
                """INSERT INTO paiement 
                   (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
            )
            
            paiement_id = cursor.lastrowid
        
        # ===== Étape 5 : Retour du paiement créé =====
        paiement = self.payment_repository.get_by_id(paiement_id)
        return paiement
