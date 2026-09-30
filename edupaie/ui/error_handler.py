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

import sys
import traceback
import logging
from functools import wraps
from pathlib import Path
from typing import Callable, Any
from PySide6.QtWidgets import QMessageBox, QApplication

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from edupaie.services.exceptions import ValidationError, NotFoundError, BusinessRuleError
from edupaie.utils.paths import user_data_dir


# Configuration du logging pour les erreurs
# Pourquoi logging : Permet de tracer les erreurs dans un fichier pour le débogage
# Pourquoi user_data_dir() : Écrit dans %APPDATA%/EduPaie (accès garanti), pas dans C:\
log_file = user_data_dir() / "edupaie_errors.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Chemin du fichier de log pour les messages d'erreur
ERROR_LOG_PATH = str(log_file)


def setup_exception_handler() -> None:
    """
    Configure le gestionnaire d'exceptions global de l'application.
    
    Cette fonction remplace sys.excepthook pour intercepter toutes les exceptions
    non gérées et les afficher dans une QMessageBox au lieu de faire planter
    l'application silencieusement.
    
    Pourquoi un exception hook global : En Python, les exceptions non gérées
    provoquent la fermeture brutale de l'application sans message explicite pour
    l'utilisateur. Ce hook affiche une boîte de dialogue avec un message
    compréhensible.
    
    Comportement :
    - ValidationError : QMessageBox.warning (erreur utilisateur)
    - NotFoundError : QMessageBox.warning (ressource introuvable)
    - BusinessRuleError : QMessageBox.warning (règle métier)
    - Autres exceptions : QMessageBox.critical (erreur technique) + log
    
    Exemple d'utilisation :
        Dans main.py, avant de lancer l'application :
        setup_exception_handler()
    """
    def exception_hook(exc_type: type, exc_value: BaseException, exc_traceback: Any) -> None:
        """
        Hook personnalisé pour les exceptions non gérées.
        
        Args:
            exc_type: Type de l'exception
            exc_value: Instance de l'exception
            exc_traceback: Traceback de l'exception
        """
        # Récupération du message d'erreur
        error_message = str(exc_value)
        
        # Si c'est une exception métier, afficher un warning
        if exc_type in (ValidationError, NotFoundError, BusinessRuleError):
            show_error_dialog("Attention", error_message, QMessageBox.Warning)
        else:
            # Pour les autres exceptions, afficher une erreur critique
            # et logger le traceback complet pour le débogage
            traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            logging.error(f"Exception non gérée : {traceback_str}")
            
            show_error_dialog(
                "Erreur critique",
                f"Une erreur inattendue s'est produite :\n\n{error_message}\n\n"
                f"Détails techniques enregistrés dans {ERROR_LOG_PATH}",
                QMessageBox.Critical
            )
    
    # Remplacement de l'exception hook par défaut
    # Pourquoi sys.excepthook : C'est le hook appelé par Python pour les exceptions non gérées
    sys.excepthook = exception_hook


def show_error_dialog(title: str, message: str, icon: QMessageBox.Icon) -> None:
    """
    Affiche une boîte de dialogue d'erreur.
    
    Args:
        title: Titre de la boîte de dialogue
        message: Message d'erreur à afficher
        icon: Icône de la boîte (Warning, Critical, Information)
    """
    # Récupération de l'application Qt active
    # Pourquoi QApplication.instance() : Permet d'accéder à l'application depuis n'importe où
    app = QApplication.instance()
    
    if app is not None:
        # Création et affichage de la boîte de dialogue
        msg_box = QMessageBox()
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()


def handle_slot_errors(func: Callable) -> Callable:
    """
    Décorateur pour protéger les slots Qt contre les exceptions.
    
    Ce décorateur enveloppe les slots pour intercepter les exceptions et les
    afficher dans une QMessageBox au lieu de les laisser propager silencieusement.
    
    Pourquoi un décorateur : Les slots Qt sont appelés par la boucle d'événements
    et les exceptions non gérées dans un slot ne sont pas visibles par l'exception
    hook global. Ce décorateur garantit que toutes les exceptions dans les slots
    sont gérées proprement.
    
    Comportement :
    - ValidationError : QMessageBox.warning
    - NotFoundError : QMessageBox.warning
    - BusinessRuleError : QMessageBox.warning
    - Autres exceptions : QMessageBox.critical + log
    
    Args:
        func: La fonction slot à protéger
    
    Returns:
        La fonction enveloppée avec gestion des erreurs
    
    Example:
        @handle_slot_errors
        def on_button_clicked(self):
            # Code qui peut lever des exceptions
            pass
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """
        Wrapper qui exécute la fonction et gère les exceptions.
        
        Args:
            *args: Arguments positionnels de la fonction
            **kwargs: Arguments nommés de la fonction
        
        Returns:
            Le résultat de la fonction si elle réussit
        
        Raises:
            Exception: L'exception si elle n'est pas une exception métier
        """
        try:
            # Exécution de la fonction originale
            return func(*args, **kwargs)
            
        except ValidationError as e:
            # Erreur de validation : afficher un warning
            show_error_dialog("Erreur de validation", e.message, QMessageBox.Warning)
            
        except NotFoundError as e:
            # Ressource introuvable : afficher un warning
            show_error_dialog("Non trouvé", e.message, QMessageBox.Warning)
            
        except BusinessRuleError as e:
            # Règle métier violée : afficher un warning
            show_error_dialog("Règle métier", e.message, QMessageBox.Warning)
            
        except Exception as e:
            # Autre exception : afficher une erreur critique et logger
            traceback_str = traceback.format_exc()
            logging.error(f"Exception dans le slot {func.__name__} : {traceback_str}")
            
            show_error_dialog(
                "Erreur critique",
                f"Une erreur inattendue s'est produite :\n\n{str(e)}\n\n"
                f"Détails techniques enregistrés dans {ERROR_LOG_PATH}",
                QMessageBox.Critical
            )
    
    return wrapper
