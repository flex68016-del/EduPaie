# =============================================================================
# students_view.py - Vue de la liste des élèves
# =============================================================================
# Rôle : QWidget affichant la liste des élèves avec recherche, filtre et actions.
# =============================================================================
# Ce fichier utilise :
# - PySide6 pour les widgets Qt (QTableWidget, QComboBox, QLineEdit, QPushButton)
# - services.student_service pour la logique métier
# - services.exceptions pour la gestion des erreurs
# - ui.student_form pour le formulaire d'ajout/modification
# =============================================================================
# Ce fichier est utilisé par :
# - ui.main_window pour afficher la page des élèves
# =============================================================================

import sys
from pathlib import Path
from typing import Optional

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QMenu, QFrame
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen
from edupaie.services.student_service import StudentService
from edupaie.services.payment_service import PaymentService
from edupaie.data.database import Database
from edupaie.services.exceptions import ValidationError, NotFoundError, BusinessRuleError
from edupaie.ui.student_form import StudentForm
from edupaie.ui.student_detail import StudentDetail
from edupaie.ui.class_dialog import ClassDialog
from edupaie.ui.error_handler import handle_slot_errors
from edupaie.ui.theme import (
    STATUS, format_fcfa, TEXT, TEXT_MUTED, TEXT_SUBTLE,
    SURFACE, BG_APP, BORDER, HOVER_ROW, ACCENT, ACCENT_2,
    add_shadow, refresh_style
)
from edupaie.ui.icons import icon


