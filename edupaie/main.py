# =============================================================================
# main.py - Point d'entrée de l'application EduPaie
# =============================================================================
# Rôle : Point d'entrée principal de l'application desktop.
# Initialise l'interface graphique et lance la boucle d'événements.
# =============================================================================
# Ce fichier utilise :
# - PySide6 pour l'interface graphique
# - ui.main_window pour la fenêtre principale
# =============================================================================
# Ce fichier est utilisé par :
# - L'utilisateur pour lancer l'application
# - PyInstaller pour créer l'exécutable
# =============================================================================

import sys
from PySide6.QtWidgets import QApplication
from edupaie.ui.main_window import MainWindow

def main() -> None:
    """
    Point d'entrée principal de l'application.
    
    Configure l'application Qt, crée la fenêtre principale et lance la boucle d'événements.
    
    Returns:
        None
        
    Exceptions:
        Exception propagée si erreur critique au démarrage
    """
    # Création de l'application Qt
    app = QApplication(sys.argv)
    
    # Configuration de l'exception hook global pour afficher les erreurs dans QMessageBox
    # Cela remplace le comportement par défaut qui affiche l'erreur dans la console
    from edupaie.ui.error_handler import setup_exception_handler
    setup_exception_handler()
    
    # Création et affichage de la fenêtre principale
    window = MainWindow()
    window.show()
    
    # Lancement de la boucle d'événements Qt
    # Cette boucle attend les événements utilisateur (clics, frappes clavier, etc.)
    # et les distribue aux widgets appropriés via les signaux/slots
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
