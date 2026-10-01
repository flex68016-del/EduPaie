# =============================================================================
# class_dialog.py - Dialogue pour ajouter/modifier une classe
# =============================================================================
# Rôle : QDialog pour la création et modification de classes.
# =============================================================================
# Ce fichier utilise :
# - PySide6 pour les widgets Qt
# - services.student_service pour la logique métier
# =============================================================================
# Ce fichier est utilisé par :
# - ui.students_view pour ajouter une nouvelle classe
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from edupaie.services.student_service import StudentService
from edupaie.services.exceptions import ValidationError
from edupaie.ui.theme import TEXT, TEXT_MUTED, SURFACE, BORDER, ACCENT, ACCENT_2, add_shadow, refresh_style
from edupaie.ui.icons import icon


class ClassDialog(QDialog):
    """
    Dialogue pour ajouter une nouvelle classe.
    
    Responsabilité : Permettre à l'utilisateur de saisir le nom d'une classe
    et de l'ajouter à la base de données avec validation.
    
    Pourquoi QDialog : Fenêtre modale standard pour les formulaires de saisie.
    """
    
    def __init__(self, student_service: StudentService, parent=None) -> None:
        """
        Initialise le dialogue de classe.
        
        Args:
            student_service: Instance du service pour les opérations métier.
            parent: Widget parent (optionnel).
        """
        super().__init__(parent)
        
        self.student_service = student_service
        
        # Configuration de la fenêtre
        self.setWindowTitle("Nouvelle classe")
        self.setMinimumWidth(400)
        
        # Création de l'interface
        self._create_ui()
    
    def _create_ui(self) -> None:
        """
        Crée l'interface utilisateur du dialogue.
        
        Comprend :
        - Champ de saisie du nom de la classe
        - Boutons Annuler et Enregistrer
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Titre
        title_label = QLabel("Nouvelle classe")
        title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {TEXT};")
        layout.addWidget(title_label)
        
        # Sous-titre
        subtitle_label = QLabel("Entrez le nom de la classe (ex: 6ème A, 5ème B)")
        subtitle_label.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        layout.addWidget(subtitle_label)
        
        # Champ de saisie
        input_layout = QVBoxLayout()
        
        input_label = QLabel("Nom de la classe")
        input_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {TEXT};")
        input_layout.addWidget(input_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: 6ème A")
        self.name_input.setMinimumHeight(40)
        input_layout.addWidget(self.name_input)
        
        layout.addLayout(input_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setProperty("button_type", "secondary")
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton("Enregistrer")
        self.btn_save.setProperty("button_type", "primary")
        self.btn_save.clicked.connect(self._on_save)
        buttons_layout.addWidget(self.btn_save)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Appliquer le style premium
        self._apply_style()
        
        # Focus sur le champ de saisie
        self.name_input.setFocus()
    
    def _apply_style(self) -> None:
        """
        Applique le style premium aux widgets.
        """
        # Style du champ de saisie
        input_style = f"""
            QLineEdit {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                color: {TEXT};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {ACCENT};
            }}
        """
        self.name_input.setStyleSheet(input_style)
        
        refresh_style(self.btn_cancel)
        refresh_style(self.btn_save)
    
    def _on_save(self) -> None:
        """
        Gère le clic sur le bouton Enregistrer.
        
        Valide le nom de la classe et l'ajoute via le service.
        """
        nom = self.name_input.text().strip()
        
        if not nom:
            QMessageBox.warning(self, "Erreur", "Le nom de la classe ne peut pas être vide.")
            return
        
        try:
            # Ajout de la classe via le service
            self.student_service.add_class(nom)
            
            # Succès
            QMessageBox.information(self, "Succès", f"La classe '{nom}' a été ajoutée avec succès.")
            self.accept()
            
        except ValidationError as e:
            QMessageBox.warning(self, "Erreur de validation", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout de la classe : {str(e)}")
