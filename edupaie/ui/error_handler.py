# =============================================================================
# error_handler.py - Gestion globale des erreurs UI
# =============================================================================
# Rôle : Configure la gestion des exceptions non gérées et fournit un décorateur
# pour protéger les slots contre les exceptions.
# =============================================================================
# Ce fichier utilise :
# - sys pour configurer l'exception hook
# - traceback pour obtenir le détail des erreurs
# - PySide6 pour afficher les QMessageBox
# =============================================================================
# Ce fichier est utilisé par :
# - main.py pour configurer l'exception hook global
# - Les widgets UI pour protéger leurs slots avec le décorateur
# =============================================================================
