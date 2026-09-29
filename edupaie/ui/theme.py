# =============================================================================
# theme.py - Couleurs et thème de l'interface EduPaie
# =============================================================================
# Rôle : Définit les couleurs utilisées dans l'interface utilisateur.
# =============================================================================
# Pourquoi un fichier séparé : Centralise les couleurs pour une maintenance
# facile et une cohérence visuelle dans toute l'application.
# =============================================================================

from PySide6.QtGui import QColor

# Couleurs de statut de paiement
# Pourquoi ces couleurs : Codes hexadécimaux standard pour les indicateurs de statut
# Vert clair pour soldé, orange pour partiel, rouge pour non payé
COLOR_SOLDÉ = QColor("#C8E6C9")      # Vert clair (Material Design Green 100)
COLOR_PARTIEL = QColor("#FFE0B2")    # Orange clair (Material Design Orange 100)
COLOR_NON_PAYÉ = QColor("#FFCDD2")   # Rouge clair (Material Design Red 100)

# Mapping statut -> couleur
STATUS_COLORS = {
    "Soldé": COLOR_SOLDÉ,
    "Partiellement payé": COLOR_PARTIEL,
    "Non payé": COLOR_NON_PAYÉ,
}
