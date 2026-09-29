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
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from edupaie.data.database import Database
from edupaie.services.student_service import StudentService
from edupaie.services.dashboard_service import DashboardService
from edupaie.ui.students_view import StudentsView
from edupaie.ui.dashboard import Dashboard


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
        # Pourquoi ces dimensions : Taille raisonnable pour une application desktop
        self.setWindowTitle("EduPaie - Gestion des Paiements Scolaires")
        self.setMinimumSize(1000, 700)
        
        # Initialisation des services
        # Pourquoi : Les services sont partagés entre les pages et doivent être initialisés
        self.database = Database()
        self.student_service = StudentService(self.database)
        self.dashboard_service = DashboardService(
            self.student_service.repository,
            self.student_service.payment_repository
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
        
        # Application du style
        self._apply_style()
    
    def _create_sidebar(self) -> QFrame:
        """
        Crée la barre latérale de navigation.
        
        Returns:
            Le widget QFrame contenant la barre latérale.
        """
        # Frame pour la barre latérale
        # Pourquoi QFrame : Permet d'appliquer un style de fond distinct
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setObjectName("sidebar")
        
        # Layout vertical pour la barre latérale
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)
        
        # Titre de l'application
        title_label = QLabel("EduPaie")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        sidebar_layout.addWidget(title_label)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        sidebar_layout.addWidget(separator)
        
        # Bouton Tableau de bord
        self.btn_dashboard = QPushButton("Tableau de bord")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        self.btn_dashboard.setObjectName("nav_button")
        # Connexion signal -> slot : clic sur le bouton -> affichage page tableau de bord
        # Pourquoi clicked.connect : Mécanisme signal/slot de Qt pour réagir aux événements
        self.btn_dashboard.clicked.connect(lambda: self._show_page(0))
        sidebar_layout.addWidget(self.btn_dashboard)
        
        # Bouton Élèves
        self.btn_students = QPushButton("Élèves")
        self.btn_students.setCheckable(True)
        self.btn_students.setObjectName("nav_button")
        # Connexion signal -> slot : clic sur le bouton -> affichage page élèves
        self.btn_students.clicked.connect(lambda: self._show_page(1))
        sidebar_layout.addWidget(self.btn_students)
        
        # Espaceur pour pousser les boutons vers le haut
        sidebar_layout.addStretch()
        
        return sidebar
    
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
        students_page = StudentsView(self.student_service)
        # Connexion signal -> slot : paiement effectué -> rafraîchissement tableau de bord
        # Pourquoi connecter à la page tableau de bord : Le KPI doit refléter le nouveau paiement
        students_page.payment_made.connect(lambda: self._refresh_dashboard())
        self.stack.addWidget(students_page)
    
    def _show_page(self, index: int) -> None:
        """
        Affiche la page correspondant à l'index donné.
        
        Args:
            index: Index de la page à afficher dans le stack widget
        """
        # Changement de la page affichée
        self.stack.setCurrentIndex(index)
        
        # Mise à jour de l'état des boutons
        # Pourquoi : Seul le bouton de la page active doit être checked
        buttons = [self.btn_dashboard, self.btn_students]
        for i, button in enumerate(buttons):
            button.setChecked(i == index)
    
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
    
    def _apply_style(self) -> None:
        """
        Applique le style QSS (Qt Style Sheet) à l'application.
        
        Pourquoi QSS : Permet de styler l'interface comme CSS pour le web,
        séparant le style de la logique.
        
        Style choisi : Sobre et professionnel, avec :
        - Couleurs neutres (gris, blanc)
        - Contraste suffisant pour la lisibilité
        - Effet hover sur les boutons pour l'interactivité
        """
        style = """
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            #sidebar {
                background-color: #2c3e50;
                color: white;
            }
            
            QLabel {
                color: #333333;
            }
            
            #sidebar QLabel {
                color: white;
            }
            
            #nav_button {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                text-align: left;
            }
            
            #nav_button:hover {
                background-color: #3d566e;
            }
            
            #nav_button:checked {
                background-color: #3498db;
            }
        """
        
        self.setStyleSheet(style)
