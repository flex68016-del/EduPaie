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
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from edupaie.services.student_service import StudentService
from edupaie.services.payment_service import PaymentService
from edupaie.ui.payment_dialog import PaymentDialog
from edupaie.ui.error_handler import handle_slot_errors


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
            "Date", "Montant (FCFA)", "Mode", "N° Reçu", "Solde après (FCFA)"
        ])
        
        # Configuration du tableau
        self.paiements_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.paiements_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.paiements_table.setAlternatingRowColors(True)
        self.paiements_table.setSortingEnabled(True)
        
        # Ajustement des colonnes
        header = self.paiements_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Montant
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Mode
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # N° Reçu
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Solde après
        
        layout.addWidget(self.paiements_table)
        
        # Espaceur
        layout.addStretch()
        
        # ===== Boutons =====
        buttons_layout = QHBoxLayout()
        
        self.btn_new_payment = QPushButton("Nouveau paiement")
        self.btn_new_payment.setMinimumHeight(35)
        self.btn_new_payment.setStyleSheet("background-color: #2196F3; color: white;")
        # Connexion signal -> slot : clic -> ouverture du dialogue de paiement
        self.btn_new_payment.clicked.connect(self._on_new_payment_clicked)
        buttons_layout.addWidget(self.btn_new_payment)
        
        self.btn_close = QPushButton("Fermer")
        self.btn_close.setMinimumHeight(35)
        # Connexion signal -> slot : clic -> fermeture de la fiche
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
            self.total_label.setText(f"Total dû : {student['total_du']:,} FCFA")
            self.paye_label.setText(f"Payé : {total_paye:,} FCFA")
            self.solde_label.setText(f"Solde : {student['solde']:,} FCFA")
            
            # Affichage du statut avec couleur
            self.statut_label.setText(f"Statut : {student['statut']}")
            # Attribution de la couleur selon le statut
            # Pourquoi ces couleurs : Vert pour soldé (positif), orange pour partiel (attention), rouge pour non payé (alerte)
            if student['statut'] == "Soldé":
                self.statut_label.setStyleSheet("color: green; background-color: #e8f5e9; padding: 10px; border-radius: 5px;")
            elif student['statut'] == "Partiellement payé":
                self.statut_label.setStyleSheet("color: orange; background-color: #fff3e0; padding: 10px; border-radius: 5px;")
            elif student['statut'] == "Non payé":
                self.statut_label.setStyleSheet("color: red; background-color: #ffebee; padding: 10px; border-radius: 5px;")
            
            # Chargement des paiements
            self._load_paiements()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des données : {str(e)}")
    
    def _load_paiements(self) -> None:
        """
        Charge et affiche l'historique des paiements de l'élève.
        
        Récupère les paiements via le payment_repository et les affiche
        dans le tableau.
        """
        try:
            # Récupération des paiements
            paiements = self.student_service.payment_repository.get_paiements_by_eleve(self.student_id)
            
            # Remplissage du tableau
            self.paiements_table.setSortingEnabled(False)
            self.paiements_table.setRowCount(0)
            
            for row, paiement in enumerate(paiements):
                self.paiements_table.insertRow(row)
                
                # Date
                date_item = QTableWidgetItem(paiement['date_paiement'])
                self.paiements_table.setItem(row, 0, date_item)
                
                # Montant
                montant_item = QTableWidgetItem(f"{paiement['montant']:,}")
                montant_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.paiements_table.setItem(row, 1, montant_item)
                
                # Mode
                mode_item = QTableWidgetItem(paiement['mode'].capitalize())
                self.paiements_table.setItem(row, 2, mode_item)
                
                # Numéro de reçu
                recu_item = QTableWidgetItem(paiement['numero_recu'])
                self.paiements_table.setItem(row, 3, recu_item)
                
                # Solde après
                solde_item = QTableWidgetItem(f"{paiement['solde_apres']:,}")
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
            self.student_id,
            self
        )
        
        result = payment_dialog.exec()
        
        # Si l'utilisateur a validé ( QDialog.Accepted)
        if result == QDialog.DialogCode.Accepted:
            # Rechargement des données de la fiche
            self._load_student_data()