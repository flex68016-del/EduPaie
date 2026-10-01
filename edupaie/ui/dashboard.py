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
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QHeaderView, QComboBox, QFrame, QPushButton,
    QGridLayout
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QRadialGradient, QBrush
from edupaie.services.dashboard_service import DashboardService
from edupaie.services.student_service import StudentService
from edupaie.ui.theme import (
    STATUS, format_fcfa, TEXT, TEXT_MUTED, TEXT_SUBTLE,
    SURFACE, BG_APP, ACCENT, ACCENT_2, BORDER, DANGER,
    ICON_TINTS, add_shadow, refresh_style
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
        
        layout.addLayout(header_layout)
        
        # ===== Section : Cartes KPI =====
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)
        
        # Carte 1 : Nombre d'élèves
        self.card_eleves = self._create_kpi_card("Élèves", "0", "users", ICON_TINTS["blue"], "18 élèves inscrits")
        kpi_layout.addWidget(self.card_eleves)
        
        # Carte 2 : Total encaissé
        self.card_encaisse = self._create_kpi_card("Encaissé", "0 FCFA", "wallet", ICON_TINTS["green"], "sur 1 035 000 FCFA dus")
        kpi_layout.addWidget(self.card_encaisse)
        
        # Carte 3 : Restant dû
        self.card_restant = self._create_kpi_card("Restant dû", "0 FCFA", "alert", ICON_TINTS["amber"], "en attente de paiement")
        kpi_layout.addWidget(self.card_restant)
        
        # Carte 4 : Élèves non soldés
        self.card_non_soldes = self._create_kpi_card("Non soldés", "0", "alert", ICON_TINTS["red"], "paiements en retard")
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
        # Appliquer le style premium
    
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
        
        # Chargement des derniers paiements
        self._load_derniers_paiements()
    
    def _load_derniers_paiements(self) -> None:
        """
        Charge et affiche les 6 derniers paiements.
        
        Utilise PaymentService.derniers_paiements() avec requête JOIN
        pour récupérer les informations de l'élève associé.
        """
        # Nettoyage de la liste existante
        while self.derniers_paiements_layout.count():
            child = self.derniers_paiements_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        try:
            # Récupération des derniers paiements via le service
            paiements = self.dashboard_service.payment_service.derniers_paiements(limite=6)
            
            if not paiements:
                # Aucun paiement
                placeholder = QLabel("Aucun paiement récent")
                placeholder.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic;")
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.derniers_paiements_layout.addWidget(placeholder)
                return
            
            # Affichage des paiements
            for paiement in paiements:
                paiement_widget = self._create_paiement_row(paiement)
                self.derniers_paiements_layout.addWidget(paiement_widget)
            
            self.derniers_paiements_layout.addStretch()
            
        except Exception as e:
            # En cas d'erreur, afficher un message avec le détail
            error_label = QLabel(f"Erreur: {str(e)}")
            error_label.setStyleSheet(f"color: {DANGER}; font-size: 12px;")
            self.derniers_paiements_layout.addWidget(error_label)
            print(f"Erreur lors du chargement des derniers paiements: {e}")
    
    def _create_paiement_row(self, paiement: dict) -> QFrame:
        """
        Crée une ligne de paiement pour la carte "Derniers paiements".
        
        Args:
            paiement: Dictionnaire contenant les informations du paiement.
        
        Returns:
            QFrame configuré comme ligne de paiement.
        """
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-bottom: 1px solid {BORDER};
                padding: 8px 0;
            }}
        """)
        
        layout = QHBoxLayout(row)
        layout.setSpacing(12)
        
        # Avatar avec initiales
        initiales = f"{paiement['eleve_prenom'][0]}{paiement['eleve_nom'][0]}".upper()
        avatar = QLabel(initiales)
        avatar.setFixedSize(32, 32)
        avatar.setStyleSheet(f"""
            QLabel {{
                background: {ACCENT};
                color: white;
                border-radius: 16px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(avatar)
        
        # Nom de l'élève
        nom_label = QLabel(f"{paiement['eleve_prenom']} {paiement['eleve_nom']}")
        nom_label.setStyleSheet(f"font-size: 13px; color: {TEXT}; font-weight: 500;")
        layout.addWidget(nom_label)
        
        layout.addStretch()
        
        # Mode de paiement
        mode_label = QLabel(paiement['mode'].replace('_', ' ').title())
        mode_label.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        layout.addWidget(mode_label)
        
        # Montant
        montant_label = QLabel(format_fcfa(paiement['montant']))
        montant_label.setStyleSheet(f"font-size: 13px; color: {TEXT}; font-weight: bold;")
        layout.addWidget(montant_label)
        
        return row
    
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