class StudentsView(QWidget):
    """
    Vue de la liste des élèves avec recherche, filtre et actions CRUD.

    Responsabilité : Afficher la liste des élèves dans un tableau, permettre la recherche
    par texte, le filtrage par classe, et les actions d'ajout, modification et suppression.

    Pourquoi QTableWidget : Widget simple pour afficher des données tabulaires
    sans avoir besoin d'un modèle personnalisé (suffisant pour cette fonctionnalité).

    Fonctionnalités :
    - Liste des élèves avec colonnes : nom, prénom, classe, total dû, payé, solde, statut
    - Recherche en temps réel par nom/prénom
    - Filtrage par classe
    - Actions : Ajouter, Modifier, Supprimer
    - Double-clic pour ouvrir la fiche détaillée
    - Signal payment_made pour notifier le tableau de bord après modifications

    Signaux :
    - payment_made : Émis après qu'un paiement a été enregistré,
                     un élève a été ajouté, modifié ou supprimé
    """
    
    # Signal émis après un paiement
    # Pourquoi Signal : Permet de notifier le tableau de bord pour rafraîchissement
    payment_made = Signal()
    
    def __init__(self, student_service: StudentService, payment_service: PaymentService = None) -> None:
        """
        Initialise la vue des élèves.
        
        Args:
            student_service: Instance du service pour les opérations métier
            payment_service: Instance du service pour les paiements (optionnel)
        """
        super().__init__()
        
        self.student_service = student_service
        self.payment_service = payment_service
        self.current_students = []  # Liste des élèves actuellement affichés
        
        # Création de l'interface
        self._create_ui()
        
        # Chargement initial des données
        self._load_students()
    
    def _create_ui(self) -> None:
        """
        Crée l'interface utilisateur premium de la vue.
        
        Crée :
        - En-tête avec titre, sous-titre et bouton d'ajout
        - Barre d'outils avec recherche, filtre classe, filtre statut, boutons modifier/supprimer
        - Tableau des élèves dans une carte arrondie
        - Menu contextuel (clic droit)
        """
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # ===== Section : En-tête =====
        header_layout = QHBoxLayout()
        
        # Titre et sous-titre
        title_layout = QVBoxLayout()
        
        title_label = QLabel("Élèves")
        title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {TEXT};")
        title_layout.addWidget(title_label)
        
        # Sous-titre avec nombre d'élèves (sera mis à jour dynamiquement)
        self.subtitle_label = QLabel("0 élèves")
        self.subtitle_label.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        title_layout.addWidget(self.subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Bouton "Ajouter un élève"
        self.btn_add = QPushButton("+ Ajouter un élève")
        self.btn_add.setIcon(icon("plus", "#FFFFFF", 16))
        self.btn_add.setProperty("button_type", "primary")
        self.btn_add.clicked.connect(self._on_add_clicked)
        header_layout.addWidget(self.btn_add)
        
        layout.addLayout(header_layout)
        
        # ===== Section : Barre d'outils =====
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)
        
        # Champ de recherche large avec icône intégrée
        search_container = QFrame()
        search_container.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 0, 12, 0)
        search_layout.setSpacing(8)
        
        search_icon = QLabel()
        search_icon.setPixmap(icon("search", TEXT_MUTED, 20).pixmap(20, 20))
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un élève...")
        self.search_input.setFrame(False)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                padding: 8px 0;
                font-size: 13px;
                color: {TEXT};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        
        toolbar_layout.addWidget(search_container, stretch=1)
        
        # Filtre par classe
        self.classe_filter = QComboBox()
        self.classe_filter.setMinimumWidth(150)
        self.classe_filter.setFixedHeight(40)
        self._load_classes_filter()
        self.classe_filter.currentIndexChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self.classe_filter)
        
        # Boutons "Nouvelle classe" et "Supprimer classe"
        class_buttons_layout = QHBoxLayout()
        class_buttons_layout.setSpacing(8)
        
        self.btn_add_class = QPushButton(icon("plus", TEXT_MUTED, 16), "")
        self.btn_add_class.setFixedSize(40, 40)
        self.btn_add_class.setProperty("button_type", "ghost")
        self.btn_add_class.setToolTip("Nouvelle classe")
        self.btn_add_class.clicked.connect(self._on_add_class_clicked)
        class_buttons_layout.addWidget(self.btn_add_class)
        
        self.btn_delete_class = QPushButton(icon("trash", TEXT_MUTED, 16), "")
        self.btn_delete_class.setFixedSize(40, 40)
        self.btn_delete_class.setProperty("button_type", "ghost")
        self.btn_delete_class.setToolTip("Supprimer la classe sélectionnée")
        self.btn_delete_class.clicked.connect(self._on_delete_class_clicked)
        class_buttons_layout.addWidget(self.btn_delete_class)
        
        toolbar_layout.addLayout(class_buttons_layout)
        
        # Filtre par statut (chips)
        self.filter_tous = QPushButton("Tous")
        self.filter_tous.setCheckable(True)
        self.filter_tous.setChecked(True)
        self.filter_tous.setProperty("filter_chip", True)
        self.filter_tous.setProperty("active", True)
        self.filter_tous.clicked.connect(lambda: self._on_filter_chip("Tous"))
        toolbar_layout.addWidget(self.filter_tous)
        
        self.filter_soldes = QPushButton("Soldés")
        self.filter_soldes.setCheckable(True)
        self.filter_soldes.setProperty("filter_chip", True)
        self.filter_soldes.setProperty("active", False)
        self.filter_soldes.clicked.connect(lambda: self._on_filter_chip("Soldé"))
        toolbar_layout.addWidget(self.filter_soldes)
        
        self.filter_partiels = QPushButton("Partiels")
        self.filter_partiels.setCheckable(True)
        self.filter_partiels.setProperty("filter_chip", True)
        self.filter_partiels.setProperty("active", False)
        self.filter_partiels.clicked.connect(lambda: self._on_filter_chip("Partiellement payé"))
        toolbar_layout.addWidget(self.filter_partiels)
        
        self.filter_non_payes = QPushButton("Non payés")
        self.filter_non_payes.setCheckable(True)
        self.filter_non_payes.setProperty("filter_chip", True)
        self.filter_non_payes.setProperty("active", False)
        self.filter_non_payes.clicked.connect(lambda: self._on_filter_chip("Non payé"))
        toolbar_layout.addWidget(self.filter_non_payes)
        
        toolbar_layout.addStretch()
        
        # Boutons Modifier et Supprimer (icônes)
        self.btn_edit = QPushButton(icon("edit", TEXT_MUTED, 20), "")
        self.btn_edit.setFixedSize(40, 40)
        self.btn_edit.setProperty("button_type", "ghost")
        self.btn_edit.setEnabled(False)
        self.btn_edit.setToolTip("Modifier")
        self.btn_edit.clicked.connect(self._on_edit_clicked)
        toolbar_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton(icon("trash", TEXT_MUTED, 20), "")
        self.btn_delete.setFixedSize(40, 40)
        self.btn_delete.setProperty("button_type", "ghost")
        self.btn_delete.setEnabled(False)
        self.btn_delete.setToolTip("Supprimer")
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        toolbar_layout.addWidget(self.btn_delete)
        
        layout.addLayout(toolbar_layout)
        
        # ===== Section : Tableau des élèves dans une carte arrondie =====
        table_card = QFrame()
        table_card.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
        """)
        add_shadow(table_card)
        
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Élève", "Classe", "Total dû", "Payé", "Solde", "Statut"])
        
        # Configuration du tableau premium
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)  # Ligne 56 px premium
        
        # Ajustement des colonnes
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Élève
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Classe
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Total dû
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Payé
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Solde
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        
        table_layout.addWidget(self.table)
        layout.addWidget(table_card)
        
        # Appliquer le style premium
        self._apply_premium_style()
        
        # Connexion signal -> slot : sélection changée -> activation/désactivation boutons
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Connexion signal -> slot : double-clic -> ouverture fiche détaillée
        self.table.itemDoubleClicked.connect(self._on_double_clicked)
        
        # Menu contextuel (clic droit)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
    
    def _apply_premium_style(self) -> None:
        """
        Applique le style premium aux widgets.
        """
        # Style des chips de filtre
        chip_style = f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {BORDER};
                border-radius: 999px;
                color: {TEXT_MUTED};
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {BG_APP};
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT}, stop:1 {ACCENT_2});
                color: white;
                border: none;
            }}
        """
        
        self.filter_tous.setStyleSheet(chip_style)
        self.filter_soldes.setStyleSheet(chip_style)
        self.filter_partiels.setStyleSheet(chip_style)
        self.filter_non_payes.setStyleSheet(chip_style)
        
        refresh_style(self.filter_tous)
        refresh_style(self.filter_soldes)
        refresh_style(self.filter_partiels)
        refresh_style(self.filter_non_payes)
        
        # Style du filtre classe
        class_filter_style = f"""
            QComboBox {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                color: {TEXT};
            }}
            QComboBox:hover {{
                border: 1px solid {ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """
        self.classe_filter.setStyleSheet(class_filter_style)
        
        # Style des boutons d'action
        refresh_style(self.btn_add)
        refresh_style(self.btn_add_class)
        refresh_style(self.btn_edit)
        refresh_style(self.btn_delete)
        
        # Style du tableau
        table_style = f"""
            QTableWidget {{
                background: {SURFACE};
                border: none;
                gridline-color: {BORDER};
                selection-background-color: {HOVER_ROW};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {BORDER};
            }}
            QTableWidget::item:selected {{
                background: {HOVER_ROW};
                color: {TEXT};
            }}
            QHeaderView::section {{
                background: {SURFACE};
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 12px 8px;
                font-size: 9px;
                font-weight: bold;
                color: {TEXT_SUBTLE};
                text-transform: uppercase;
            }}
        """
        self.table.setStyleSheet(table_style)
    
    def _load_classes_filter(self) -> None:
        """
        Charge la liste des classes dans le filtre.
        
        Ajoute une option "Toutes les classes" en première position pour permettre
        d'afficher tous les élèves sans filtre.
        """
        try:
            classes = self.student_service.list_classes()
            self.classe_filter.clear()
            
            # Option "Toutes les classes"
            self.classe_filter.addItem("Toutes les classes", -1)
            
            # Ajout des classes
            for classe in classes:
                self.classe_filter.addItem(classe['nom'], classe['id'])
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des classes : {str(e)}")
    
    def _get_active_filter(self) -> str:
        """
        Retourne le filtre de statut actuellement actif.
        
        Returns:
            Le statut actif ("Tous", "Soldé", "Partiellement payé", "Non payé").
        """
        if self.filter_tous.isChecked():
            return "Tous"
        elif self.filter_soldes.isChecked():
            return "Soldé"
        elif self.filter_partiels.isChecked():
            return "Partiellement payé"
        elif self.filter_non_payes.isChecked():
            return "Non payé"
        return "Tous"
    
    def _on_filter_chip(self, statut: str) -> None:
        """
        Gère le clic sur un chip de filtre de statut.
        
        Args:
            statut: Statut sélectionné ("Tous", "Soldé", "Partiellement payé", "Non payé").
        """
        # Mettre à jour l'état des chips
        self.filter_tous.setProperty("active", statut == "Tous")
        self.filter_soldes.setProperty("active", statut == "Soldé")
        self.filter_partiels.setProperty("active", statut == "Partiellement payé")
        self.filter_non_payes.setProperty("active", statut == "Non payé")
        
        self.filter_tous.setChecked(statut == "Tous")
        self.filter_soldes.setChecked(statut == "Soldé")
        self.filter_partiels.setChecked(statut == "Partiellement payé")
        self.filter_non_payes.setChecked(statut == "Non payé")
        
        refresh_style(self.filter_tous)
        refresh_style(self.filter_soldes)
        refresh_style(self.filter_partiels)
        refresh_style(self.filter_non_payes)
        
        # Rafraîchir le tableau
        self._load_students()
    
    def _on_add_class_clicked(self) -> None:
        """
        Gère le clic sur le bouton "Nouvelle classe".
        
        Ouvre le dialogue pour créer une nouvelle classe.
        """
        dialog = ClassDialog(self.student_service, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Rafraîchir le filtre de classe
            self._load_classes_filter()
    
    def _on_delete_class_clicked(self) -> None:
        """
        Gère le clic sur le bouton "Supprimer classe".
        
        Ouvre le dialogue pour supprimer la classe sélectionnée.
        """
        classe_id = self.classe_filter.currentData()
        if classe_id == 0:
            # Aucune classe sélectionnée (0 correspond à "Toutes")
            from edupaie.ui.toast import show_toast
            show_toast("Veuillez sélectionner une classe à supprimer", parent=self)
            return
        
        dialog = ClassDialog(self.student_service, classe_id=classe_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Rafraîchir le filtre de classe
            self._load_classes_filter()
            # Rafraîchir le tableau des élèves
            self._load_students()
    
    def _show_context_menu(self, pos: QPoint) -> None:
        """
        Affiche le menu contextuel au clic droit.
        
        Args:
            pos: Position du clic dans le tableau.
        """
        # Vérifier qu'une ligne est sélectionnée
        if not self.table.selectedItems():
            return
        
        # Créer le menu contextuel
        menu = QMenu(self)
        
        action_detail = menu.addAction("Voir la fiche")
        action_detail.setIcon(icon("eye", TEXT, 16))
        
        menu.addSeparator()
        
        action_payment = menu.addAction("Nouveau paiement")
        action_payment.setIcon(icon("wallet", TEXT, 16))
        
        menu.addSeparator()
        
        action_edit = menu.addAction("Modifier")
        action_edit.setIcon(icon("edit", TEXT, 16))
        
        action_delete = menu.addAction("Supprimer")
        action_delete.setIcon(icon("trash", TEXT, 16))
        
        # Afficher le menu et récupérer l'action sélectionnée
        action = menu.exec(self.table.mapToGlobal(pos))
        
        # Exécuter l'action correspondante
        if action == action_detail:
            self._on_double_clicked(self.table.currentItem())
        elif action == action_payment:
            self._on_payment_clicked()
        elif action == action_edit:
            self._on_edit_clicked()
        elif action == action_delete:
            self._on_delete_clicked()
    
    def _on_payment_clicked(self) -> None:
        """
        Gère le clic sur "Nouveau paiement" dans le menu contextuel.
        
        Ouvre la fiche détaillée de l'élève, qui contient le bouton de paiement.
        """
        self._on_double_clicked(self.table.currentItem())
    
    def _load_students(self) -> None:
        """
        Charge et affiche la liste des élèves selon les filtres actuels.
        
        Cette méthode :
        1. Récupère le texte de recherche, la classe et le statut sélectionnés
        2. Appelle le service pour rechercher les élèves avec solde et statut
        3. Remplit le tableau avec les résultats
        4. Met à jour le sous-titre avec le nombre d'élèves
        """
        try:
            # Récupération des filtres
            search_text = self.search_input.text().strip()
            classe_id = self.classe_filter.currentData()
            statut = self._get_active_filter()
            
            # Si classe_id est -1, None (pas de filtre)
            if classe_id == -1:
                classe_id = None
            
            # Si statut est "Tous", None (pas de filtre)
            if statut == "Tous":
                statut = None
            
            # Recherche des élèves avec solde et statut
            students = self.student_service.search_students_with_solde(search_text, classe_id, statut)
            
            # Stockage pour utilisation ultérieure
            self.current_students = students
            
            # Mise à jour du sous-titre
            self.subtitle_label.setText(f"{len(students)} élève{'s' if len(students) != 1 else ''}")
            
            # Remplissage du tableau
            self._populate_table(students)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des élèves : {str(e)}")
    
    def _populate_table(self, students: list) -> None:
        """
        Remplit le tableau avec la liste des élèves.
        
        Args:
            students: Liste d'élèves à afficher
        
        Pourquoi désactiver le tri pendant le remplissage : Évite les problèmes
        de performance et de tri incorrect pendant l'ajout des lignes.
        """
        # Désactivation du tri pendant le remplissage
        self.table.setSortingEnabled(False)
        
        # Vidage du tableau
        self.table.setRowCount(0)
        
        # Ajout des lignes
        for row, student in enumerate(students):
            self.table.insertRow(row)
            
            # Élève (nom complet)
            nom_complet = f"{student['prenom']} {student['nom']}"
            eleve_item = QTableWidgetItem(nom_complet)
            eleve_item.setData(Qt.ItemDataRole.UserRole, student['id'])  # Stocke l'ID
            self.table.setItem(row, 0, eleve_item)
            
            # Classe
            classe_item = QTableWidgetItem(student['nom_classe'])
            self.table.setItem(row, 1, classe_item)
            
            # Total dû
            total_item = QTableWidgetItem(format_fcfa(student['total_du']))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, total_item)
            
            # Payé
            total_paye = student.get('total_paye', 0)
            paye_item = QTableWidgetItem(format_fcfa(total_paye))
            paye_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, paye_item)
            
            # Solde (en rouge si positif)
            solde_item = QTableWidgetItem(format_fcfa(student['solde']))
            solde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if student['solde'] > 0:
                solde_item.setForeground(QColor("#991B1B"))  # Rouge foncé pour le solde restant
            self.table.setItem(row, 4, solde_item)
            
            # Statut avec couleur (fond ET texte pour contraste WCAG)
            statut = student['statut']
            statut_colors = STATUS.get(statut, {"bg": "#FFFFFF", "fg": TEXT})
            statut_item = QTableWidgetItem(statut)
            statut_item.setBackground(QColor(statut_colors["bg"]))
            statut_item.setForeground(QColor(statut_colors["fg"]))
            statut_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            font = statut_item.font()
            font.setBold(True)
            statut_item.setFont(font)
            self.table.setItem(row, 5, statut_item)
            
            # Statut avec couleur (fond ET texte pour contraste WCAG)
            statut = student['statut']
            statut_colors = STATUS.get(statut, {"bg": "#FFFFFF", "fg": TEXT})
            statut_item = QTableWidgetItem(statut)
            statut_item.setBackground(QColor(statut_colors["bg"]))
            statut_item.setForeground(QColor(statut_colors["fg"]))
            statut_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            font = statut_item.font()
            font.setBold(True)
            statut_item.setFont(font)
            self.table.setItem(row, 6, statut_item)
        
        # Réactivation du tri
        self.table.setSortingEnabled(True)
    
    @handle_slot_errors
    def _on_search_changed(self, texte: str = "") -> None:
        """
        Gère le changement de texte dans le champ de recherche.
        
        Appelé à chaque frappe dans le champ de recherche pour filtrer
        la liste des élèves en temps réel.
        
        Args:
            texte: Le texte saisi dans le champ de recherche (émis par textChanged)
        
        Pourquoi textChanged.connect : Fournit un filtrage instantané sans
        avoir besoin d'appuyer sur un bouton "Rechercher".
        """
        self._load_students()
    
    @handle_slot_errors
    def _on_filter_changed(self, index: int) -> None:
        """
        Gère le changement de sélection dans le filtre par classe ou statut.
        
        Args:
            index: L'index sélectionné dans le QComboBox (émis par currentIndexChanged)
        
        Appelé quand l'utilisateur change la classe ou le statut dans le filtre pour
        mettre à jour la liste des élèves affichés.
        """
        self._load_students()
    
    def _on_selection_changed(self) -> None:
        """
        Gère le changement de sélection dans le tableau.
        
        Active ou désactive les boutons Modifier et Supprimer selon
        qu'une ligne est sélectionnée ou non.
        
        Pourquoi itemSelectionChanged.connect : Permet de désactiver les boutons
        quand aucune ligne n'est sélectionnée, évitant les erreurs.
        """
        has_selection = len(self.table.selectedItems()) > 0
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
    
    @handle_slot_errors
    def _on_add_clicked(self) -> None:
        """
        Gère le clic sur le bouton Ajouter.

        Ouvre le formulaire d'ajout en mode création (student_data=None).
        Si l'utilisateur valide, recharge la liste des élèves et notifie le tableau de bord.

        Pourquoi QDialog.exec() : Bloque la fenêtre principale tant que le formulaire
        est ouvert, garantissant une interaction cohérente.
        """
        # Création du formulaire en mode ajout
        form = StudentForm(self.student_service, student_data=None)
        # Connexion signal -> slot : élève ajouté -> propagation du signal
        # Pourquoi connecter : Permet de notifier le tableau de bord pour rafraîchissement
        form.student_changed.connect(self.payment_made.emit)

        # Ouverture du formulaire (bloquant)
        result = form.exec()

        # Si l'utilisateur a validé ( QDialog.Accepted)
        if result == QDialog.DialogCode.Accepted:
            # Rechargement de la liste
            self._load_students()
    
    @handle_slot_errors
    def _on_edit_clicked(self) -> None:
        """
        Gère le clic sur le bouton Modifier.
        
        Récupère l'élève sélectionné, ouvre le formulaire en mode modification
        avec ses données, et recharge la liste si validé.
        
        Pourquoi vérifier la sélection : Évite d'ouvrir le formulaire sans
        données si aucune ligne n'est sélectionnée.
        """
        # Récupération de la ligne sélectionnée
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un élève à modifier.")
            return
        
        # Récupération de l'ID de l'élève (stocké dans UserRole de la première colonne)
        row = self.table.currentRow()
        id_item = self.table.item(row, 0)
        student_id = id_item.data(Qt.ItemDataRole.UserRole)
        
        # Récupération des données de l'élève
        try:
            student = self.student_service.get_student(student_id)

            # Ouverture du formulaire en mode modification
            form = StudentForm(self.student_service, student_data=student)
            # Connexion signal -> slot : élève modifié -> propagation du signal
            # Pourquoi connecter : Permet de notifier le tableau de bord pour rafraîchissement
            form.student_changed.connect(self.payment_made.emit)
            result = form.exec()

            # Si l'utilisateur a validé
            if result == QDialog.DialogCode.Accepted:
                # Rechargement de la liste
                self._load_students()
                
        except NotFoundError as e:
            QMessageBox.warning(self, "Non trouvé", e.message)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification : {str(e)}")
    
    @handle_slot_errors
    def _on_delete_clicked(self) -> None:
        """
        Gère le clic sur le bouton Supprimer.
        
        Affiche une confirmation, puis supprime l'élève sélectionné.
        Recharge la liste si la suppression réussit.
        
        Pourquoi la confirmation : Empêche les suppressions accidentelles.
        Pourquoi try/except : Gère le cas où l'élève a des paiements (BusinessRuleError).
        """
        # Récupération de la ligne sélectionnée
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un élève à supprimer.")
            return
        
        # Récupération de l'ID et du nom de l'élève
        row = self.table.currentRow()
        id_item = self.table.item(row, 0)
        student_id = id_item.data(Qt.ItemDataRole.UserRole)
        nom_item = self.table.item(row, 0)
        nom = nom_item.text()
        prenom_item = self.table.item(row, 1)
        prenom = prenom_item.text()
        
        # Confirmation de suppression
        # Pourquoi QMessageBox.question : Demande confirmation à l'utilisateur
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer l'élève {nom} {prenom} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Suppression de l'élève
                self.student_service.delete_student(student_id)

                # Message de succès
                QMessageBox.information(self, "Succès", "L'élève a été supprimé avec succès.")

                # Émission du signal pour notifier le rafraîchissement
                # Pourquoi Signal : Permet au tableau de bord de se rafraîchir après suppression
                self.payment_made.emit()

                # Rechargement de la liste
                self._load_students()
                
            except NotFoundError as e:
                QMessageBox.warning(self, "Non trouvé", e.message)
            
            except BusinessRuleError as e:
                # L'élève a des paiements : afficher le message de la règle métier
                QMessageBox.warning(self, "Impossible de supprimer", e.message)
            
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression : {str(e)}")
    
    @handle_slot_errors
    def _on_double_clicked(self, item: QTableWidgetItem) -> None:
        """
        Gère le double-clic sur une ligne du tableau.
        
        Args:
            item: L'item cliqué (émis par itemDoubleClicked)
        
        Ouvre la fiche détaillée de l'élève sélectionné.
        
        Pourquoi itemDoubleClicked.connect : Permet d'ouvrir la fiche détaillée
        par un double-clic, interaction intuitive pour l'utilisateur.
        """
        # Récupération de la ligne sélectionnée
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        
        # Récupération de l'ID de l'élève
        row = self.table.currentRow()
        id_item = self.table.item(row, 0)
        student_id = id_item.data(Qt.ItemDataRole.UserRole)
        
        # Ouverture de la fiche détaillée
        try:
            detail = StudentDetail(self.student_service, student_id)
            # Connexion du signal payment_made de la fiche vers le signal local
            # Pourquoi : Quand un paiement est enregistré dans la fiche, le tableau de bord doit se rafraîchir
            detail.payment_made.connect(self.payment_made.emit)
            detail.exec()
            
            # Rechargement de la liste après fermeture de la fiche
            # Pourquoi : Si un paiement a été enregistré dans la fiche,
            # la liste doit refléter les nouvelles données (solde, statut)
            self._load_students()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture de la fiche : {str(e)}")