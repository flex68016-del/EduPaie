# =============================================================================
# receipt_service.py - Service pour la génération des reçus PDF
# =============================================================================
# Rôle : Générer des reçus PDF pour les paiements.
# =============================================================================
# Ce fichier utilise :
# - fpdf2 pour la génération de fichiers PDF
# - data.payment_repository.PaymentRepository pour récupérer les données du paiement
# - data.student_repository.StudentRepository pour récupérer les infos de l'élève
# =============================================================================
# Ce fichier est utilisé par :
# - ui.payment_dialog pour générer un reçu après paiement
# - ui.student_detail pour ré-imprimer un reçu depuis l'historique
# =============================================================================

import sys
from pathlib import Path
from typing import Optional

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/services/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fpdf import FPDF
from edupaie.data.payment_repository import PaymentRepository
from edupaie.data.student_repository import StudentRepository


class ReceiptService:
    """
    Service pour la génération de reçus PDF pour les paiements.
    
    Responsabilité : Générer des reçus PDF reproductibles et professionnels
    à partir des données figées en base de données.
    
    Pourquoi un service séparé : Sépare la logique de génération PDF de la logique
    métier et de l'interface, facilitant les tests et les modifications futures
    (changement de bibliothèque PDF, mise en page, etc.).
    
    Principe de reproductibilité : Le reçu est reconstruit UNIQUEMENT à partir de
    données figées en base (paiement.solde_apres, paiement.numero_recu, etc.).
    Cela garantit que deux générations successives du même reçu sont identiques,
    même si les données de l'élève changent par la suite.
    """
    
    def __init__(self, payment_repository: PaymentRepository,
                 student_repository: StudentRepository) -> None:
        """
        Initialise le service avec les repositories nécessaires.
        
        Args:
            payment_repository: Repository pour accéder aux données des paiements.
            student_repository: Repository pour accéder aux données des élèves.
        """
        self.payment_repository = payment_repository
        self.student_repository = student_repository
    
    # Alias pour compatibilité avec le code existant qui utilise generate_receipt
    # Pourquoi : Certains fichiers utilisent le nom anglais generate_receipt
    generate_receipt = generer_recu
    
    def generer_recu(self, paiement_id: int, chemin_sortie: Optional[str] = None) -> str:
        """
        Génère un reçu PDF pour un paiement.
        
        Le reçu est reconstruit UNIQUEMENT à partir de données figées en base :
        - paiement.numero_recu : numéro unique du reçu
        - paiement.montant : montant du paiement
        - paiement.date_paiement : date du paiement
        - paiement.mode : mode de paiement
        - paiement.solde_apres : solde après paiement (figé)
        
        Les informations de l'élève (nom, prénom, classe) sont utilisées pour
        l'affichage mais le contenu financier du reçu provient uniquement des
        données figées du paiement.
        
        Args:
            paiement_id: Identifiant du paiement.
            chemin_sortie: Chemin de sortie du PDF. Si None, utilise un chemin
                          par défaut dans le dossier reçus.
        
        Returns:
            Le chemin du fichier PDF généré.
        
        Raises:
            ValueError: Si le paiement n'existe pas.
        
        Pourquoi reconstruction figée : Garantit la reproductibilité du reçu.
        Si on réimprime un reçu 6 mois après, il doit être identique à l'original,
        même si l'élève a changé de classe ou si des nouveaux paiements ont été effectués.
        """
        # Récupération du paiement
        paiement = self.payment_repository.get_by_id(paiement_id)
        if paiement is None:
            raise ValueError(f"Paiement {paiement_id} introuvable.")
        
        # Récupération des informations de l'élève
        eleve = self.student_repository.get_by_id(paiement['eleve_id'])
        if eleve is None:
            raise ValueError(f"Élève {paiement['eleve_id']} introuvable.")
        
        # Récupération du nom de la classe
        classe_nom = self.student_repository.get_class_name(eleve['classe_id'])
        
        # Définition du chemin de sortie si non fourni
        if chemin_sortie is None:
            from edupaie.utils.paths import user_data_dir
            receipts_dir = user_data_dir() / "reçus"
            receipts_dir.mkdir(parents=True, exist_ok=True)
            chemin_sortie = str(receipts_dir / f"{paiement['numero_recu']}.pdf")
        
        # Création du PDF
        pdf = FPDF()
        pdf.add_page()

        # ===== En-tête avec fond coloré =====
        pdf.set_fill_color(44, 62, 80)  # Fond bleu foncé (#2c3e50)
        pdf.rect(0, 0, 210, 40, "F")  # Rectangle plein
        pdf.set_text_color(255, 255, 255)  # Texte blanc

        # Titre de l'établissement
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 15, "EDUPAIE", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, "Système de Gestion des Paiements Scolaires", ln=True, align="C")
        pdf.ln(5)

        # Numéro de reçu
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"REÇU DE PAIEMENT", ln=True, align="C")
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, f"Numéro : {paiement['numero_recu']}", ln=True, align="C")

        # Réinitialisation du texte en noir
        pdf.set_text_color(0, 0, 0)
        pdf.ln(15)

        # ===== Cadre pour informations de l'élève =====
        pdf.set_fill_color(240, 244, 248)  # Fond gris clair (#f0f4f8)
        pdf.rect(10, pdf.get_y(), 190, 45, "F")
        pdf.set_xy(15, pdf.get_y() + 5)

        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(44, 62, 80)  # Titre en bleu foncé
        pdf.cell(0, 8, "INFORMATIONS DE L'ÉLÈVE", ln=True)
        pdf.set_text_color(0, 0, 0)  # Texte en noir
        pdf.ln(3)

        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 7, f"Nom : {eleve['nom']}", ln=True)
        pdf.cell(0, 7, f"Prénom : {eleve['prenom']}", ln=True)
        pdf.cell(0, 7, f"Classe : {classe_nom}", ln=True)
        pdf.cell(0, 7, f"Année scolaire : {eleve['annee_scolaire']}", ln=True)
        pdf.ln(10)

        # ===== Cadre pour détails du paiement =====
        pdf.set_fill_color(240, 244, 248)  # Fond gris clair (#f0f4f8)
        pdf.rect(10, pdf.get_y(), 190, 55, "F")
        pdf.set_xy(15, pdf.get_y() + 5)

        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(44, 62, 80)  # Titre en bleu foncé
        pdf.cell(0, 8, "DÉTAILS DU PAIEMENT", ln=True)
        pdf.set_text_color(0, 0, 0)  # Texte en noir
        pdf.ln(3)

        # Montant en évidence avec fond vert
        pdf.set_fill_color(76, 175, 80)  # Fond vert (#4caf50)
        pdf.set_text_color(255, 255, 255)  # Texte blanc
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 12, f"Montant : {paiement['montant']:,} FCFA", ln=True, fill=True)
        pdf.ln(5)

        pdf.set_text_color(0, 0, 0)  # Texte en noir
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 7, f"Date : {paiement['date_paiement']}", ln=True)
        pdf.cell(0, 7, f"Mode : {paiement['mode'].replace('_', ' ').title()}", ln=True)
        pdf.ln(5)

        # Solde avec couleur selon le statut
        pdf.set_font("Arial", "B", 12)
        if paiement['solde_apres'] == 0:
            pdf.set_text_color(76, 175, 80)  # Vert (#4caf50)
            statut_text = "SOLDÉ"
        elif paiement['solde_apres'] > 0:
            pdf.set_text_color(255, 152, 0)  # Orange (#ff9800)
            statut_text = "RESTE À PAYER"
        else:
            pdf.set_text_color(244, 67, 54)  # Rouge (#f44336)
            statut_text = "ERREUR"

        pdf.cell(0, 8, f"Solde après paiement : {paiement['solde_apres']:,} FCFA ({statut_text})", ln=True)
        pdf.set_text_color(0, 0, 0)  # Réinitialisation
        pdf.ln(15)

        # ===== Pied de page =====
        pdf.set_y(-30)
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(128, 128, 128)  # Gris (#808080)
        pdf.cell(0, 8, "Ce document fait foi de paiement", ln=True, align="C")
        pdf.cell(0, 8, "Généré automatiquement par EduPaie - " + paiement['date_paiement'], ln=True, align="C")
        
        # Sauvegarde du PDF
        pdf.output(chemin_sortie)
        
        return chemin_sortie
