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
    QHeaderView, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from edupaie.services.student_service import StudentService
from edupaie.data.database import Database
from edupaie.services.exceptions import ValidationError, NotFoundError, BusinessRuleError
from edupaie.ui.student_form import StudentForm
from edupaie.ui.student_detail import StudentDetail
from edupaie.ui.error_handler import handle_slot_errors
from edupaie.ui.theme import STATUS_COLORS


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
    
    def __init__(self, student_service: StudentService) -> None:
        """
        Initialise la vue des élèves.
        
        Args:
            student_service: Instance du service pour les opérations métier
        """
        super().__init__()
        
        self.student_service = student_service
        self.current_students = []  # Liste des élèves actuellement affichés
        
        # Création de l'interface
        self._create_ui()
        
        # Chargement initial des données
        self._load_students()
    
    def _create_ui(self) -> None:
        """
        Crée l'interface utilisateur de la vue.
        
        Crée :
        - Barre de recherche et filtre par classe
        - Tableau des élèves
        - Boutons d'action (Ajouter, Modifier, Supprimer)
        """
        # Layout principal
        layout = QVBoxLayout(self)
        
        # ===== Section : Recherche et filtre =====
        filter_layout = QHBoxLayout()
        
        # Champ de recherche
        search_label = QLabel("Rechercher :")
        search_label.setStyleSheet("color: black;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom ou prénom...")
        # Couleur du placeholder et du texte en noir pour lisibilité
        palette = self.search_input.palette()
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        self.search_input.setPalette(palette)
        # Connexion signal -> slot : texte changé -> filtrage en temps réel
        # Pourquoi textChanged.connect : Réagit à chaque frappe pour un filtrage instantané
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(search_label)
        filter_layout.addWidget(self.search_input)
        
        # Filtre par classe
        classe_label = QLabel("Classe :")
        classe_label.setStyleSheet("color: black;")
        self.classe_filter = QComboBox()
        self._load_classes_filter()
        # Couleur du texte : noir quand fermé, blanc dans la liste déroulante
        self.classe_filter.setStyleSheet("""
            QComboBox { color: black; }
            QComboBox QAbstractItemView { color: white; background-color: #2c3e50; }
        """)
        # Connexion signal -> slot : sélection changée -> filtrage
        self.classe_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(classe_label)
        filter_layout.addWidget(self.classe_filter)
        
        # Filtre par statut
        statut_label = QLabel("Statut :")
        statut_label.setStyleSheet("color: black;")
        self.statut_filter = QComboBox()
        self._load_statut_filter()
        # Couleur du texte : noir quand fermé, blanc dans la liste déroulante
        self.statut_filter.setStyleSheet("""
            QComboBox { color: black; }
            QComboBox QAbstractItemView { color: white; background-color: #2c3e50; }
        """)
        # Connexion signal -> slot : sélection changée -> filtrage
        self.statut_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(statut_label)
        filter_layout.addWidget(self.statut_filter)
        
        layout.addLayout(filter_layout)
        
        # ===== Section : Tableau des élèves =====
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Nom", "Prénom", "Classe", "Total dû (FCFA)", "Payé (FCFA)", "Solde (FCFA)", "Statut"])
        
        # Configuration du tableau
        # Pourquoi setSelectionBehavior : Sélectionne la ligne entière au lieu de la cellule
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Pourquoi setSelectionMode : Une seule ligne sélectionnable à la fois
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        # Pourquoi setAlternatingRowColors : Améliore la lisibilité avec des couleurs alternées
        self.table.setAlternatingRowColors(True)
        # Pourquoi setSortingEnabled : Permet le tri par colonne en cliquant sur l'en-tête
        self.table.setSortingEnabled(True)
        
        # Ajustement des colonnes
        header = self.table.horizontalHeader()
        # Pourquoi setSectionResizeMode : Ajuste automatiquement la largeur des colonnes
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Nom : extensible
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Prénom : extensible
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Classe : auto
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Total : auto
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Payé : auto
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Solde : auto
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Statut : auto
        
        layout.addWidget(self.table)
        
        # ===== Section : Boutons d'action =====
        buttons_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Ajouter")
        self.btn_add.setMinimumHeight(35)
        # Couleur du texte en noir pour lisibilité (override stylesheet global)
        self.btn_add.setStyleSheet("color: black;")
        # Connexion signal -> slot : clic -> ouverture formulaire d'ajout
        self.btn_add.clicked.connect(self._on_add_clicked)
        
        self.btn_edit = QPushButton("Modifier")
        self.btn_edit.setMinimumHeight(35)
        self.btn_edit.setEnabled(False)  # Désactivé tant qu'aucune sélection
        # Couleur du texte en noir pour lisibilité (override stylesheet global)
        self.btn_edit.setStyleSheet("color: black;")
        # Connexion signal -> slot : clic -> ouverture formulaire de modification
        self.btn_edit.clicked.connect(self._on_edit_clicked)
        
        self.btn_delete = QPushButton("Supprimer")
        self.btn_delete.setMinimumHeight(35)
        self.btn_delete.setEnabled(False)  # Désactivé tant qu'aucune sélection
        # Couleur du texte en noir pour lisibilité (override stylesheet global)
        self.btn_delete.setStyleSheet("color: black;")
        # Connexion signal -> slot : clic -> suppression de l'élève sélectionné
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        
        buttons_layout.addWidget(self.btn_add)
        buttons_layout.addWidget(self.btn_edit)
        buttons_layout.addWidget(self.btn_delete)
        layout.addLayout(buttons_layout)
        
        # Connexion signal -> slot : sélection changée -> activation/désactivation boutons
        # Pourquoi itemSelectionChanged : Réagit quand l'utilisateur sélectionne/désélectionne une ligne
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Connexion signal -> slot : double-clic -> ouverture fiche détaillée
        # Pourquoi itemDoubleClicked : Permet d'ouvrir la fiche détaillée par double-clic
        self.table.itemDoubleClicked.connect(self._on_double_clicked)
    
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
    
    def _load_statut_filter(self) -> None:
        """
        Charge les options du filtre par statut.
        
        Ajoute une option "Tous les statuts" en première position pour permettre
        d'afficher tous les élèves sans filtre de statut.
        """
        self.statut_filter.clear()
        
        # Option "Tous les statuts"
        self.statut_filter.addItem("Tous les statuts", None)
        
        # Options de statut
        self.statut_filter.addItem("Soldé", "Soldé")
        self.statut_filter.addItem("Partiellement payé", "Partiellement payé")
        self.statut_filter.addItem("Non payé", "Non payé")
    
    def _load_students(self) -> None:
        """
        Charge et affiche la liste des élèves selon les filtres actuels.
        
        Cette méthode :
        1. Récupère le texte de recherche, la classe et le statut sélectionnés
        2. Appelle le service pour rechercher les élèves avec solde et statut
        3. Remplit le tableau avec les résultats
        """
        try:
            # Récupération des filtres
            search_text = self.search_input.text().strip()
            classe_id = self.classe_filter.currentData()
            statut = self.statut_filter.currentData()
            
            # Si classe_id est -1, None (pas de filtre)
            if classe_id == -1:
                classe_id = None
            
            # Recherche des élèves avec solde et statut
            students = self.student_service.search_students_with_solde(search_text, classe_id, statut)
            
            # Stockage pour utilisation ultérieure
            self.current_students = students
            
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
            
            # Nom
            nom_item = QTableWidgetItem(student['nom'])
            nom_item.setData(Qt.ItemDataRole.UserRole, student['id'])  # Stocke l'ID
            self.table.setItem(row, 0, nom_item)
            
            # Prénom
            prenom_item = QTableWidgetItem(student['prenom'])
            self.table.setItem(row, 1, prenom_item)
            
            # Classe
            classe_item = QTableWidgetItem(student['nom_classe'])
            self.table.setItem(row, 2, classe_item)
            
            # Total dû
            total_item = QTableWidgetItem(f"{student['total_du']:,}")  # Format avec séparateur de milliers
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, total_item)
            
            # Payé
            # Pourquoi student.get('total_paye', 0) : Le service fournit maintenant total_paye
            total_paye = student.get('total_paye', 0)
            paye_item = QTableWidgetItem(f"{total_paye:,}")  # Format avec séparateur de milliers
            paye_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, paye_item)
            
            # Solde
            solde_item = QTableWidgetItem(f"{student['solde']:,}")  # Format avec séparateur de milliers
            solde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, solde_item)
            
            # Statut avec couleur
            statut_item = QTableWidgetItem(student['statut'])
            # Attribution de la couleur selon le statut
            # Pourquoi STATUS_COLORS : Couleurs cohérentes définies dans theme.py
            statut_item.setBackground(STATUS_COLORS.get(student['statut'], QColor(255, 255, 255)))
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
            detail.exec()
            
            # Rechargement de la liste après fermeture de la fiche
            # Pourquoi : Si un paiement a été enregistré dans la fiche,
            # la liste doit refléter les nouvelles données (solde, statut)
            self._load_students()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture de la fiche : {str(e)}")