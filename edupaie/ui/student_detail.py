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
    QFileDialog, QFrame, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from edupaie.services.payment_service import PaymentService
from edupaie.services.student_service import StudentService
from edupaie.services.receipt_service import ReceiptService
from edupaie.ui.payment_dialog import PaymentDialog
from edupaie.ui.receipt_preview_dialog import ReceiptPreviewDialog
from edupaie.ui.error_handler import handle_slot_errors
from edupaie.ui.theme import (
    STATUS, format_fcfa, TEXT, TEXT_MUTED, TEXT_SUBTLE,
    SURFACE, BG_APP, BORDER, ACCENT, ACCENT_2,
    add_shadow, refresh_style
)
from edupaie.ui.icons import icon


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
        Crée l'interface utilisateur premium de la fiche.
        
        Crée :
        - Header avec grand avatar, nom, pastilles de classe et statut
        - 3 cartes KPI (Total dû, Payé, Solde)
        - Barre de progression du paiement
        - Tableau des paiements premium
        - Boutons d'action (Nouveau paiement, Aperçu, Enregistrer PDF, Imprimer)
        """
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # ===== Section : Header =====
        header_layout = QHBoxLayout()
        
        # Avatar grand (cercle 64 px)
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(64, 64)
        self.avatar_label.setStyleSheet(f"""
            QLabel {{
                background: {ACCENT};
                border-radius: 32px;
                color: white;
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.avatar_label)
        
        # Nom et pastilles
        name_layout = QVBoxLayout()
        
        self.nom_label = QLabel()
        self.nom_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT};")
        name_layout.addWidget(self.nom_label)
        
        pastilles_layout = QHBoxLayout()
        pastilles_layout.setSpacing(8)
        
        self.classe_label = QLabel()
        self.classe_label.setStyleSheet(f"""
            QLabel {{
                background: {BG_APP};
                color: {TEXT_MUTED};
                padding: 4px 12px;
                border-radius: 999px;
                font-size: 11px;
                font-weight: 500;
            }}
        """)
        pastilles_layout.addWidget(self.classe_label)
        
        self.statut_label = QLabel()
        self.statut_label.setStyleSheet(f"""
            QLabel {{
                padding: 4px 12px;
                border-radius: 999px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        pastilles_layout.addWidget(self.statut_label)
        
        name_layout.addLayout(pastilles_layout)
        header_layout.addLayout(name_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # ===== Section : 3 cartes KPI =====
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)
        
        # Carte Total dû
        self.card_total = self._create_kpi_card("Total dû", "0 FCFA", "#475569")
        kpi_layout.addWidget(self.card_total)
        
        # Carte Payé
        self.card_paye = self._create_kpi_card("Payé", "0 FCFA", "#16A34A")
        kpi_layout.addWidget(self.card_paye)
        
        # Carte Solde
        self.card_solde = self._create_kpi_card("Solde", "0 FCFA", "#DC2626")
        kpi_layout.addWidget(self.card_solde)
        
        layout.addLayout(kpi_layout)
        
        # ===== Section : Barre de progression =====
        progress_layout = QVBoxLayout()
        progress_label = QLabel("Progression du paiement")
        progress_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {TEXT_SUBTLE};")
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {BG_APP};
                border: none;
                border-radius: 10px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT}, stop:1 {ACCENT_2});
                border-radius: 10px;
            }}
        """)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_percentage = QLabel("0%")
        self.progress_percentage.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        self.progress_percentage.setAlignment(Qt.AlignmentFlag.AlignRight)
        progress_layout.addWidget(self.progress_percentage)
        
        layout.addLayout(progress_layout)
        
        # ===== Section : Historique des paiements =====
        history_label = QLabel("Historique des paiements")
        history_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {TEXT};")
        layout.addWidget(history_label)
        
        self.paiements_table = QTableWidget()
        self.paiements_table.setColumnCount(5)
        self.paiements_table.setHorizontalHeaderLabels([
            "N° Reçu", "Date", "Mode", "Montant", "Solde après"
        ])
        
        # Configuration du tableau premium
        self.paiements_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.paiements_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.paiements_table.setSortingEnabled(True)
        self.paiements_table.verticalHeader().setVisible(False)
        self.paiements_table.verticalHeader().setDefaultSectionSize(48)
        
        # Ajustement des colonnes
        header = self.paiements_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # Connexion signal -> slot
        self.paiements_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.paiements_table.cellDoubleClicked.connect(self._on_table_double_clicked)
        
        layout.addWidget(self.paiements_table)
        
        # ===== Boutons =====
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_new_payment = QPushButton("+ Nouveau paiement")
        self.btn_new_payment.setIcon(icon("plus", "#FFFFFF", 16))
        self.btn_new_payment.setProperty("button_type", "primary")
        self.btn_new_payment.clicked.connect(self._on_new_payment_clicked)
        buttons_layout.addWidget(self.btn_new_payment)
        
        self.btn_preview_receipt = QPushButton(icon("eye", TEXT_MUTED, 16), "Aperçu")
        self.btn_preview_receipt.setProperty("button_type", "secondary")
        self.btn_preview_receipt.setEnabled(False)
        self.btn_preview_receipt.clicked.connect(self._on_preview_receipt_clicked)
        buttons_layout.addWidget(self.btn_preview_receipt)
        
        self.btn_save_receipt = QPushButton(icon("download", TEXT_MUTED, 16), "Enregistrer")
        self.btn_save_receipt.setProperty("button_type", "secondary")
        self.btn_save_receipt.setEnabled(False)
        self.btn_save_receipt.clicked.connect(self._on_save_receipt_clicked)
        buttons_layout.addWidget(self.btn_save_receipt)
        
        self.btn_print_receipt = QPushButton(icon("printer", TEXT_MUTED, 16), "Imprimer")
        self.btn_print_receipt.setProperty("button_type", "secondary")
        self.btn_print_receipt.setEnabled(False)
        self.btn_print_receipt.clicked.connect(self._on_print_receipt_clicked)
        buttons_layout.addWidget(self.btn_print_receipt)
        
        self.btn_close = QPushButton("Fermer")
        self.btn_close.setProperty("button_type", "secondary")
        self.btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btn_close)
        
        layout.addLayout(buttons_layout)
        
        # Appliquer le style premium
        self._apply_premium_style()
    
    def _create_kpi_card(self, title: str, value: str, color: str) -> QFrame:
        """
        Crée une carte KPI premium simple.
        
        Args:
            title: Titre de la carte.
            value: Valeur initiale.
            color: Couleur de la valeur.
        
        Returns:
            QFrame configuré comme carte KPI.
        """
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED}; font-weight: 500;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 18px; color: {color}; font-weight: bold;")
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        
        # Stockage de la référence
        card.value_label = value_label
        
        return card
    
    def _apply_premium_style(self) -> None:
        """
        Applique le style premium aux widgets.
        """
        # Style du tableau
        table_style = f"""
            QTableWidget {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 12px;
                gridline-color: {BORDER};
                selection-background-color: {BG_APP};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {BORDER};
            }}
            QTableWidget::item:selected {{
                background: {BG_APP};
                color: {TEXT};
            }}
            QHeaderView::section {{
                background: {SURFACE};
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 8px;
                font-size: 9px;
                font-weight: bold;
                color: {TEXT_SUBTLE};
                text-transform: uppercase;
            }}
        """
        self.paiements_table.setStyleSheet(table_style)
        
        # Style des boutons
        refresh_style(self.btn_new_payment)
        refresh_style(self.btn_preview_receipt)
        refresh_style(self.btn_save_receipt)
        refresh_style(self.btn_print_receipt)
        refresh_style(self.btn_close)
    
    def _load_student_data(self) -> None:
        """
        Charge et affiche les données de l'élève.
        
        Récupère les informations de l'élève avec solde et statut,
        puis remplit les widgets premium et le tableau des paiements.
        """
        try:
            # Récupération des données de l'élève
            student = self.student_service.get_student_with_solde_and_statut(self.student_id)
            
            if student is None:
                QMessageBox.warning(self, "Non trouvé", "L'élève n'existe pas.")
                self.reject()
                return
            
            # Affichage du nom
            self.nom_label.setText(f"{student['prenom']} {student['nom']}")
            
            # Affichage de la classe
            self.classe_label.setText(student['nom_classe'])
            
            # Avatar avec initiales
            initiales = f"{student['prenom'][0]}{student['nom'][0]}".upper()
            self.avatar_label.setText(initiales)
            
            # Calcul du montant payé
            total_paye = student['total_du'] - student['solde']
            
            # Mise à jour des cartes KPI
            self.card_total.value_label.setText(format_fcfa(student['total_du']))
            self.card_paye.value_label.setText(format_fcfa(total_paye))
            self.card_solde.value_label.setText(format_fcfa(student['solde']))
            
            # Couleur du solde selon le montant
            if student['solde'] == 0:
                self.card_solde.value_label.setStyleSheet(f"font-size: 18px; color: #16A34A; font-weight: bold;")
            else:
                self.card_solde.value_label.setStyleSheet(f"font-size: 18px; color: #DC2626; font-weight: bold;")
            
            # Affichage du statut avec couleur (fond ET texte pour contraste WCAG)
            statut = student['statut']
            statut_colors = STATUS.get(statut, {"bg": "#FFFFFF", "fg": TEXT})
            self.statut_label.setText(statut)
            self.statut_label.setStyleSheet(f"""
                QLabel {{
                    background: {statut_colors["bg"]};
                    color: {statut_colors["fg"]};
                    padding: 4px 12px;
                    border-radius: 999px;
                    font-size: 11px;
                    font-weight: 600;
                }}
            """)
            
            # Barre de progression
            percentage = (total_paye / student['total_du'] * 100) if student['total_du'] > 0 else 0
            self.progress_bar.setValue(int(percentage))
            self.progress_percentage.setText(f"{int(percentage)}%")
            
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
                if paiement['solde_apres'] > 0:
                    solde_item.setForeground(QColor("#991B1B"))  # Rouge foncé si solde positif
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
        
        Active les boutons de reçu (Aperçu, Enregistrer, Imprimer) si une ligne
        est sélectionnée, les désactive sinon.
        
        Pourquoi itemSelectionChanged.connect : Permet d'activer/désactiver
        les boutons de reçu selon la sélection.
        """
        # Vérification si une ligne est sélectionnée
        selected_items = self.paiements_table.selectedItems()
        has_selection = len(selected_items) > 0
        
        # Activation/désactivation des boutons
        self.btn_preview_receipt.setEnabled(has_selection)
        self.btn_save_receipt.setEnabled(has_selection)
        self.btn_print_receipt.setEnabled(has_selection)
    
    @handle_slot_errors
    def _on_table_double_clicked(self, row: int, column: int) -> None:
        """
        Gère le double-clic sur une ligne du tableau des paiements.
        
        Ouvre directement l'aperçu du reçu du paiement sélectionné.
        
        Args:
            row: Index de la ligne cliquée
            column: Index de la colonne cliquée
        
        Pourquoi double-clic : Raccourci utilisateur courant pour consulter
        un élément de liste.
        """
        # Vérifier qu'il y a des paiements
        if self.paiements_table.rowCount() == 0:
            return
        
        # Vérifier que ce n'est pas la ligne "Aucun paiement"
        if self.paiements_table.item(row, 0).text() == "Aucun paiement enregistré":
            return
        
        # Ouvrir l'aperçu
        self._on_preview_receipt_clicked()
    
    @handle_slot_errors
    def _on_preview_receipt_clicked(self) -> None:
        """
        Gère le clic sur le bouton Aperçu.
        
        Ouvre le dialogue d'aperçu du reçu du paiement sélectionné.
        
        Pourquoi l'aperçu : Permet à l'utilisateur de vérifier le reçu avant
        de l'enregistrer ou de l'imprimer.
        """
        paiement_id = self._get_selected_payment_id()
        if paiement_id is None:
            return
        
        # Ouvrir le dialogue d'aperçu
        preview_dialog = ReceiptPreviewDialog(
            paiement_id,
            self.receipt_service,
            self
        )
        preview_dialog.exec()
    
    @handle_slot_errors
    def _on_save_receipt_clicked(self) -> None:
        """
        Gère le clic sur le bouton Enregistrer le PDF.
        
        Génère et enregistre directement le PDF du paiement sélectionné
        via QFileDialog.
        
        Pourquoi enregistrement direct : Pour les utilisateurs qui connaissent
        déjà le format et veulent éviter l'étape d'aperçu.
        """
        paiement_id = self._get_selected_payment_id()
        if paiement_id is None:
            return
        
        # Générer le PDF dans un fichier temporaire
        from edupaie.utils.paths import user_data_dir
        import shutil
        from pathlib import Path
        
        tmp_dir = user_data_dir() / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        temp_file = tmp_dir / f"temp_receipt_{paiement_id}.pdf"
        
        try:
            # Générer le PDF
            receipt_number = self.receipt_service.generate_receipt(paiement_id, str(temp_file))
            
            # Nom de fichier proposé
            default_name = f"Recu_{receipt_number}.pdf"
            
            # Boîte de dialogue pour choisir l'emplacement
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer le reçu",
                default_name,
                "Fichiers PDF (*.pdf)"
            )
            
            if file_path:
                shutil.copy2(temp_file, file_path)
                QMessageBox.information(self, "Succès", "Le reçu a été enregistré avec succès")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'enregistrer le reçu :\n{str(e)}"
            )
            import logging
            logging.error(f"Erreur lors de l'enregistrement du reçu : {e}", exc_info=True)
        finally:
            # Supprimer le fichier temporaire
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
    
    @handle_slot_errors
    def _on_print_receipt_clicked(self) -> None:
        """
        Gère le clic sur le bouton Imprimer.
        
        Génère et imprime directement le reçu du paiement sélectionné
        via QPrintDialog.
        
        Pourquoi impression directe : Pour les utilisateurs qui veulent
        imprimer sans passer par l'aperçu.
        """
        paiement_id = self._get_selected_payment_id()
        if paiement_id is None:
            return
        
        # Générer le PDF dans un fichier temporaire
        from edupaie.utils.paths import user_data_dir
        from pathlib import Path
        
        tmp_dir = user_data_dir() / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        temp_file = tmp_dir / f"temp_receipt_{paiement_id}.pdf"
        
        try:
            # Générer le PDF
            receipt_number = self.receipt_service.generate_receipt(paiement_id, str(temp_file))
            
            # Imprimer via le dialogue d'aperçu (le dialogue gère l'impression)
            preview_dialog = ReceiptPreviewDialog(
                paiement_id,
                self.receipt_service,
                self
            )
            # Simuler un clic sur le bouton Imprimer
            preview_dialog._print_pdf()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'imprimer le reçu :\n{str(e)}"
            )
            import logging
            logging.error(f"Erreur lors de l'impression du reçu : {e}", exc_info=True)
        finally:
            # Supprimer le fichier temporaire
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
    
    def _get_selected_payment_id(self) -> int | None:
        """
        Récupère l'ID du paiement sélectionné dans le tableau.
        
        Returns:
            L'ID du paiement sélectionné, ou None si aucune sélection.
        
        Pourquoi cette méthode : Évite la duplication de code pour récupérer
        l'ID du paiement sélectionné.
        """
        selected_items = self.paiements_table.selectedItems()
        if not selected_items:
            return None
        
        row = self.paiements_table.currentRow()
        recu_item = self.paiements_table.item(row, 0)
        
        # Vérifier que ce n'est pas la ligne "Aucun paiement"
        if recu_item.text() == "Aucun paiement enregistré":
            return None
        
        paiement_id = recu_item.data(Qt.ItemDataRole.UserRole)
        return paiement_id
    
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