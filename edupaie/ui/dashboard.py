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
from datetime import datetime
import locale

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QFrame, QPushButton,
    QGridLayout
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QRadialGradient, QBrush
from edupaie.services.dashboard_service import DashboardService
from edupaie.services.student_service import StudentService
from edupaie.ui.error_handler import handle_slot_errors
from edupaie.ui.theme import (
    STATUS, format_fcfa, TEXT, TEXT_MUTED, TEXT_SUBTLE,
    SURFACE, BG_APP, ACCENT, ACCENT_2, BORDER,
    ICON_TINT_BLUE, ICON_TINT_GREEN, ICON_TINT_AMBER, ICON_TINT_RED,
    add_shadow, refresh_style
)
from edupaie.ui.icons import icon

# Configuration locale française pour les dates
# Pourquoi : Afficher les dates en français (ex. "Jeudi 1 octobre 2026")
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except:
    # Fallback : Si la locale française n'est pas disponible
    pass


class CircularGaugeWidget(QWidget):
    """
    Widget personnalisé pour afficher une jauge circulaire premium.
    
    Affiche un anneau en dégradé accent avec le pourcentage au centre
    et une légende en FCFA en dessous.
    """
    
    def __init__(self, parent=None):
        """
        Initialise la jauge circulaire.
        
        Args:
            parent: Widget parent (optionnel).
        """
        super().__init__(parent)
        self.percentage = 0  # Pourcentage encaissé/dû (0-100)
        self.setMinimumSize(150, 150)
    
    def set_percentage(self, percentage: float) -> None:
        """
        Définit le pourcentage à afficher.
        
        Args:
            percentage: Pourcentage (0-100).
        """
        self.percentage = percentage
        self.update()
    
    def paintEvent(self, event):
        """
        Dessine la jauge circulaire avec QPainter.
        
        Pourquoi QPainter : Permet de dessiner des formes personnalisées
        (cercles, dégradés) qui ne sont pas disponibles avec les widgets Qt standard.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dimensions
        size = min(self.width(), self.height())
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = (size // 2) - 20
        
        # Cercle de fond (gris clair)
        painter.setPen(QPen(QColor(BORDER), 12))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Arc de progression (dégradé accent)
        # Pourquoi dégradé ACCENT → ACCENT_2 : Look premium inspiré de Stripe
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, QColor(ACCENT_2))
        gradient.setColorAt(1, QColor(ACCENT))
        
        pen = QPen(QBrush(gradient), 12)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Calcul de l'angle de progression (0° à 360°)
        start_angle = 90 * 16  # Qt utilise des 1/16èmes de degré
        span_angle = int(360 * 16 * (self.percentage / 100))
        
        painter.drawArc(center_x - radius, center_y - radius, radius * 2, radius * 2, start_angle, -span_angle)
        
        # Pourcentage au centre
        painter.setPen(QColor(TEXT))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 0, self.width(), self.height()), Qt.AlignmentFlag.AlignCenter, f"{int(self.percentage)}%")
        
        # Légende en dessous
        painter.setPen(QColor(TEXT_MUTED))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(QRectF(0, self.height() - 30, self.width(), 30), Qt.AlignmentFlag.AlignCenter, "Encaissé / Dû")


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
        Crée l'interface utilisateur du tableau de bord premium.
        
        Comprend :
        - En-tête avec titre, date et bouton "Nouveau paiement"
        - 4 cartes KPI blanches avec ombre douce
        - Deux cartes côte à côte : Recouvrement (jauge) et Derniers paiements
        - Filtres en chips arrondies
        - Tableau des élèves avec leur informations
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # ===== Section : En-tête =====
        header_layout = QHBoxLayout()
        
        # Titre et date
        title_date_layout = QVBoxLayout()
        
        title_label = QLabel("Tableau de bord")
        title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {TEXT};")
        title_date_layout.addWidget(title_label)
        
        # Date du jour en français
        # Pourquoi : Affiche "Jeudi 1 octobre 2026" pour un look premium
        today = datetime.now()
        date_str = today.strftime("%A %d %B %Y").capitalize()
        date_label = QLabel(date_str)
        date_label.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        title_date_layout.addWidget(date_label)
        
        header_layout.addLayout(title_date_layout)
        header_layout.addStretch()
        
        # Bouton "Nouveau paiement"
        self.btn_new_payment = QPushButton("+ Nouveau paiement")
        self.btn_new_payment.setIcon(icon("plus", "#FFFFFF", 16))
        self.btn_new_payment.setProperty("button_type", "primary")
        self.btn_new_payment.clicked.connect(self._on_new_payment)
        header_layout.addWidget(self.btn_new_payment)
        
        layout.addLayout(header_layout)
        
        # ===== Section : Cartes KPI =====
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)
        
        # Carte 1 : Nombre d'élèves
        self.card_eleves = self._create_kpi_card("Élèves", "0", "users", ICON_TINT_BLUE, "18 élèves inscrits")
        kpi_layout.addWidget(self.card_eleves)
        
        # Carte 2 : Total encaissé
        self.card_encaisse = self._create_kpi_card("Encaissé", "0 FCFA", "wallet", ICON_TINT_GREEN, "sur 1 035 000 FCFA dus")
        kpi_layout.addWidget(self.card_encaisse)
        
        # Carte 3 : Restant dû
        self.card_restant = self._create_kpi_card("Restant dû", "0 FCFA", "alert", ICON_TINT_AMBER, "en attente de paiement")
        kpi_layout.addWidget(self.card_restant)
        
        # Carte 4 : Élèves non soldés
        self.card_non_soldes = self._create_kpi_card("Non soldés", "0", "alert", ICON_TINT_RED, "paiements en retard")
        kpi_layout.addWidget(self.card_non_soldes)
        
        layout.addLayout(kpi_layout)
        
        # ===== Section : Deux cartes côte à côte =====
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(16)
        
        # Carte Recouvrement (jauge circulaire)
        self.card_recouvrement = self._create_recouvrement_card()
        row2_layout.addWidget(self.card_recouvrement, stretch=1)
        
        # Carte Derniers paiements
        self.card_derniers_paiements = self._create_derniers_paiements_card()
        row2_layout.addWidget(self.card_derniers_paiements, stretch=1)
        
        layout.addLayout(row2_layout)
        
        # ===== Section : Filtres en chips =====
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(8)
        
        self.filter_tous = QPushButton("Tous")
        self.filter_tous.setCheckable(True)
        self.filter_tous.setChecked(True)
        self.filter_tous.setProperty("filter_chip", True)
        self.filter_tous.setProperty("active", True)
        self.filter_tous.clicked.connect(lambda: self._on_filter_chip("Tous"))
        filters_layout.addWidget(self.filter_tous)
        
        self.filter_soldes = QPushButton("Soldés")
        self.filter_soldes.setCheckable(True)
        self.filter_soldes.setProperty("filter_chip", True)
        self.filter_soldes.setProperty("active", False)
        self.filter_soldes.clicked.connect(lambda: self._on_filter_chip("Soldé"))
        filters_layout.addWidget(self.filter_soldes)
        
        self.filter_partiels = QPushButton("Partiels")
        self.filter_partiels.setCheckable(True)
        self.filter_partiels.setProperty("filter_chip", True)
        self.filter_partiels.setProperty("active", False)
        self.filter_partiels.clicked.connect(lambda: self._on_filter_chip("Partiellement payé"))
        filters_layout.addWidget(self.filter_partiels)
        
        self.filter_non_payes = QPushButton("Non payés")
        self.filter_non_payes.setCheckable(True)
        self.filter_non_payes.setProperty("filter_chip", True)
        self.filter_non_payes.setProperty("active", False)
        self.filter_non_payes.clicked.connect(lambda: self._on_filter_chip("Non payé"))
        filters_layout.addWidget(self.filter_non_payes)
        
        filters_layout.addStretch()
        layout.addLayout(filters_layout)
        
        # ===== Section : Tableau des élèves =====
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(6)
        self.students_table.setHorizontalHeaderLabels([
            "Élève", "Classe", "Total dû", "Payé", "Solde", "Statut"
        ])
        
        # Configuration du tableau
        self.students_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.students_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.students_table.setSortingEnabled(True)
        
        # Masquer les numéros de ligne
        self.students_table.verticalHeader().setVisible(False)
        
        # Définir la hauteur des lignes (56 px premium)
        self.students_table.verticalHeader().setDefaultSectionSize(56)
        
        # Ajustement des colonnes
        header = self.students_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Élève
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Classe
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Total dû
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Payé
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Solde
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        
        layout.addWidget(self.students_table)
        
        self.setLayout(layout)
        
        # Appliquer le style premium
        self._apply_premium_style()
    
    def _create_kpi_card(self, title: str, value: str, icon_name: str, icon_tint: dict, context: str) -> QFrame:
        """
        Crée une carte KPI premium avec pastille d'icône teintée.
        
        Args:
            title: Titre de la carte.
            value: Valeur initiale.
            icon_name: Nom de l'icône (ex. "users", "wallet").
            icon_tint: Dictionnaire {"bg": ..., "fg": ...} pour la teinte de l'icône.
            context: Ligne de contexte discrète (ex. "18 élèves inscrits").
        
        Returns:
            QFrame configuré comme carte KPI premium.
        """
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
        """)
        add_shadow(card)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Pastille d'icône teintée (cercle 44 px)
        icon_bg = QFrame()
        icon_bg.setFixedSize(44, 44)
        icon_bg.setStyleSheet(f"""
            QFrame {{
                background: {icon_tint['bg']};
                border-radius: 22px;
            }}
        """)
        
        icon_layout = QVBoxLayout(icon_bg)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel()
        icon_label.setPixmap(icon(icon_name, icon_tint['fg'], 24).pixmap(24, 24))
        icon_layout.addWidget(icon_label)
        
        layout.addWidget(icon_bg)
        
        # Labels
        labels_layout = QVBoxLayout()
        labels_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED}; font-weight: 500;")
        labels_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 26px; color: {TEXT}; font-weight: bold;")
        labels_layout.addWidget(value_label)
        
        context_label = QLabel(context)
        context_label.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        labels_layout.addWidget(context_label)
        
        layout.addLayout(labels_layout)
        layout.addStretch()
        
        card.setLayout(layout)
        
        # Stockage des références pour mise à jour
        card.value_label = value_label
        card.context_label = context_label
        
        return card
    
    def _create_recouvrement_card(self) -> QFrame:
        """
        Crée la carte "Recouvrement" avec jauge circulaire.
        
        Returns:
            QFrame configuré avec la jauge et la répartition par statut.
        """
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
        """)
        add_shadow(card)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Titre
        title_label = QLabel("Recouvrement")
        title_label.setStyleSheet(f"font-size: 14px; color: {TEXT}; font-weight: 600;")
        layout.addWidget(title_label)
        
        # Jauge circulaire (widget personnalisé)
        self.gauge_widget = CircularGaugeWidget()
        layout.addWidget(self.gauge_widget, stretch=1)
        
        # Répartition par statut
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        # Soldés
        soldes_layout = QVBoxLayout()
        soldes_dot = QLabel("●")
        soldes_dot.setStyleSheet(f"color: {STATUS['Soldé']['bg']}; font-size: 12px;")
        soldes_count = QLabel("0")
        soldes_count.setStyleSheet(f"font-size: 18px; color: {TEXT}; font-weight: bold;")
        soldes_label = QLabel("Soldés")
        soldes_label.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        soldes_layout.addWidget(soldes_dot)
        soldes_layout.addWidget(soldes_count)
        soldes_layout.addWidget(soldes_label)
        stats_layout.addLayout(soldes_layout)
        
        # Partiels
        partiels_layout = QVBoxLayout()
        partiels_dot = QLabel("●")
        partiels_dot.setStyleSheet(f"color: {STATUS['Partiellement payé']['bg']}; font-size: 12px;")
        partiels_count = QLabel("0")
        partiels_count.setStyleSheet(f"font-size: 18px; color: {TEXT}; font-weight: bold;")
        partiels_label = QLabel("Partiels")
        partiels_label.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        partiels_layout.addWidget(partiels_dot)
        partiels_layout.addWidget(partiels_count)
        partiels_layout.addWidget(partiels_label)
        stats_layout.addLayout(partiels_layout)
        
        # Non payés
        non_payes_layout = QVBoxLayout()
        non_payes_dot = QLabel("●")
        non_payes_dot.setStyleSheet(f"color: {STATUS['Non payé']['bg']}; font-size: 12px;")
        non_payes_count = QLabel("0")
        non_payes_count.setStyleSheet(f"font-size: 18px; color: {TEXT}; font-weight: bold;")
        non_payes_label = QLabel("Non payés")
        non_payes_label.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        non_payes_layout.addWidget(non_payes_dot)
        non_payes_layout.addWidget(non_payes_count)
        non_payes_layout.addWidget(non_payes_label)
        stats_layout.addLayout(non_payes_layout)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        card.setLayout(layout)
        
        # Stockage des références pour mise à jour
        card.soldes_count = soldes_count
        card.partiels_count = partiels_count
        card.non_payes_count = non_payes_count
        
        return card
    
    def _create_derniers_paiements_card(self) -> QFrame:
        """
        Crée la carte "Derniers paiements" avec liste de 6 paiements.
        
        Returns:
            QFrame configuré avec la liste des derniers paiements.
        """
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 16px;
            }}
        """)
        add_shadow(card)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Titre
        title_label = QLabel("Derniers paiements")
        title_label.setStyleSheet(f"font-size: 14px; color: {TEXT}; font-weight: 600;")
        layout.addWidget(title_label)
        
        # Liste des paiements (6 lignes max)
        self.derniers_paiements_layout = QVBoxLayout()
        self.derniers_paiements_layout.setSpacing(8)
        layout.addLayout(self.derniers_paiements_layout)
        
        card.setLayout(layout)
        
        return card
    
    def _apply_premium_style(self) -> None:
        """
        Applique le style premium aux widgets.
        
        Pourquoi : Sépare le style de la création de l'interface pour une meilleure lisibilité.
        """
        # Style des boutons de filtre (chips)
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
    
    @handle_slot_errors
    def _load_dashboard_data(self) -> None:
        """
        Charge et affiche les données du tableau de bord premium.
        
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
        
        # Mise à jour de la jauge de recouvrement
        total_du = stats['total_encaisse'] + stats['total_restant_du']
        percentage = (stats['total_encaisse'] / total_du * 100) if total_du > 0 else 0
        self.gauge_widget.set_percentage(percentage)
        
        # Mise à jour de la répartition par statut
        self.card_recouvrement.soldes_count.setText(str(stats.get('soldes', 0)))
        self.card_recouvrement.partiels_count.setText(str(stats.get('partiels', 0)))
        self.card_recouvrement.non_payes_count.setText(str(stats.get('non_payes', 0)))
        
        # Chargement de la liste des élèves
        self._load_students_table()
        
        # Chargement des derniers paiements
        self._load_derniers_paiements()
    
    def _load_students_table(self) -> None:
        """
        Charge et affiche la liste des élèves dans le tableau premium.
        
        Récupère la liste enrichie des élèves (avec solde et statut) via
        student_service.get_students_with_solde_and_statut() et l'affiche
        dans le tableau avec le filtre de statut appliqué.
        
        Pourquoi cette méthode : Sépare le chargement des KPI du chargement
        de la liste pour permettre des rafraîchissements sélectifs.
        """
        # Récupération du filtre de statut actif
        statut_filter = self._get_active_filter()
        
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
            
            # Élève (avatar + nom complet)
            # Pour l'instant, on utilise le nom complet sans avatar (avatar sera ajouté avec delegate)
            nom_complet = f"{student['prenom']} {student['nom']}"
            eleve_item = QTableWidgetItem(nom_complet)
            self.students_table.setItem(row, 0, eleve_item)
            
            # Classe
            classe_item = QTableWidgetItem(student['nom_classe'])
            self.students_table.setItem(row, 1, classe_item)
            
            # Total dû
            total_du_item = QTableWidgetItem(format_fcfa(student['total_du']))
            total_du_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.students_table.setItem(row, 2, total_du_item)
            
            # Payé
            total_paye = student['total_du'] - student['solde']
            paye_item = QTableWidgetItem(format_fcfa(total_paye))
            paye_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.students_table.setItem(row, 3, paye_item)
            
            # Solde (en rouge si positif)
            solde_item = QTableWidgetItem(format_fcfa(student['solde']))
            solde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if student['solde'] > 0:
                solde_item.setForeground(QColor("#991B1B"))  # Rouge foncé pour le solde restant
            self.students_table.setItem(row, 4, solde_item)
            
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
    
    def _load_derniers_paiements(self) -> None:
        """
        Charge et affiche les 6 derniers paiements.
        
        Pourquoi cette méthode : Affiche les paiements récents pour une vue
        d'orientation rapide sur l'activité.
        
        Note : Pour l'instant, affiche un placeholder car le service
        derniers_paiements sera ajouté plus tard.
        """
        # Nettoyage de la liste existante
        while self.derniers_paiements_layout.count():
            child = self.derniers_paiements_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Placeholder pour l'instant (sera remplacé par le service)
        placeholder = QLabel("Aucun paiement récent")
        placeholder.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.derniers_paiements_layout.addWidget(placeholder)
    
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
    
    @handle_slot_errors
    def _on_filter_chip(self, statut: str) -> None:
        """
        Gère le clic sur un chip de filtre.
        
        Args:
            statut: Statut sélectionné ("Tous", "Soldé", "Partiellement payé", "Non payé").
        
        Pourquoi : Met à jour l'état des chips et rafraîchit le tableau.
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
        self._load_students_table()
    
    @handle_slot_errors
    def _on_new_payment(self) -> None:
        """
        Gère le clic sur le bouton "Nouveau paiement".
        
        Pourquoi : Ouvre le dialogue de paiement pour un nouvel élève.
        
        Note : Pour l'instant, affiche un message car le dialogue sera
        implémenté dans la vue élèves.
        """
        # Placeholder : pour l'instant, on redirige vers la vue élèves
        # Plus tard, on pourra ouvrir directement le dialogue de paiement
        pass
    
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
