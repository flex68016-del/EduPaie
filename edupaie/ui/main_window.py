# =============================================================================
# main_window.py - Fenêtre principale de l'application
# =============================================================================
# Rôle : Définit la fenêtre principale avec barre de navigation et zones de contenu.
# =============================================================================
# Ce fichier utilise :
# - PySide6 pour les widgets Qt
# - services.student_service pour la logique métier
# - data.database pour la connexion à la base de données
# - ui.students_view pour la page des élèves
# =============================================================================
# Ce fichier est utilisé par :
# - main.py pour créer et afficher la fenêtre principale
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QIcon
from edupaie.data.database import Database
from edupaie.services.student_service import StudentService
from edupaie.services.payment_service import PaymentService
from edupaie.services.dashboard_service import DashboardService
from edupaie.ui.students_view import StudentsView
from edupaie.ui.dashboard import Dashboard
from edupaie.ui.theme import (
    refresh_style, SIDEBAR_TOP, SIDEBAR_BOTTOM, SIDEBAR_TEXT,
    TEXT, SURFACE, BORDER, HOVER_ROW
)
from edupaie.ui.icons import icon
from edupaie.utils.paths import resource_path


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application EduPaie.
    
    Responsabilité : Fournir la structure de base de l'interface avec une barre
    latérale de navigation et une zone de contenu qui change selon la page sélectionnée.
    
    Pourquoi QMainWindow : Fournit une fenêtre principale avec barre de menu,
    barre de statut et dock widgets, standard pour les applications desktop.
    
    Structure :
    - Barre latérale gauche avec boutons de navigation
    - Zone de contenu centrale avec QStackedWidget pour changer de page
    - Pages actuelles : Tableau de bord, Élèves (autres "à venir")
    """
    
    def __init__(self) -> None:
        """
        Initialise la fenêtre principale.
        
        Crée la barre latérale, le stack widget et les pages.
        Configure le style de l'application.
        Initialise les services pour les pages.
        """
        super().__init__()
        
        # Configuration de la fenêtre
        # Pourquoi 1280x800 : Taille premium standard pour applications desktop
        # Pourquoi minimum 900x600 : Adapte aux petits écrans tout en gardant l'UX
        self.setWindowTitle("EduPaie - Gestion des Paiements Scolaires")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)
        
        # Centrer la fenêtre
        # Pourquoi : Meilleure UX au premier lancement
        screen = self.screen().availableGeometry()
        x = (screen.width() - 1280) // 2
        y = (screen.height() - 800) // 2
        self.move(x, y)
        
        # Icône de l'application
        # Pourquoi : Affiche l'icône dans la barre de titre et le gestionnaire de tâches
        icon_path = resource_path("edupaie/assets/edupaie-icon.svg")
        try:
            self.setWindowIcon(QIcon(icon_path))
        except Exception:
            # Fallback : Si l'icône ne charge pas, l'application fonctionne quand même
            pass
        
        # Initialisation des services
        # Pourquoi : Les services sont partagés entre les pages et doivent être initialisés
        self.database = Database()
        self.student_service = StudentService(self.database)
        self.payment_service = PaymentService(self.database)
        self.dashboard_service = DashboardService(
            self.student_service.repository,
            self.student_service.payment_repository,
            self.payment_service
        )
        
        # Création du widget central
        # Pourquoi QWidget central : QMainWindow a un widget central obligatoire
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal horizontal
        # Pourquoi QHBoxLayout : Sépare la barre latérale (gauche) du contenu (droite)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Création de la barre latérale
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Création du stack widget pour le contenu
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Création des pages
        self._create_pages()
    
    def _create_sidebar(self) -> QFrame:
        """
        Crée la barre latérale de navigation avec dégradé premium.
        
        Returns:
            Le widget QFrame contenant la barre latérale.
        """
        # Frame pour la barre latérale
        # Pourquoi QFrame : Permet d'appliquer un style de fond distinct
        sidebar = QFrame()
        sidebar.setFixedWidth(240)  # Largeur premium
        sidebar.setObjectName("sidebar")
        
        # Dégradé vertical pour la barre latérale
        # Pourquoi SIDEBAR_TOP → SIDEBAR_BOTTOM : Look premium inspiré de Stripe/Linear
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {SIDEBAR_TOP}, stop:1 {SIDEBAR_BOTTOM});
                border-right: 1px solid rgba(255,255,255,0.1);
            }}
        """)
        
        # Layout vertical pour la barre latérale
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(12)
        
        # Logo SVG en haut
        # Pourquoi : Branding premium avec logo vectoriel
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = resource_path("edupaie/assets/edupaie-logo.svg")
        try:
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
                logo_pixmap = logo_pixmap.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(logo_pixmap)
            else:
                # Fallback : texte si le logo ne charge pas
                logo_label.setText("EduPaie")
                logo_label.setStyleSheet(f"color: {SIDEBAR_TEXT}; font-size: 24px; font-weight: bold;")
        except Exception:
            # Fallback : texte si erreur
            logo_label.setText("EduPaie")
            logo_label.setStyleSheet(f"color: {SIDEBAR_TEXT}; font-size: 24px; font-weight: bold;")
        sidebar_layout.addWidget(logo_label)
        
        # Espace
        sidebar_layout.addSpacing(24)
        
        # Bouton Tableau de bord
        self.btn_dashboard = QPushButton("Tableau de bord")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        self.btn_dashboard.setProperty("active", True)
        self.btn_dashboard.setIcon(icon("dashboard", SIDEBAR_TEXT, 20))
        self.btn_dashboard.clicked.connect(lambda: self._show_page(0))
        sidebar_layout.addWidget(self.btn_dashboard)
        
        # Bouton Élèves
        self.btn_students = QPushButton("Élèves")
        self.btn_students.setCheckable(True)
        self.btn_students.setProperty("active", False)
        self.btn_students.setIcon(icon("users", SIDEBAR_TEXT, 20))
        self.btn_students.clicked.connect(lambda: self._show_page(1))
        sidebar_layout.addWidget(self.btn_students)
        
        # Espaceur pour pousser le bas vers le bas
        sidebar_layout.addStretch()
        
        # Carte version en bas
        # Pourquoi : Petit badge de version élégant
        version_card = QFrame()
        version_card.setObjectName("versionCard")
        version_card.setStyleSheet(f"""
            QFrame#versionCard {{
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        version_layout = QVBoxLayout(version_card)
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(4)
        
        version_label = QLabel("EduPaie v1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"color: {SIDEBAR_TEXT}; font-size: 11px;")
        version_layout.addWidget(version_label)
        
        sidebar_layout.addWidget(version_card)
        
        # Appliquer le style premium aux boutons de navigation
        self._style_nav_buttons()
        
        return sidebar
    
    def _style_nav_buttons(self) -> None:
        """
        Applique le style premium aux boutons de navigation.
        
        Pourquoi : Dégradé pour l'actif, translucide pour l'inactif, survol élégant.
        """
        # Style commun pour les boutons de navigation
        nav_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 10px;
                color: {SIDEBAR_TEXT};
                padding: 12px 16px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.1);
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4F46E5, stop:1 #2563EB);
                color: white;
                font-weight: 600;
            }}
            QPushButton::icon {{
                padding-right: 12px;
            }}
        """
        
        self.btn_dashboard.setStyleSheet(nav_style)
        self.btn_students.setStyleSheet(nav_style)
        refresh_style(self.btn_dashboard)
        refresh_style(self.btn_students)
    
    def _create_pages(self) -> None:
        """
        Crée les différentes pages de l'application et les ajoute au stack widget.
        
        Crée :
        - Page Tableau de bord (Dashboard avec KPI et liste des élèves)
        - Page Élèves (vue complète avec StudentsView)
        
        Pourquoi le tableau de bord en premier : C'est la page d'accueil qui donne
        une vue d'ensemble immédiate de la situation financière.
        """
        # Page Tableau de bord (Dashboard avec KPI et liste des élèves)
        # Pourquoi Dashboard : Affiche les 4 KPI et la liste des élèves filtrable
        dashboard_page = Dashboard(self.dashboard_service, self.student_service)
        self.stack.addWidget(dashboard_page)
        
        # Page Élèves (vue complète)
        # Pourquoi StudentsView : Vue complète avec tableau, recherche, filtre et actions CRUD
        students_page = StudentsView(self.student_service, self.payment_service)
        # Connexion signal -> slot : paiement effectué -> rafraîchissement tableau de bord
        # Pourquoi connecter à la page tableau de bord : Le KPI doit refléter le nouveau paiement
        students_page.payment_made.connect(lambda: self._refresh_dashboard())
        self.stack.addWidget(students_page)
    
    def _show_page(self, index: int) -> None:
        """
        Affiche la page correspondant à l'index donné avec une transition douce.
        
        Transition : Fondu de 150 ms entre les pages.
        
        Args:
            index: Index de la page à afficher dans le stack widget
        """
        # Page actuelle
        current_widget = self.stack.currentWidget()
        new_widget = self.stack.widget(index)
        
        # Mise à jour de l'état des boutons
        # Pourquoi : Seul le bouton de la page active doit être checked
        buttons = [self.btn_dashboard, self.btn_students]
        for i, button in enumerate(buttons):
            button.setChecked(i == index)
            button.setProperty("active", i == index)
            refresh_style(button)
        
        # Transition avec fondu si une page existe déjà
        if current_widget and new_widget and current_widget != new_widget:
            # Effet d'opacité pour la transition
            self._fade_transition(current_widget, new_widget, index)
        else:
            # Pas de transition si c'est le premier affichage
            self.stack.setCurrentIndex(index)
    
    def _fade_transition(self, old_widget: QWidget, new_widget: QWidget, target_index: int) -> None:
        """
        Effectue une transition par fondu entre deux widgets.
        
        Args:
            old_widget: Widget à faire disparaître
            new_widget: Widget à faire apparaître
            target_index: Index cible dans le stack widget
        """
        # Créer l'effet d'opacité pour le nouveau widget
        opacity_effect = QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0)
        
        # Changer la page
        self.stack.setCurrentIndex(target_index)
        
        # Animation de fondu (150 ms)
        self.fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_animation.setDuration(150)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Nettoyer l'effet après l'animation
        self.fade_animation.finished.connect(
            lambda: new_widget.setGraphicsEffect(None)
        )
        
        self.fade_animation.start()
    
    def _refresh_dashboard(self) -> None:
        """
        Rafraîchit le tableau de bord.
        
        Pourquoi cette méthode : Permet de rafraîchir les KPI après un paiement.
        Le tableau de bord est le premier widget dans le stack (index 0).
        """
        # Récupération du widget tableau de bord (index 0)
        dashboard_widget = self.stack.widget(0)
        if hasattr(dashboard_widget, 'refresh'):
            dashboard_widget.refresh()
