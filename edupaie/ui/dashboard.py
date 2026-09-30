# =============================================================================
# dashboard.py - Tableau de bord de l'application
# =============================================================================
# Rôle : QWidget affichant les statistiques et la liste des élèves.
# =============================================================================
# Ce fichier utilise :
# - PySide6 pour les widgets Qt
# - services.dashboard_service pour les statistiques
# - services.student_service pour la liste enrichie des élèves
# =============================================================================
# Ce fichier est utilisé par :
# - ui.main_window comme page d'accueil de l'application
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from edupaie.services.dashboard_service import DashboardService
from edupaie.services.student_service import StudentService
from edupaie.ui.error_handler import handle_slot_errors
from edupaie.ui.theme import STATUS, format_fcfa, TEXT, TEXT_MUTED


class Dashboard(QWidget):
    """
    Tableau de bord de l'application EduPaie.
    
    Responsabilité : Afficher les 4 indicateurs clés de performance (KPI)
    et la liste des élèves avec leur statut de paiement.
    
    Pourquoi cette page : Permet une vue d'ensemble immédiate de la situation
    financière de l'établissement (nombre d'élèves, total encaissé, total restant dû,
    nombre d'élèves non soldés) et un accès rapide à la liste des élèves.
    
    Fonctionnalités :
    - 4 cartes avec les KPI (nombre d'élèves, total encaissé, total restant dû, non soldés)
    - Tableau des élèves triable et filtrable par statut
    - Rafraîchissement automatique après chaque paiement
    - Couleurs du statut (vert Soldé, orange Partiel, rouge Non payé)
    """
    
    def __init__(self, dashboard_service: DashboardService,
                 student_service: StudentService, parent=None) -> None:
        """
        Initialise le tableau de bord.
        
        Args:
            dashboard_service: Instance du service pour les statistiques.
            student_service: Instance du service pour les opérations métier.
            parent: Widget parent (optionnel).
        """
        super().__init__(parent)
        
        self.dashboard_service = dashboard_service
        self.student_service = student_service
        
        # Configuration de l'interface
        self._create_ui()
        
        # Chargement initial des données
        self._load_dashboard_data()
    
    def _create_ui(self) -> None:
        """
        Crée l'interface utilisateur du tableau de bord.
        
        Comprend :
        - 4 cartes avec les KPI
        - Filtre par statut
        - Tableau des élèves avec leurs informations
        """
        layout = QVBoxLayout()
        
        # ===== Section : Cartes KPI =====
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)
        
        # Carte 1 : Nombre d'élèves (bleu)
        self.card_eleves = self._create_kpi_card("Élèves", "0", "#2563EB")
        kpi_layout.addWidget(self.card_eleves)
        
        # Carte 2 : Total encaissé (vert)
        self.card_encaisse = self._create_kpi_card("Encaissé", "0 FCFA", "#16A34A")
        kpi_layout.addWidget(self.card_encaisse)
        
        # Carte 3 : Restant dû (orange)
        self.card_restant = self._create_kpi_card("Restant dû", "0 FCFA", "#D97706")
        kpi_layout.addWidget(self.card_restant)
        
        # Carte 4 : Élèves non soldés (rouge)
        self.card_non_soldes = self._create_kpi_card("Non soldés", "0", "#DC2626")
        kpi_layout.addWidget(self.card_non_soldes)
        
        layout.addLayout(kpi_layout)
        
        # ===== Section : Filtre par statut =====
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(20, 10, 20, 10)
        
        filter_label = QLabel("Filtrer par statut :")
        filter_label.setProperty("isFilter", True)
        filter_layout.addWidget(filter_label)
        
        self.statut_filter = QComboBox()
        self.statut_filter.addItems(["Tous", "Soldé", "Partiellement payé", "Non payé"])
        self.statut_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.statut_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # ===== Section : Tableau des élèves =====
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(6)
        self.students_table.setHorizontalHeaderLabels([
            "Nom", "Prénom", "Classe", "Total dû (FCFA)", "Payé (FCFA)", "Statut"
        ])
        
        # Configuration du tableau
        self.students_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.students_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.students_table.setAlternatingRowColors(True)
        self.students_table.setSortingEnabled(True)
        
        # Masquer les numéros de ligne
        self.students_table.verticalHeader().setVisible(False)
        
        # Définir la hauteur des lignes
        self.students_table.verticalHeader().setDefaultSectionSize(36)
        
        # Ajustement des colonnes
        header = self.students_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Nom
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Prénom
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Classe
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Total dû
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Payé
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        
        layout.addWidget(self.students_table)
        
        self.setLayout(layout)
    
    def _create_kpi_card(self, title: str, value: str, color: str) -> QFrame:
        """
        Crée une carte KPI avec un titre et une valeur.
        
        Args:
            title: Titre de la carte.
            value: Valeur initiale.
            color: Couleur de fond de la carte (code hexadécimal).
        
        Returns:
            QFrame configuré comme carte KPI.
        
        Pourquoi QFrame : Permet de créer un conteneur avec bordure
        et fond personnalisés pour mettre en valeur les KPI.
        """
        card = QFrame()
        card.setProperty("card_type", "kpi")
        card.setProperty("border_color", color)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setProperty("label_type", "kpi_title")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setProperty("label_type", "kpi_value")
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        
        # Stockage de la référence à la valeur pour mise à jour
        card.value_label = value_label
        
        return card
    
    @handle_slot_errors
    def _load_dashboard_data(self) -> None:
        """
        Charge et affiche les données du tableau de bord.
        
        Récupère les 4 KPI via dashboard_service.dashboard_stats()
        et les affiche dans les cartes. Charge également la liste des élèves
        avec leur statut de paiement.
        
        Pourquoi cette méthode : Centralise le chargement des données pour
        faciliter le rafraîchissement après chaque paiement.
        """
        # Récupération des statistiques
        stats = self.dashboard_service.dashboard_stats()
        
        # Mise à jour des cartes KPI
        self.card_eleves.value_label.setText(str(stats['nombre_eleves']))
        self.card_encaisse.value_label.setText(format_fcfa(stats['total_encaisse']))
        self.card_restant.value_label.setText(format_fcfa(stats['total_restant_du']))
        self.card_non_soldes.value_label.setText(str(stats['eleves_non_soldes']))
        
        # Chargement de la liste des élèves
        self._load_students_table()
    
    def _load_students_table(self) -> None:
        """
        Charge et affiche la liste des élèves dans le tableau.
        
        Récupère la liste enrichie des élèves (avec solde et statut) via
        student_service.get_students_with_solde_and_statut() et l'affiche
        dans le tableau avec le filtre de statut appliqué.
        
        Pourquoi cette méthode : Sépare le chargement des KPI du chargement
        de la liste pour permettre des rafraîchissements sélectifs.
        """
        # Récupération du filtre de statut
        statut_filter = self.statut_filter.currentText()
        
        # Récupération de la liste enrichie des élèves
        students = self.student_service.get_students_with_solde_and_statut()
        
        # Filtrage par statut
        if statut_filter != "Tous":
            students = [s for s in students if s['statut'] == statut_filter]
        
        # Remplissage du tableau
        self.students_table.setSortingEnabled(False)
        self.students_table.setRowCount(0)
        
        for row, student in enumerate(students):
            self.students_table.insertRow(row)
            
            # Nom
            nom_item = QTableWidgetItem(student['nom'])
            self.students_table.setItem(row, 0, nom_item)
            
            # Prénom
            prenom_item = QTableWidgetItem(student['prenom'])
            self.students_table.setItem(row, 1, prenom_item)
            
            # Classe
            classe_item = QTableWidgetItem(student['nom_classe'])
            self.students_table.setItem(row, 2, classe_item)
            
            # Total dû
            total_du_item = QTableWidgetItem(format_fcfa(student['total_du']))
            total_du_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.students_table.setItem(row, 3, total_du_item)
            
            # Payé
            total_paye = student['total_du'] - student['solde']
            paye_item = QTableWidgetItem(format_fcfa(total_paye))
            paye_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.students_table.setItem(row, 4, paye_item)
            
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
            self.students_table.setItem(row, 5, statut_item)
        
        self.students_table.setSortingEnabled(True)
    
    @handle_slot_errors
    def _on_filter_changed(self, statut: str) -> None:
        """
        Gère le changement de filtre de statut.
        
        Args:
            statut: Nouveau statut sélectionné (Tous, Soldé, Partiellement payé, Non payé).
        
        Pourquoi currentTextChanged.connect : Permet de rafraîchir le tableau
        dès que l'utilisateur change le filtre.
        
        Pourquoi rafraîchissement immédiat : Fournit un feedback instantané
        à l'utilisateur pour améliorer l'expérience utilisateur.
        """
        self._load_students_table()
    
    def refresh(self) -> None:
        """
        Rafraîchit les données du tableau de bord.
        
        Pourquoi cette méthode publique : Permet à d'autres widgets
        (comme student_detail après un paiement) de demander le rafraîchissement
        du tableau de bord via un signal/slot.
        
        Pourquoi le mécanisme de rafraîchissement : Le tableau de bord doit
        refléter l'état actuel des données après chaque modification (paiement,
        ajout d'élève, etc.). Les signaux Qt permettent de propager les notifications
        de changement de manière découplée.
        """
        self._load_dashboard_data()
