# =============================================================================
# student_detail.py - Fiche détaillée d'un élève
# =============================================================================
# Rôle : QDialog affichant les informations détaillées d'un élève.
# =============================================================================
# Ce fichier utilise :
# - PySide6 pour les widgets Qt
# - services.student_service pour la logique métier
# =============================================================================
# Ce fichier est utilisé par :
# - ui.students_view pour ouvrir la fiche par double-clic
# =============================================================================

import sys
from pathlib import Path
from typing import Optional

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from edupaie.services.payment_service import PaymentService
from edupaie.services.student_service import StudentService
from edupaie.services.receipt_service import ReceiptService
from edupaie.ui.payment_dialog import PaymentDialog
from edupaie.ui.error_handler import handle_slot_errors
from edupaie.ui.theme import STATUS, format_fcfa, TEXT


class StudentDetail(QDialog):
    """
    Fiche détaillée d'un élève.
    
    Responsabilité : Afficher les informations complètes d'un élève
    avec son solde, son statut et l'historique de ses paiements.
    
    Pourquoi QDialog : Fenêtre modale qui affiche les détails d'un élève
    sans bloquer l'application principale (contrairement au formulaire).
    
    Fonctionnalités :
    - Informations de l'élève (nom, prénom, classe, année scolaire)
    - Informations financières (total dû, payé, solde, statut)
    - Historique des paiements (date, montant, mode, numéro de reçu, solde après)
    - Couleur du statut (vert Soldé, orange Partiel, rouge Non payé)
    """
    
    # Signal émis après un paiement
    # Pourquoi Signal : Permet de notifier la vue principale pour rafraîchissement
    payment_made = Signal()
    
    def __init__(self, student_service: StudentService, student_id: int) -> None:
        """
        Initialise la fiche détaillée.
        
        Args:
            student_service: Instance du service pour les opérations métier
            student_id: Identifiant de l'élève à afficher
        """
        super().__init__()
        
        self.student_service = student_service
        self.payment_service = PaymentService(student_service.database)
        self.receipt_service = ReceiptService(
            self.payment_service.payment_repository,
            self.student_service.repository
        )
        self.student_id = student_id
        
        # Configuration de la fenêtre
        self.setWindowTitle("Fiche Élève")
        self.setMinimumSize(600, 500)
        
        # Création de l'interface
        self._create_ui()
        
        # Chargement des données
        self._load_student_data()
    
    def _create_ui(self) -> None:
        """
        Crée l'interface utilisateur de la fiche.
        
        Crée :
        - Section informations de l'élève
        - Section informations financières avec statut coloré
        - Tableau des paiements
        - Bouton Fermer
        """
        # Layout principal
        layout = QVBoxLayout(self)
        
        # ===== Section : Informations de l'élève =====
        info_layout = QVBoxLayout()
        
        # Nom et prénom
        self.nom_label = QLabel()
        nom_font = QFont()
        nom_font.setPointSize(16)
        nom_font.setBold(True)
        self.nom_label.setFont(nom_font)
        info_layout.addWidget(self.nom_label)
        
        # Classe et année scolaire
        self.classe_label = QLabel()
        info_layout.addWidget(self.classe_label)
        
        layout.addLayout(info_layout)
        
        # Séparateur
        separator = QLabel("─" * 50)
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)
        
        # ===== Section : Informations financières =====
        finance_layout = QVBoxLayout()
        
        # Total dû
        self.total_label = QLabel()
        total_font = QFont()
        total_font.setPointSize(12)
        total_font.setBold(True)
        self.total_label.setFont(total_font)
        finance_layout.addWidget(self.total_label)
        
        # Payé
        self.paye_label = QLabel()
        finance_layout.addWidget(self.paye_label)
        
        # Solde
        self.solde_label = QLabel()
        solde_font = QFont()
        solde_font.setPointSize(12)
        solde_font.setBold(True)
        self.solde_label.setFont(solde_font)
        finance_layout.addWidget(self.solde_label)
        
        # Statut avec couleur
        self.statut_label = QLabel()
        statut_font = QFont()
        statut_font.setPointSize(14)
        statut_font.setBold(True)
        self.statut_label.setFont(statut_font)
        self.statut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        finance_layout.addWidget(self.statut_label)
        
        layout.addLayout(finance_layout)
        
        # Séparateur
        separator2 = QLabel("─" * 50)
        separator2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator2)
        
        # ===== Section : Historique des paiements =====
        paiements_label = QLabel("Historique des paiements :")
        layout.addWidget(paiements_label)
        
        self.paiements_table = QTableWidget()
        self.paiements_table.setColumnCount(5)
        self.paiements_table.setHorizontalHeaderLabels([
            "N° Reçu", "Date", "Mode", "Montant (FCFA)", "Solde après (FCFA)"
        ])
        
        # Configuration du tableau
        self.paiements_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.paiements_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.paiements_table.setAlternatingRowColors(True)
        self.paiements_table.setSortingEnabled(True)
        
        # Masquer les numéros de ligne
        self.paiements_table.verticalHeader().setVisible(False)
        
        # Définir la hauteur des lignes
        self.paiements_table.verticalHeader().setDefaultSectionSize(36)
        
        # Ajustement des colonnes
        header = self.paiements_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # N° Reçu
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Mode
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Montant
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Solde après
        
        # Connexion signal -> slot : sélection -> activation du bouton Consulter le reçu
        self.paiements_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.paiements_table)
        
        # Espaceur
        layout.addStretch()
        
        # ===== Boutons =====
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_view_receipt = QPushButton("Consulter le reçu")
        self.btn_view_receipt.setProperty("variant", "secondary")
        self.btn_view_receipt.setEnabled(False)  # Désactivé par défaut
        self.btn_view_receipt.clicked.connect(self._on_view_receipt_clicked)
        buttons_layout.addWidget(self.btn_view_receipt)
        
        self.btn_new_payment = QPushButton("Nouveau paiement")
        self.btn_new_payment.setProperty("variant", "primary")
        self.btn_new_payment.clicked.connect(self._on_new_payment_clicked)
        buttons_layout.addWidget(self.btn_new_payment)
        
        self.btn_close = QPushButton("Fermer")
        self.btn_close.setProperty("variant", "secondary")
        self.btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btn_close)
        
        layout.addLayout(buttons_layout)
    
    def _load_student_data(self) -> None:
        """
        Charge et affiche les données de l'élève.
        
        Récupère les informations de l'élève avec solde et statut,
        puis remplit les labels et le tableau des paiements.
        """
        try:
            # Récupération des données de l'élève
            student = self.student_service.get_student_with_solde_and_statut(self.student_id)
            
            if student is None:
                QMessageBox.warning(self, "Non trouvé", "L'élève n'existe pas.")
                self.reject()
                return
            
            # Affichage des informations de l'élève
            self.nom_label.setText(f"{student['nom']} {student['prenom']}")
            self.classe_label.setText(f"Classe : {student['nom_classe']} | Année scolaire : {student['annee_scolaire']}")
            
            # Calcul du montant payé
            total_paye = student['total_du'] - student['solde']
            
            # Affichage des informations financières
            self.total_label.setText(f"Total dû : {format_fcfa(student['total_du'])}")
            self.paye_label.setText(f"Payé : {format_fcfa(total_paye)}")
            self.solde_label.setText(f"Solde : {format_fcfa(student['solde'])}")
            
            # Affichage du statut avec couleur (fond ET texte pour contraste WCAG)
            statut = student['statut']
            statut_colors = STATUS.get(statut, {"bg": "#FFFFFF", "fg": TEXT})
            self.statut_label.setText(f"Statut : {statut}")
            self.statut_label.setStyleSheet(f"color: {statut_colors['fg']}; background-color: {statut_colors['bg']}; padding: 10px; border-radius: 5px; font-weight: bold;")
            
            # Chargement des paiements
            self._load_paiements()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des données : {str(e)}")
    
    def _load_paiements(self) -> None:
        """
        Charge et affiche l'historique chronologique des paiements de l'élève.
        
        Récupère les paiements via payment_service.historique() et les affiche
        dans le tableau trié chronologiquement (du plus ancien au plus récent).
        
        Pourquoi chronologique : Permet de voir l'évolution des paiements dans le temps,
        ce qui est plus pertinent pour l'historique que du plus récent au plus ancien.
        
        Pourquoi stocker l'ID dans UserRole : Permet de relier chaque ligne du tableau
        à son paiement en base de données (pour consulter le reçu par exemple).
        """
        try:
            # Récupération de l'historique chronologique
            paiements = self.payment_service.historique(self.student_id)
            
            # Remplissage du tableau
            self.paiements_table.setSortingEnabled(False)
            self.paiements_table.setRowCount(0)
            
            for row, paiement in enumerate(paiements):
                self.paiements_table.insertRow(row)
                
                # N° Reçu
                recu_item = QTableWidgetItem(paiement['numero_recu'])
                # Stockage de l'ID du paiement dans UserRole pour relier à la base
                # Pourquoi UserRole : Permet de récupérer l'ID quand l'utilisateur sélectionne une ligne
                recu_item.setData(Qt.ItemDataRole.UserRole, paiement['id'])
                self.paiements_table.setItem(row, 0, recu_item)
                
                # Date
                date_item = QTableWidgetItem(paiement['date_paiement'])
                self.paiements_table.setItem(row, 1, date_item)
                
                # Mode
                mode_item = QTableWidgetItem(paiement['mode'].capitalize())
                self.paiements_table.setItem(row, 2, mode_item)
                
                # Montant
                montant_item = QTableWidgetItem(format_fcfa(paiement['montant']))
                montant_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.paiements_table.setItem(row, 3, montant_item)
                
                # Solde après
                solde_item = QTableWidgetItem(format_fcfa(paiement['solde_apres']))
                solde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.paiements_table.setItem(row, 4, solde_item)
            
            self.paiements_table.setSortingEnabled(True)
            
            # Message si aucun paiement
            if len(paiements) == 0:
                self.paiements_table.insertRow(0)
                no_paiement_item = QTableWidgetItem("Aucun paiement enregistré")
                no_paiement_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.paiements_table.setItem(0, 0, no_paiement_item)
                self.paiements_table.setSpan(0, 0, 1, 5)  # Fusionne les 5 colonnes
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des paiements : {str(e)}")
    
    @handle_slot_errors
    def _on_selection_changed(self) -> None:
        """
        Gère le changement de sélection dans le tableau des paiements.
        
        Active le bouton "Consulter le reçu" si une ligne est sélectionnée,
        le désactive sinon.
        
        Pourquoi itemSelectionChanged.connect : Permet d'activer/désactiver
        le bouton de consultation du reçu selon la sélection.
        """
        # Vérification si une ligne est sélectionnée
        selected_items = self.paiements_table.selectedItems()
        has_selection = len(selected_items) > 0
        
        # Activation/désactivation du bouton
        self.btn_view_receipt.setEnabled(has_selection)
    
    @handle_slot_errors
    def _on_view_receipt_clicked(self) -> None:
        """
        Gère le clic sur le bouton Consulter le reçu.
        
        Propose à l'utilisateur de générer ou ré-imprimer le reçu PDF
        du paiement sélectionné depuis l'historique.
        
        Pourquoi ré-impression identique : Le reçu est reconstruit UNIQUEMENT
        à partir de données figées en base (paiement.solde_apres, numero_recu, etc.),
        garantissant que deux générations successives sont identiques.
        
        Pourquoi l'ID dans UserRole : Permet de récupérer l'ID du paiement sélectionné
        depuis la ligne du tableau pour le relier à la base de données.
        """
        # Récupération de la ligne sélectionnée
        selected_items = self.paiements_table.selectedItems()
        if not selected_items:
            return
        
        # Récupération de l'ID du paiement (stocké dans UserRole de la première colonne)
        row = self.paiements_table.currentRow()
        recu_item = self.paiements_table.item(row, 0)
        paiement_id = recu_item.data(Qt.ItemDataRole.UserRole)
        
        # Création d'un dialogue personnalisé pour choisir l'action
        dialog = QDialog(self)
        dialog.setWindowTitle("Reçu de paiement")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        label = QLabel("Que souhaitez-vous faire avec ce reçu ?")
        layout.addWidget(label)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_save_pdf = QPushButton("Enregistrer le PDF")
        btn_save_pdf.setProperty("variant", "primary")
        btn_save_pdf.clicked.connect(lambda: self._enregistrer_pdf(dialog, paiement_id))
        buttons_layout.addWidget(btn_save_pdf)
        
        btn_print = QPushButton("Imprimer")
        btn_print.setProperty("variant", "secondary")
        btn_print.clicked.connect(lambda: self._imprimer_recu(dialog, paiement_id))
        buttons_layout.addWidget(btn_print)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setProperty("variant", "secondary")
        btn_cancel.clicked.connect(dialog.reject)
        buttons_layout.addWidget(btn_cancel)
        
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        
        # Affichage du dialogue
        dialog.exec()
    
    @handle_slot_errors
    def _enregistrer_pdf(self, dialog: QDialog, paiement_id: int) -> None:
        """
        Enregistre le reçu PDF au choix de l'utilisateur.
        
        Args:
            dialog: Dialogue à fermer après enregistrement.
            paiement_id: Identifiant du paiement.
        
        Pourquoi QFileDialog.getSaveFileName : Permet à l'utilisateur de choisir
        le nom et l'emplacement du fichier PDF.
        
        Pourquoi dossier par défaut via utils/paths : Stocke les reçus dans un
        dossier dédié pour l'organisation (user_data_dir/reçus).
        """
        from edupaie.utils.paths import user_data_dir
        from datetime import datetime
        
        # Récupération du numéro de reçu pour le nom par défaut
        paiement = self.payment_service.payment_repository.get_by_id(paiement_id)
        if paiement is None:
            QMessageBox.warning(self, "Non trouvé", "Le paiement n'existe pas.")
            return
        
        # Dossier par défaut pour les reçus
        receipts_dir = user_data_dir() / "reçus"
        receipts_dir.mkdir(parents=True, exist_ok=True)
        
        # Ouverture du dialogue de sauvegarde
        fichier_pdf, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le reçu",
            str(receipts_dir / f"{paiement['numero_recu']}.pdf"),
            "Fichiers PDF (*.pdf)"
        )
        
        if fichier_pdf:
            try:
                # Génération du PDF
                chemin = self.receipt_service.generer_recu(paiement_id, fichier_pdf)
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Reçu enregistré avec succès :\n{chemin}"
                )
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du PDF : {str(e)}")
    
    @handle_slot_errors
    def _imprimer_recu(self, dialog: QDialog, paiement_id: int) -> None:
        """
        Imprime directement le reçu.
        
        Args:
            dialog: Dialogue à fermer après impression.
            paiement_id: Identifiant du paiement.
        
        Pourquoi approche simplifiée : PySide6 standard n'inclut pas QPdfDocument.
        Pour l'instant, génère le PDF et informe l'utilisateur qu'il peut l'imprimer
        via son lecteur PDF.
        
        Note : Une implémentation complète nécessiterait d'ajouter PySide6-Pdf
        ou d'utiliser une bibliothèque externe pour l'impression directe.
        """
        from edupaie.utils.paths import user_data_dir
        
        try:
            # Génération du PDF dans le dossier reçus
            receipts_dir = user_data_dir() / "reçus"
            receipts_dir.mkdir(parents=True, exist_ok=True)
            
            paiement = self.payment_service.payment_repository.get_by_id(paiement_id)
            if paiement is None:
                QMessageBox.warning(self, "Non trouvé", "Le paiement n'existe pas.")
                return
            
            chemin_pdf = str(receipts_dir / f"{paiement['numero_recu']}.pdf")
            self.receipt_service.generer_recu(paiement_id, chemin_pdf)
            
            QMessageBox.information(
                self,
                "PDF généré",
                f"Le reçu a été généré :\n{chemin_pdf}\n\n"
                "Vous pouvez l'imprimer depuis votre lecteur PDF."
            )
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du PDF : {str(e)}")
    
    @handle_slot_errors
    def _on_new_payment_clicked(self) -> None:
        """
        Gère le clic sur le bouton Nouveau paiement.
        
        Ouvre le dialogue de paiement pour enregistrer un nouveau paiement.
        Si le paiement est enregistré, recharge les données de la fiche.
        
        Pourquoi QPushButton.clicked.connect : Permet d'ouvrir le dialogue
        de paiement par un clic sur le bouton.
        
        Pourquoi recharger après paiement : Les données de la fiche doivent
        refléter le nouveau paiement (solde mis à jour, nouveau paiement dans la liste).
        """
        # Ouverture du dialogue de paiement
        payment_dialog = PaymentDialog(
            self.payment_service,
            self.student_service,
            self.receipt_service,
            self.student_id,
            self
        )
        
        # Connexion signal -> slot : paiement effectué -> propagation du signal
        # Pourquoi connecter : Permet de notifier la vue principale pour rafraîchissement
        payment_dialog.payment_made.connect(self.payment_made.emit)
        
        result = payment_dialog.exec()
        
        # Si l'utilisateur a validé ( QDialog.Accepted)
        if result == QDialog.DialogCode.Accepted:
            # Rechargement des données de la fiche
            self._load_student_data()
            
            # Émission du signal pour notifier le rafraîchissement
            # Pourquoi Signal : Permet au tableau de bord de se rafraîchir après paiement
            self.payment_made.emit()