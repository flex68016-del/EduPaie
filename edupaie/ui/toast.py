# =============================================================================
# toast.py - Notifications toast non bloquantes
# =============================================================================
# Rôle : QWidget pour afficher des notifications de succès temporaires.
# =============================================================================
# Ce fichier utilise :
# - PySide6 pour les widgets Qt
# - PySide6.QtCore pour les animations et timers
# =============================================================================
# Ce fichier est utilisé par :
# - Toutes les vues UI pour afficher des notifications de succès
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont
from edupaie.ui.theme import TEXT


class Toast(QWidget):
    """
    Notification toast non bloquante pour les succès.
    
    Responsabilité : Afficher une notification de succès temporaire
    en bas à droite de l'écran, qui disparaît après 3 secondes.
    
    Pourquoi QWidget au lieu de QMessageBox : QMessageBox est bloquant
    et interrompt le flux de travail. Toast est non bloquant et permet
    à l'utilisateur de continuer à travailler.
    
    Style :
    - Carte verte (#DCFCE7 / #166534)
    - Positionnée en bas à droite
    - Disparition en fondu après 3 secondes
    """
    
    def __init__(self, message: str, parent=None) -> None:
        """
        Initialise la notification toast.
        
        Args:
            message: Message à afficher.
            parent: Widget parent (optionnel).
        """
        super().__init__(parent)
        
        self.message = message
        
        # Configuration de la fenêtre
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Label du message
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: #166534;
                font-size: 13px;
                font-weight: 500;
            }}
        """)
        layout.addWidget(self.message_label)
        
        # Style de la carte
        self.setStyleSheet("""
            QWidget {
                background: #DCFCE7;
                border-radius: 10px;
                border: 1px solid #BBF7D0;
            }
        """)
        
        # Effet d'opacité pour l'animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Timer pour la disparition automatique
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._fade_out)
        self.timer.setSingleShot(True)
    
    def show_toast(self, duration: int = 3000) -> None:
        """
        Affiche la notification toast et la fait disparaître après un délai.
        
        Args:
            duration: Durée d'affichage en millisecondes (défaut: 3000).
        """
        # Animation d'apparition (fade in)
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_in_animation.start()
        
        # Afficher le widget
        self.show()
        
        # Positionner en bas à droite du parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.width() - self.width() - 24
            y = parent_rect.height() - self.height() - 24
            self.move(x, y)
        
        # Démarrer le timer pour la disparition
        self.timer.start(duration)
    
    def _fade_out(self) -> None:
        """
        Animation de disparition (fade out) puis fermeture.
        """
        # Animation de disparition
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_animation.finished.connect(self.close)
        self.fade_out_animation.start()


def show_toast(message: str, parent=None, duration: int = 3000) -> None:
    """
    Fonction utilitaire pour afficher une notification toast.
    
    Args:
        message: Message à afficher.
        parent: Widget parent (optionnel).
        duration: Durée d'affichage en millisecondes (défaut: 3000).
    
    Pourquoi cette fonction : Simplifie l'utilisation de Toast dans tout le code.
    """
    toast = Toast(message, parent)
    toast.show_toast(duration)
