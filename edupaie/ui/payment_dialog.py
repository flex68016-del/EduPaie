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
    QComboBox, QDateEdit, QPushButton, QMessageBox, QFrame,
    QFileDialog, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIntValidator, QColor
from edupaie.services.payment_service import PaymentService
from edupaie.services.student_service import StudentService
from edupaie.services.receipt_service import ReceiptService
from edupaie.ui.error_handler import handle_slot_errors
from edupaie.ui.theme import (
    format_fcfa, TEXT, TEXT_MUTED, SURFACE, BORDER,
    ACCENT, ACCENT_2, DANGER, refresh_style
)
from edupaie.ui.icons import icon
from edupaie.ui.receipt_preview_dialog import ReceiptPreviewDialog


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
    
    # Signal émis après un paiement
    # Pourquoi Signal : Permet de notifier la vue principale pour rafraîchissement
    payment_made = Signal()
    
    def __init__(self, payment_service: PaymentService, student_service: StudentService,
                 receipt_service: ReceiptService, student_id: int, parent=None) -> None:
        """
        Initialise le dialogue de paiement.
        
        Args:
            payment_service: Instance du service pour les opérations de paiement
            student_service: Instance du service pour récupérer les infos élève
            receipt_service: Instance du service pour générer les reçus PDF
            student_id: Identifiant de l'élève concerné
            parent: Widget parent (optionnel)
        """
        super().__init__(parent)
        
        self.payment_service = payment_service
        self.student_service = student_service
        self.receipt_service = receipt_service
        self.student_id = student_id
        self.dernier_paiement_id = None  # Stocke l'ID du dernier paiement pour le reçu
        
        # Configuration de la fenêtre
        self.setWindowTitle("Enregistrer un paiement")
        self.setMinimumSize(400, 350)
        
        # Création de l'interface
        self._create_ui()
        
        # Chargement des données de l'élève
        self._load_student_data()
    
    def _create_ui(self) -> None:
        """
        Crée l'interface utilisateur premium du dialogue.
        
        Crée :
        - Header avec nom de l'élève
        - Solde restant bien visible
        - Champ Montant grand (20 pt)
        - Bouton "Solder"
        - Modes de paiement en boutons segmentés
        - Date
        - Validation inline
        - Boutons Enregistrer / Annuler
        """
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # ===== Header =====
        self.nom_label = QLabel()
        self.nom_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {TEXT};")
        layout.addWidget(self.nom_label)
        
        self.classe_label = QLabel()
        self.classe_label.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        layout.addWidget(self.classe_label)
        
        # ===== Solde restant =====
        solde_frame = QFrame()
        solde_frame.setStyleSheet(f"""
            QFrame {{
                background: {BG_APP};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        solde_layout = QVBoxLayout(solde_frame)
        
        solde_title = QLabel("Solde restant")
        solde_title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {TEXT_MUTED};")
        solde_layout.addWidget(solde_title)
        
        self.solde_value_label = QLabel()
        self.solde_value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {DANGER};")
        solde_layout.addWidget(self.solde_value_label)
        
        layout.addWidget(solde_frame)
        
        # ===== Champ Montant =====
        montant_label = QLabel("Montant du paiement")
        montant_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {TEXT};")
        layout.addWidget(montant_label)
        
        montant_layout = QHBoxLayout()
        self.montant_input = QLineEdit()
        self.montant_input.setPlaceholderText("Ex: 10000")
        self.montant_input.setValidator(QIntValidator(1, 999999999))
        self.montant_input.setStyleSheet(f"""
            QLineEdit {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 20px;
                font-weight: bold;
                color: {TEXT};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {ACCENT};
            }}
        """)
        montant_layout.addWidget(self.montant_input)
        
        self.btn_solder = QPushButton("Solder")
        self.btn_solder.setProperty("button_type", "secondary")
        self.btn_solder.clicked.connect(self._on_solder_clicked)
        montant_layout.addWidget(self.btn_solder)
        
        layout.addLayout(montant_layout)
        
        # ===== Modes de paiement (boutons segmentés) =====
        mode_label = QLabel("Mode de paiement")
        mode_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {TEXT};")
        layout.addWidget(mode_label)
        
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        
        self.mode_group = QButtonGroup(self)
        
        self.mode_especes = QRadioButton("Espèces")
        self.mode_especes.setChecked(True)
        self.mode_group.addButton(self.mode_especes, 0)
        mode_layout.addWidget(self.mode_especes)
        
        self.mode_cheque = QRadioButton("Chèque")
        self.mode_group.addButton(self.mode_cheque, 1)
        mode_layout.addWidget(self.mode_cheque)
        
        self.mode_virement = QRadioButton("Virement")
        self.mode_group.addButton(self.mode_virement, 2)
        mode_layout.addWidget(self.mode_virement)
        
        self.mode_mobile = QRadioButton("Mobile money")
        self.mode_group.addButton(self.mode_mobile, 3)
        mode_layout.addWidget(self.mode_mobile)
        
        layout.addLayout(mode_layout)
        
        # ===== Date =====
        date_label = QLabel("Date du paiement")
        date_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {TEXT};")
        layout.addWidget(date_label)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        self.date_input.setMinimumHeight(40)
        self.date_input.setStyleSheet(f"""
            QDateEdit {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                color: {TEXT};
            }}
        """)
        layout.addWidget(self.date_input)
        
        # ===== Validation inline =====
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet(f"""
            QLabel {{
                background: #FEE2E2;
                color: #991B1B;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 11px;
            }}
        """)
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)
        
        # Connexion signal -> slot : changement de montant -> vérification solde
        self.montant_input.textChanged.connect(self._on_montant_changed)
        
        # Espaceur
        layout.addStretch()
        
        # ===== Boutons =====
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_validate = QPushButton("Enregistrer le paiement")
        self.btn_validate.setProperty("button_type", "primary")
        self.btn_validate.clicked.connect(self._on_validate_clicked)
        buttons_layout.addWidget(self.btn_validate)
        
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setProperty("button_type", "secondary")
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        layout.addLayout(buttons_layout)
        
        # Appliquer le style premium
        self._apply_premium_style()
    
    def _apply_premium_style(self) -> None:
        """
        Applique le style premium aux widgets.
        """
        # Style des boutons radio
        radio_style = f"""
            QRadioButton {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                color: {TEXT};
            }}
            QRadioButton:checked {{
                background: {ACCENT};
                color: white;
                border: none;
            }}
        """
        self.mode_especes.setStyleSheet(radio_style)
        self.mode_cheque.setStyleSheet(radio_style)
        self.mode_virement.setStyleSheet(radio_style)
        self.mode_mobile.setStyleSheet(radio_style)
        
        # Style des boutons
        refresh_style(self.btn_solder)
        refresh_style(self.btn_validate)
        refresh_style(self.btn_cancel)
    
    def _on_solder_clicked(self) -> None:
        """
        Remplit le champ montant avec le solde restant.
        """
        if hasattr(self, 'solde_restant'):
            self.montant_input.setText(str(self.solde_restant))
    
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
            self.nom_label.setText(f"{student['prenom']} {student['nom']}")
            self.classe_label.setText(student['nom_classe'])
            
            # Affichage du solde restant
            solde = student['solde']
            self.solde_restant = solde  # Stocker pour le bouton "Solder"
            self.solde_value_label.setText(format_fcfa(solde))
            
            # Mettre à jour le texte du bouton "Solder"
            self.btn_solder.setText(f"Solder ({format_fcfa(solde)})")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des données : {str(e)}")
            self.reject()
    
    @handle_slot_errors
    def _on_montant_changed(self, texte: str = "") -> None:
        """
        Gère le changement de montant.
        
        Affiche un avertissement si le montant dépasse le solde restant.
        """
        montant_text = self.montant_input.text()
        
        if not montant_text:
            self.warning_label.hide()
            return
        
        try:
            montant = int(montant_text)
            solde = self.solde_restant if hasattr(self, 'solde_restant') else 0
            
            if montant > solde:
                self.warning_label.setText(
                    f"Attention : Le montant ({format_fcfa(montant)}) dépasse le solde restant ({format_fcfa(solde)})."
                )
                self.warning_label.show()
            else:
                self.warning_label.hide()
                
        except ValueError:
            self.warning_label.hide()
    
    @handle_slot_errors
    def _on_validate_clicked(self) -> None:
        """
        Gère le clic sur le bouton Enregistrer.
        
        Valide les données UI pour le confort utilisateur, puis appelle
        le service pour l'enregistrement avec validation métier réelle.
        """
        # ===== Validation UI (confort utilisateur) =====
        montant_text = self.montant_input.text()
        if not montant_text:
            self.warning_label.setText("Veuillez saisir un montant.")
            self.warning_label.show()
            self.montant_input.setFocus()
            return
        
        try:
            montant = int(montant_text)
        except ValueError:
            self.warning_label.setText("Le montant doit être un entier.")
            self.warning_label.show()
            self.montant_input.setFocus()
            return
        
        if montant <= 0:
            self.warning_label.setText("Le montant doit être strictement positif.")
            self.warning_label.show()
            self.montant_input.setFocus()
            return
        
        # Récupération de la date
        date_qdate = self.date_input.date()
        date_paiement = date_qdate.toString("yyyy-MM-dd")
        
        # Récupération du mode (en minuscules pour le service)
        mode_index = self.mode_group.checkedId()
        modes = ["especes", "cheque", "virement", "mobile_money"]
        mode = modes[mode_index]
        
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
            
            # Stockage de l'ID du paiement pour générer le reçu
            self.dernier_paiement_id = paiement['id']
            
            # Émission du signal pour notifier le rafraîchissement
            self.payment_made.emit()
            
            # Proposition de générer le reçu
            self._proposer_recu()
            
        except ValidationError as e:
            self.warning_label.setText(e.message)
            self.warning_label.show()
            
        except NotFoundError as e:
            QMessageBox.warning(self, "Non trouvé", e.message)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {str(e)}")
    
    @handle_slot_errors
    def _proposer_recu(self) -> None:
        """
        Propose à l'utilisateur de générer le reçu après un paiement réussi.
        
        Présente trois options :
        - Aperçu (par défaut) : Ouvre le dialogue d'aperçu du reçu
        - Enregistrer le PDF : Enregistre directement via QFileDialog
        - Imprimer : Imprime directement via QPrintDialog
        
        Pourquoi ces trois options : L'aperçu permet de vérifier le reçu avant
        de l'enregistrer ou de l'imprimer. Les options directes sont disponibles
        pour les utilisateurs qui connaissent déjà le format.
        
        Pourquoi QDialog avec boutons personnalisés : Plus clair qu'une QMessageBox
        standard avec oui/non, l'utilisateur choisit explicitement l'action souhaitée.
        """
        # Création d'un dialogue personnalisé
        dialog = QDialog(self)
        dialog.setWindowTitle("Reçu de paiement")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        label = QLabel("Voulez-vous générer le reçu de paiement ?")
        layout.addWidget(label)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Bouton Aperçu (par défaut, primary)
        btn_preview = QPushButton("Aperçu")
        btn_preview.setProperty("variant", "primary")
        btn_preview.clicked.connect(lambda: self._ouvrir_apercu(dialog))
        buttons_layout.addWidget(btn_preview)
        
        # Bouton Enregistrer le PDF
        btn_save_pdf = QPushButton("Enregistrer le PDF")
        btn_save_pdf.setProperty("variant", "secondary")
        btn_save_pdf.clicked.connect(lambda: self._enregistrer_pdf(dialog))
        buttons_layout.addWidget(btn_save_pdf)
        
        # Bouton Imprimer
        btn_print = QPushButton("Imprimer")
        btn_print.setProperty("variant", "secondary")
        btn_print.clicked.connect(lambda: self._imprimer_recu(dialog))
        buttons_layout.addWidget(btn_print)
        
        # Bouton Passer
        btn_skip = QPushButton("Passer")
        btn_skip.setProperty("variant", "secondary")
        btn_skip.clicked.connect(dialog.accept)
        buttons_layout.addWidget(btn_skip)
        
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        
        # Affichage du dialogue
        dialog.exec()
    
    @handle_slot_errors
    def _ouvrir_apercu(self, parent_dialog: QDialog) -> None:
        """
        Ouvre le dialogue d'aperçu du reçu.
        
        Args:
            parent_dialog: Dialogue parent à fermer après l'aperçu
        
        Pourquoi fermer le parent : L'aperçu est une fenêtre modale qui
        remplace le dialogue de proposition. Une fois l'aperçu fermé,
        l'utilisateur peut continuer.
        """
        parent_dialog.accept()
        
        # Ouvrir le dialogue d'aperçu
        preview_dialog = ReceiptPreviewDialog(
            self.dernier_paiement_id,
            self.receipt_service,
            self
        )
        preview_dialog.exec()
        
        # Fermeture du dialogue de paiement après choix
        self.accept()
    
    @handle_slot_errors
    def _enregistrer_pdf(self, dialog: QDialog) -> None:
        """
        Enregistre le reçu PDF au choix de l'utilisateur.
        
        Args:
            dialog: Dialogue à fermer après enregistrement.
        
        Pourquoi QFileDialog.getSaveFileName : Permet à l'utilisateur de choisir
        le nom et l'emplacement du fichier PDF.
        
        Pourquoi dossier par défaut via utils/paths : Stocke les reçus dans un
        dossier dédié pour l'organisation (user_data_dir/reçus).
        """
        from edupaie.utils.paths import user_data_dir
        
        # Dossier par défaut pour les reçus
        receipts_dir = user_data_dir() / "reçus"
        receipts_dir.mkdir(parents=True, exist_ok=True)
        
        # Ouverture du dialogue de sauvegarde
        fichier_pdf, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le reçu",
            str(receipts_dir / f"REC-{datetime.now().year}-000001.pdf"),
            "Fichiers PDF (*.pdf)"
        )
        
        if fichier_pdf:
            try:
                # Génération du PDF
                chemin = self.receipt_service.generer_recu(self.dernier_paiement_id, fichier_pdf)
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Reçu enregistré avec succès :\n{chemin}"
                )
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du PDF : {str(e)}")
    
    @handle_slot_errors
    def _imprimer_recu(self, dialog: QDialog) -> None:
        """
        Imprime directement le reçu.
        
        Args:
            dialog: Dialogue à fermer après impression.
        
        Pourquoi approche simplifiée : PySide6 standard n'inclut pas QPdfDocument.
        Pour l'instant, génère le PDF et informe l'utilisateur qu'il peut l'imprimer
        via son lecteur PDF.
        
        Note : Une implémentation complète nécessiterait d'ajouter PySide6-Pdf
        ou d'utiliser une bibliothèque externe pour l'impression directe.
        """
        from edupaie.utils.paths import user_data_dir
        import tempfile
        
        try:
            # Génération du PDF dans le dossier reçus
            receipts_dir = user_data_dir() / "reçus"
            receipts_dir.mkdir(parents=True, exist_ok=True)
            
            paiement = self.payment_service.payment_repository.get_by_id(self.dernier_paiement_id)
            if paiement is None:
                QMessageBox.warning(self, "Non trouvé", "Le paiement n'existe pas.")
                return
            
            chemin_pdf = str(receipts_dir / f"{paiement['numero_recu']}.pdf")
            self.receipt_service.generer_recu(self.dernier_paiement_id, chemin_pdf)
            
            QMessageBox.information(
                self,
                "PDF généré",
                f"Le reçu a été généré :\n{chemin_pdf}\n\n"
                "Vous pouvez l'imprimer depuis votre lecteur PDF."
            )
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération du PDF : {str(e)}")
