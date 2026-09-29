# =============================================================================
# payment_dialog.py - Dialogue d'enregistrement de paiement
# =============================================================================
# Rôle : QDialog pour enregistrer un nouveau paiement pour un élève.
# =============================================================================
# Ce fichier utilise :
# - PySide6 pour les widgets Qt
# - services.payment_service pour la logique métier
# - services.student_service pour récupérer le solde
# =============================================================================
# Ce fichier est utilisé par :
# - ui.student_detail pour ouvrir le dialogue de paiement
# =============================================================================

import sys
from pathlib import Path
from datetime import datetime

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIntValidator
from edupaie.services.payment_service import PaymentService
from edupaie.services.student_service import StudentService
from edupaie.ui.error_handler import handle_slot_errors


class PaymentDialog(QDialog):
    """
    Dialogue d'enregistrement de paiement pour un élève.
    
    Responsabilité : Permettre à l'utilisateur de saisir un paiement
    avec validation UI et affichage du solde restant.
    
    Pourquoi QDialog : Fenêtre modale qui bloque l'application principale
    tant que le paiement n'est pas enregistré ou annulé.
    
    Fonctionnalités :
    - Affichage des informations de l'élève
    - Affichage du solde restant
    - Saisie du montant avec validation (entier > 0)
    - Saisie de la date (QDateEdit, aujourd'hui par défaut)
    - Sélection du mode de paiement
    - Avertissement si montant > solde
    - Validation UI pour le confort utilisateur
    """
    
    def __init__(self, payment_service: PaymentService, student_service: StudentService, 
                 student_id: int, parent=None) -> None:
        """
        Initialise le dialogue de paiement.
        
        Args:
            payment_service: Instance du service pour les opérations de paiement
            student_service: Instance du service pour récupérer les infos élève
            student_id: Identifiant de l'élève concerné
            parent: Widget parent (optionnel)
        """
        super().__init__(parent)
        
        self.payment_service = payment_service
        self.student_service = student_service
        self.student_id = student_id
        
        # Configuration de la fenêtre
        self.setWindowTitle("Enregistrer un paiement")
        self.setMinimumSize(400, 350)
        
        # Création de l'interface
        self._create_ui()
        
        # Chargement des données de l'élève
        self._load_student_data()
    
    def _create_ui(self) -> None:
        """
        Crée l'interface utilisateur du dialogue.
        
        Crée :
        - Section informations de l'élève
        - Section solde restant
        - Formulaire de paiement (montant, date, mode)
        - Boutons Valider / Annuler
        """
        # Layout principal
        layout = QVBoxLayout(self)
        
        # ===== Section : Informations de l'élève =====
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout(info_frame)
        
        self.nom_label = QLabel()
        nom_font = self.nom_label.font()
        nom_font.setPointSize(12)
        nom_font.setBold(True)
        self.nom_label.setFont(nom_font)
        info_layout.addWidget(self.nom_label)
        
        self.classe_label = QLabel()
        info_layout.addWidget(self.classe_label)
        
        layout.addWidget(info_frame)
        
        # ===== Section : Solde restant =====
        solde_layout = QHBoxLayout()
        solde_label = QLabel("Solde restant :")
        self.solde_value_label = QLabel()
        solde_font = self.solde_value_label.font()
        solde_font.setPointSize(14)
        solde_font.setBold(True)
        self.solde_value_label.setFont(solde_font)
        self.solde_value_label.setStyleSheet("color: blue;")
        solde_layout.addWidget(solde_label)
        solde_layout.addWidget(self.solde_value_label)
        solde_layout.addStretch()
        layout.addLayout(solde_layout)
        
        # Séparateur
        separator = QLabel("─" * 50)
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)
        
        # ===== Section : Formulaire de paiement =====
        form_layout = QVBoxLayout()
        
        # Montant
        montant_layout = QHBoxLayout()
        montant_label = QLabel("Montant (FCFA) :")
        montant_label.setMinimumWidth(120)
        self.montant_input = QLineEdit()
        self.montant_input.setPlaceholderText("Ex: 10000")
        # QIntValidator : n'accepte que des entiers
        # Pourquoi QIntValidator : Empêche l'utilisateur de saisir des lettres ou des décimales
        self.montant_input.setValidator(QIntValidator(1, 999999999))
        montant_layout.addWidget(montant_label)
        montant_layout.addWidget(self.montant_input)
        form_layout.addLayout(montant_layout)
        
        # Date
        date_layout = QHBoxLayout()
        date_label = QLabel("Date :")
        date_label.setMinimumWidth(120)
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        # Format d'affichage de la date
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_input)
        form_layout.addLayout(date_layout)
        
        # Mode de paiement
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode :")
        mode_label.setMinimumWidth(120)
        self.mode_input = QComboBox()
        self.mode_input.addItems(PaymentService.MODES_AUTORISES)
        # Capitalisation de la première lettre pour l'affichage
        for i in range(self.mode_input.count()):
            mode = self.mode_input.itemText(i)
            self.mode_input.setItemText(i, mode.capitalize())
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_input)
        form_layout.addLayout(mode_layout)
        
        # Avertissement (visible si montant > solde)
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: red;")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        form_layout.addWidget(self.warning_label)
        
        layout.addLayout(form_layout)
        
        # Espaceur
        layout.addStretch()
        
        # ===== Boutons =====
        buttons_layout = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setMinimumHeight(35)
        # Connexion signal -> slot : clic -> fermeture sans validation
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        
        self.btn_validate = QPushButton("Valider")
        self.btn_validate.setMinimumHeight(35)
        self.btn_validate.setStyleSheet("background-color: #4CAF50; color: white;")
        # Connexion signal -> slot : clic -> validation et enregistrement
        self.btn_validate.clicked.connect(self._on_validate_clicked)
        buttons_layout.addWidget(self.btn_validate)
        
        layout.addLayout(buttons_layout)
        
        # Connexion signal -> slot : changement de montant -> vérification solde
        self.montant_input.textChanged.connect(self._on_montant_changed)
    
    def _load_student_data(self) -> None:
        """
        Charge et affiche les données de l'élève.
        
        Récupère les informations de l'élève et son solde restant,
        puis remplit les labels correspondants.
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
            self.classe_label.setText(f"Classe : {student['nom_classe']} | Année : {student['annee_scolaire']}")
            
            # Affichage du solde restant
            solde = student['solde']
            self.solde_value_label.setText(f"{solde:,} FCFA")
            
            # Couleur du solde selon le statut
            if solde == 0:
                self.solde_value_label.setStyleSheet("color: green; font-weight: bold;")
            elif solde > 0:
                self.solde_value_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.solde_value_label.setStyleSheet("color: red; font-weight: bold;")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des données : {str(e)}")
            self.reject()
    
    @handle_slot_errors
    def _on_montant_changed(self) -> None:
        """
        Gère le changement de montant.
        
        Affiche un avertissement si le montant dépasse le solde restant.
        
        Pourquoi textChanged.connect : Permet de donner un feedback immédiat
        à l'utilisateur pendant la saisie.
        """
        montant_text = self.montant_input.text()
        
        if not montant_text:
            self.warning_label.hide()
            return
        
        try:
            montant = int(montant_text)
            solde = int(self.solde_value_label.text().replace(" FCFA", "").replace(",", ""))
            
            if montant > solde:
                self.warning_label.setText(
                    f"Attention : Le montant ({montant:,} FCFA) dépasse le solde restant ({solde:,} FCFA)."
                )
                self.warning_label.show()
            else:
                self.warning_label.hide()
                
        except ValueError:
            self.warning_label.hide()
    
    @handle_slot_errors
    def _on_validate_clicked(self) -> None:
        """
        Gère le clic sur le bouton Valider.
        
        Valide les données UI pour le confort utilisateur, puis appelle
        le service pour l'enregistrement avec validation métier réelle.
        
        Pourquoi deux niveaux de validation :
        - Validation UI : Confort utilisateur (feedback immédiat)
        - Validation service : Règle métier réelle (authentique)
        """
        # ===== Validation UI (confort utilisateur) =====
        montant_text = self.montant_input.text()
        if not montant_text:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un montant.")
            self.montant_input.setFocus()
            return
        
        try:
            montant = int(montant_text)
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le montant doit être un entier.")
            self.montant_input.setFocus()
            return
        
        if montant <= 0:
            QMessageBox.warning(self, "Erreur", "Le montant doit être strictement positif.")
            self.montant_input.setFocus()
            return
        
        # Récupération de la date
        date_qdate = self.date_input.date()
        date_paiement = date_qdate.toString("yyyy-MM-dd")
        
        # Récupération du mode (en minuscules pour le service)
        mode_index = self.mode_input.currentIndex()
        mode = PaymentService.MODES_AUTORISES[mode_index]
        
        # ===== Appel du service (validation métier réelle) =====
        try:
            paiement = self.payment_service.enregistrer_paiement(
                eleve_id=self.student_id,
                montant=montant,
                date_paiement=date_paiement,
                mode=mode
            )
            
            # Message de succès
            QMessageBox.information(
                self,
                "Succès",
                f"Paiement enregistré avec succès !\n\n"
                f"Numéro de reçu : {paiement['numero_recu']}\n"
                f"Montant : {paiement['montant']:,} FCFA\n"
                f"Solde après : {paiement['solde_apres']:,} FCFA"
            )
            
            # Fermeture du dialogue avec QDialog.Accepted
            self.accept()
            
        except ValidationError as e:
            QMessageBox.warning(self, "Erreur de validation", e.message)
            
        except NotFoundError as e:
            QMessageBox.warning(self, "Non trouvé", e.message)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {str(e)}")
