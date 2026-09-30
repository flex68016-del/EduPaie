# =============================================================================
# student_form.py - Formulaire d'ajout/modification d'élève
# =============================================================================
# Rôle : QDialog pour saisir ou modifier les informations d'un élève.
# =============================================================================
# Ce fichier utilise :
# - PySide6 pour les widgets Qt
# - services.student_service pour la logique métier
# - services.exceptions pour la gestion des erreurs
# =============================================================================
# Ce fichier est utilisé par :
# - ui.students_view pour ouvrir le formulaire d'ajout/modification
# =============================================================================

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/ui/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from edupaie.services.student_service import StudentService
from edupaie.data.database import Database
from edupaie.services.exceptions import ValidationError, NotFoundError, BusinessRuleError
from edupaie.ui.error_handler import handle_slot_errors


class StudentForm(QDialog):
    """
    Formulaire d'ajout ou de modification d'un élève.

    Responsabilité : Fournir une interface pour saisir les informations d'un élève
    avec validation et gestion des erreurs.

    Pourquoi QDialog : Fenêtre modale qui bloque la fenêtre principale tant que
    l'utilisateur n'a pas validé ou annulé, garantissant une interaction cohérente.

    Modes de fonctionnement :
    - Mode ajout : champs vides, bouton "Créer"
    - Mode modification : champs pré-remplis, bouton "Modifier"

    La différence entre les modes est gérée par le paramètre student_data :
    - None : mode ajout
    - Dict avec données : mode modification

    Signaux :
    - student_changed : Émis après qu'un élève a été ajouté ou modifié
    """

    # Signal émis après l'ajout ou la modification d'un élève
    # Pourquoi Signal : Permet de notifier le tableau de bord pour rafraîchissement
    student_changed = Signal()

    def __init__(self, student_service: StudentService,
                 student_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialise le formulaire.
        
        Args:
            student_service: Instance du service pour les opérations métier
            student_data: Optionnel, données de l'élève pour le mode modification.
                          Si None, mode ajout.
        """
        super().__init__()
        
        self.student_service = student_service
        self.student_data = student_data
        self.is_edit_mode = student_data is not None
        
        # Configuration de la fenêtre
        self.setWindowTitle("Modifier l'élève" if self.is_edit_mode else "Ajouter un élève")
        self.setMinimumWidth(400)
        
        # Création de l'interface
        self._create_ui()
        
        # Remplissage des champs si mode modification
        if self.is_edit_mode:
            self._fill_fields()
    
    def _create_ui(self) -> None:
        """
        Crée l'interface utilisateur du formulaire.
        
        Crée les champs de saisie pour : nom, prénom, classe, année scolaire, total dû.
        Crée les boutons : Valider, Annuler.
        """
        # Layout principal
        layout = QVBoxLayout(self)
        
        # ===== Champ : Nom =====
        # Pourquoi QLabel + QLineEdit : Label pour l'intitulé, LineEdit pour la saisie
        nom_layout = QHBoxLayout()
        nom_label = QLabel("Nom :")
        nom_label.setFixedWidth(100)
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Nom de famille")
        nom_layout.addWidget(nom_label)
        nom_layout.addWidget(self.nom_input)
        layout.addLayout(nom_layout)
        
        # ===== Champ : Prénom =====
        prenom_layout = QHBoxLayout()
        prenom_label = QLabel("Prénom :")
        prenom_label.setFixedWidth(100)
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("Prénom")
        prenom_layout.addWidget(prenom_label)
        prenom_layout.addWidget(self.prenom_input)
        layout.addLayout(prenom_layout)
        
        # ===== Champ : Classe =====
        # Pourquoi QComboBox : Liste déroulante pour sélectionner une classe existante
        classe_layout = QHBoxLayout()
        classe_label = QLabel("Classe :")
        classe_label.setFixedWidth(100)
        self.classe_combo = QComboBox()
        self._load_classes()
        classe_layout.addWidget(classe_label)
        classe_layout.addWidget(self.classe_combo)
        layout.addLayout(classe_layout)
        
        # ===== Champ : Année scolaire =====
        annee_layout = QHBoxLayout()
        annee_label = QLabel("Année scolaire :")
        annee_label.setFixedWidth(100)
        self.annee_input = QLineEdit()
        self.annee_input.setPlaceholderText("2024-2025")
        self.annee_input.setInputMask("9999-9999")  # Masque de saisie
        annee_layout.addWidget(annee_label)
        annee_layout.addWidget(self.annee_input)
        layout.addLayout(annee_layout)
        
        # ===== Champ : Total dû =====
        # Pourquoi QSpinBox : Saisie d'entier avec boutons +/- et valeur minimum 0
        total_layout = QHBoxLayout()
        total_label = QLabel("Total dû (FCFA) :")
        total_label.setFixedWidth(100)
        self.total_input = QSpinBox()
        self.total_input.setMinimum(0)
        self.total_input.setMaximum(1000000)  # Maximum 1 000 000 FCFA
        self.total_input.setSingleStep(1000)  # Pas de 1000 FCFA
        self.total_input.setValue(50000)  # Valeur par défaut
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_input)
        layout.addLayout(total_layout)
        
        # Espaceur
        layout.addStretch()
        
        # ===== Boutons =====
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_validate = QPushButton(
            "Modifier" if self.is_edit_mode else "Créer"
        )
        self.btn_validate.setProperty("variant", "primary")
        self.btn_validate.clicked.connect(self._on_validate)
        buttons_layout.addWidget(self.btn_validate)
        
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setProperty("variant", "secondary")
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        layout.addLayout(buttons_layout)
    
    def _load_classes(self) -> None:
        """
        Charge la liste des classes dans la comboBox.
        
        Pourquoi charger les classes dynamiquement : Permet d'afficher les classes
        existantes dans la base de données plutôt que de les coder en dur.
        """
        try:
            classes = self.student_service.list_classes()
            self.classe_combo.clear()
            
            # Ajout d'une option vide par défaut
            self.classe_combo.addItem("", -1)
            
            # Ajout des classes
            for classe in classes:
                # Pourquoi userData : Stocke l'ID de la classe comme donnée utilisateur
                self.classe_combo.addItem(classe['nom'], classe['id'])
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement des classes : {str(e)}")
    
    def _fill_fields(self) -> None:
        """
        Remplit les champs avec les données de l'élève (mode modification).
        
        Pourquoi cette méthode : Sépare la logique de remplissage de la création de l'UI,
        rendant le code plus lisible et maintenable.
        """
        if not self.student_data:
            return
        
        # Remplissage des champs
        self.nom_input.setText(self.student_data.get('nom', ''))
        self.prenom_input.setText(self.student_data.get('prenom', ''))
        
        # Sélection de la classe
        classe_id = self.student_data.get('classe_id')
        for i in range(self.classe_combo.count()):
            if self.classe_combo.itemData(i) == classe_id:
                self.classe_combo.setCurrentIndex(i)
                break
        
        self.annee_input.setText(self.student_data.get('annee_scolaire', ''))
        self.total_input.setValue(self.student_data.get('total_du', 0))
    
    @handle_slot_errors
    def _on_validate(self) -> None:
        """
        Gère la validation du formulaire (clic sur bouton Valider).
        
        Cette méthode est décorée par @handle_slot_errors pour gérer les exceptions
        et afficher des QMessageBox appropriés.
        
        Comportement :
        - Valide les champs (vérifications basiques)
        - Appelle le service pour créer ou modifier l'élève
        - Affiche un message de succès
        - Ferme le formulaire avec accept() (retourne QDialog.Accepted)
        
        Pourquoi accept() : Indique à l'appelant que l'utilisateur a validé le formulaire
        et que les données ont été enregistrées avec succès.
        """
        # Récupération des valeurs des champs
        nom = self.nom_input.text().strip()
        prenom = self.prenom_input.text().strip()
        classe_id = self.classe_combo.currentData()
        annee_scolaire = self.annee_input.text().strip()
        total_du = self.total_input.value()
        
        # Validation basique des champs (ne doit pas être vide)
        # Pourquoi ces vérifications : Pré-validation avant d'appeler le service
        if not nom:
            QMessageBox.warning(self, "Validation", "Le nom ne peut pas être vide.")
            return
        
        if not prenom:
            QMessageBox.warning(self, "Validation", "Le prénom ne peut pas être vide.")
            return
        
        if classe_id == -1:
            QMessageBox.warning(self, "Validation", "Veuillez sélectionner une classe.")
            return
        
        if not annee_scolaire:
            QMessageBox.warning(self, "Validation", "L'année scolaire ne peut pas être vide.")
            return
        
        try:
            if self.is_edit_mode:
                # Mode modification : mettre à jour l'élève
                self.student_service.update_student(
                    self.student_data['id'],
                    nom,
                    prenom,
                    classe_id,
                    annee_scolaire,
                    total_du
                )
                QMessageBox.information(self, "Succès", "L'élève a été modifié avec succès.")
            else:
                # Mode ajout : créer l'élève
                self.student_service.create_student(
                    nom,
                    prenom,
                    classe_id,
                    annee_scolaire,
                    total_du
                )
                QMessageBox.information(self, "Succès", "L'élève a été créé avec succès.")

            # Émission du signal pour notifier le rafraîchissement
            # Pourquoi Signal : Permet au tableau de bord de se rafraîchir après ajout/modification
            self.student_changed.emit()

            # Fermeture du formulaire avec succès
            # Pourquoi accept() : Indique que l'utilisateur a validé
            self.accept()
            
        except ValidationError as e:
            # Erreur de validation : afficher un warning
            QMessageBox.warning(self, "Erreur de validation", e.message)
        
        except NotFoundError as e:
            # Élève non trouvé : afficher un warning
            QMessageBox.warning(self, "Non trouvé", e.message)
        
        except BusinessRuleError as e:
            # Règle métier violée : afficher un warning
            QMessageBox.warning(self, "Règle métier", e.message)
        
        except Exception as e:
            # Autre erreur : afficher une erreur critique
            QMessageBox.critical(self, "Erreur", f"Une erreur inattendue s'est produite : {str(e)}")
    
    def get_student_data(self) -> Dict[str, Any]:
        """
        Retourne les données saisies dans le formulaire.
        
        Returns:
            Dictionnaire contenant les données de l'élève.
        
        Pourquoi cette méthode : Permet à l'appelant de récupérer les données
        après accept() sans avoir besoin d'accéder directement aux champs.
        """
        return {
            'nom': self.nom_input.text().strip(),
            'prenom': self.prenom_input.text().strip(),
            'classe_id': self.classe_combo.currentData(),
            'annee_scolaire': self.annee_input.text().strip(),
            'total_du': self.total_input.value()
        }