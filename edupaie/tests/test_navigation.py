# =============================================================================
# test_navigation.py - Tests de la navigation de la barre latérale
# =============================================================================
# Rôle : Vérifier que la navigation entre les pages fonctionne correctement
# =============================================================================
# Ce fichier utilise :
# - pytest pour les tests
# - PySide6 pour les widgets Qt
# =============================================================================
# Ce fichier est utilisé par :
# - pytest pour vérifier la qualité de la navigation
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from edupaie.ui.main_window import MainWindow


@pytest.fixture
def app():
    """Fixture pour créer l'application Qt."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_navigation(app):
    """
    Test la navigation entre les pages de la barre latérale.
    
    Vérifie :
    - Aucune exception lors des clics
    - La bonne page est affichée
    - La propriété 'active' est correcte sur les boutons
    """
    # Initialisation de la base de données pour les tests
    from edupaie.utils.paths import initialize_database
    initialize_database()
    
    # Création de la fenêtre principale
    window = MainWindow()
    
    try:
        # Vérification initiale : page tableau de bord active
        assert window.stack.currentIndex() == 0, "La page initiale doit être le tableau de bord"
        assert window.btn_dashboard.property("active") == True, "Le bouton Tableau de bord doit être actif"
        assert window.btn_students.property("active") == False, "Le bouton Élèves ne doit pas être actif"
        
        # Clic sur le bouton Élèves
        window.btn_students.click()
        
        # Vérification : page élèves active
        assert window.stack.currentIndex() == 1, "La page Élèves doit être affichée"
        assert window.btn_dashboard.property("active") == False, "Le bouton Tableau de bord ne doit plus être actif"
        assert window.btn_students.property("active") == True, "Le bouton Élèves doit être actif"
        
        # Clic sur le bouton Tableau de bord
        window.btn_dashboard.click()
        
        # Vérification : page tableau de bord active
        assert window.stack.currentIndex() == 0, "La page Tableau de bord doit être affichée"
        assert window.btn_dashboard.property("active") == True, "Le bouton Tableau de bord doit être actif"
        assert window.btn_students.property("active") == False, "Le bouton Élèves ne doit pas être actif"
        
        # Navigation alternée (10 fois pour test de stabilité)
        for i in range(10):
            if i % 2 == 0:
                window.btn_students.click()
                assert window.stack.currentIndex() == 1
                assert window.btn_students.property("active") == True
            else:
                window.btn_dashboard.click()
                assert window.stack.currentIndex() == 0
                assert window.btn_dashboard.property("active") == True
        
    finally:
        window.close()


def test_navigation_without_database(app):
    """
    Test la navigation sans base de données initialisée.
    
    Vérifie que la navigation fonctionne même si la base n'est pas prête.
    """
    # Création de la fenêtre principale sans initialiser la base
    window = MainWindow()
    
    try:
        # Clic sur le bouton Élèves
        window.btn_students.click()
        assert window.stack.currentIndex() == 1
        
        # Clic sur le bouton Tableau de bord
        window.btn_dashboard.click()
        assert window.stack.currentIndex() == 0
        
    finally:
        window.close()
