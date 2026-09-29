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
from PySide6.QtGui import QFont
from edupaie.services.dashboard_service import DashboardService
from edupaie.services.student_service import StudentService
from edupaie.ui.error_handler import handle_slot_errors


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
        
        # Carte 1 : Nombre d'élèves
        self.card_eleves = self._create_kpi_card("Nombre d'élèves", "0", "#2196F3")
        kpi_layout.addWidget(self.card_eleves)
        
        # Carte 2 : Total encaissé
        self.card_encaisse = self._create_kpi_card("Total encaissé", "0 FCFA", "#4CAF50")
        kpi_layout.addWidget(self.card_encaisse)
        
        # Carte 3 : Total restant dû
        self.card_restant = self._create_kpi_card("Total restant dû", "0 FCFA", "#FF9800")
        kpi_layout.addWidget(self.card_restant)
        
        # Carte 4 : Élèves non soldés
        self.card_non_soldes = self._create_kpi_card("Élèves non soldés", "0", "#F44336")
        kpi_layout.addWidget(self.card_non_soldes)
        
        layout.addLayout(kpi_layout)
        
        # ===== Section : Filtre par statut =====
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("Filtrer par statut :")
        filter_label.setStyleSheet("font-weight: bold;")
        filter_layout.addWidget(filter_label)
        
        self.statut_filter = QComboBox()
        self.statut_filter.addItems(["Tous", "Soldé", "Partiellement payé", "Non payé"])
        # Connexion signal -> slot : changement de filtre -> rafraîchissement du tableau
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
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
            }}
            QLabel {{
                color: white;
                background-color: transparent;
            }}
        """)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
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
        self.card_encaisse.value_label.setText(f"{stats['total_encaisse']:,} FCFA")
        self.card_restant.value_label.setText(f"{stats['total_restant_du']:,} FCFA")
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
            total_du_item = QTableWidgetItem(f"{student['total_du']:,}")
            total_du_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.students_table.setItem(row, 3, total_du_item)
            
            # Payé
            total_paye = student['total_du'] - student['solde']
            paye_item = QTableWidgetItem(f"{total_paye:,}")
            paye_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.students_table.setItem(row, 4, paye_item)
            
            # Statut avec couleur
            statut_item = QTableWidgetItem(student['statut'])
            # Attribution de la couleur selon le statut
            # Pourquoi ces couleurs : Vert pour soldé (positif), orange pour partiel (attention), rouge pour non payé (alerte)
            if student['statut'] == "Soldé":
                statut_item.setBackground(Qt.GlobalColor.green)
                statut_item.setForeground(Qt.GlobalColor.white)
            elif student['statut'] == "Partiellement payé":
                statut_item.setBackground(Qt.GlobalColor.yellow)
                statut_item.setForeground(Qt.GlobalColor.black)
            elif student['statut'] == "Non payé":
                statut_item.setBackground(Qt.GlobalColor.red)
                statut_item.setForeground(Qt.GlobalColor.white)
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
