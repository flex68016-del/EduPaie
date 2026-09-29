# =============================================================================
# student_service.py - Service pour la logique métier des élèves
# =============================================================================
# Rôle : Fournit la logique métier pour la gestion des élèves avec validations.
# =============================================================================
# Ce fichier utilise :
# - data.student_repository.StudentRepository pour l'accès aux données
# - data.payment_repository.PaymentRepository pour le calcul du solde
# - services.exceptions pour les erreurs métier
# =============================================================================
# Ce fichier est utilisé par :
# - ui.students_view pour les opérations sur les élèves
# =============================================================================

import sys
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/services/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from edupaie.data.student_repository import StudentRepository
from edupaie.data.payment_repository import PaymentRepository
from edupaie.data.database import Database
from edupaie.services.exceptions import ValidationError, NotFoundError, BusinessRuleError


class StudentService:
    """
    Service pour la gestion des élèves avec validation des règles métier.
    
    Responsabilité : Fournir les opérations métier sur les élèves en appliquant
    toutes les validations nécessaires avant d'interagir avec la base de données.
    
    Pourquoi un service : Sépare la logique métier de l'accès aux données et de l'interface.
    Le service valide les données, applique les règles métier, et lève des exceptions
    appropriées que l'interface peut afficher à l'utilisateur.
    
    Règles métier implémentées :
    - Nom et prénom non vides
    - Classe existante
    - Année scolaire au format YYYY-YYYY ou YYYY/YYYY
    - Total dû entier >= 0
    - Suppression refusée si l'élève a des paiements
    """
    
    def __init__(self, database: Database) -> None:
        """
        Initialise le service avec une connexion à la base de données.
        
        Args:
            database: Instance de la classe Database pour la connexion.
        """
        self.database = database
        self.repository = StudentRepository(database)
        self.payment_repository = PaymentRepository(database)
    
    # ===== Section : Validations =====
    
    def _validate_nom(self, nom: str) -> None:
        """
        Valide le nom de l'élève.
        
        Règle : Le nom ne doit pas être vide et doit contenir au moins 2 caractères.
        
        Args:
            nom: Nom de famille à valider
        
        Raises:
            ValidationError: Si le nom est vide ou trop court.
        
        Pourquoi cette validation : Un nom vide ou trop court n'a pas de sens
        et indique probablement une erreur de saisie.
        """
        # Vérification que le nom n'est pas vide
        # Pourquoi strip() : Élimine les espaces en début et fin de chaîne
        if not nom or not nom.strip():
            raise ValidationError("Le nom ne peut pas être vide.")
        
        # Vérification de la longueur minimale
        # Pourquoi 2 caractères : Un nom d'un seul caractère est très probablement une erreur
        if len(nom.strip()) < 2:
            raise ValidationError("Le nom doit contenir au moins 2 caractères.")
    
    def _validate_prenom(self, prenom: str) -> None:
        """
        Valide le prénom de l'élève.
        
        Règle : Le prénom ne doit pas être vide et doit contenir au moins 2 caractères.
        
        Args:
            prenom: Prénom à valider
        
        Raises:
            ValidationError: Si le prénom est vide ou trop court.
        
        Pourquoi cette validation : Même raison que pour le nom.
        """
        if not prenom or not prenom.strip():
            raise ValidationError("Le prénom ne peut pas être vide.")
        
        if len(prenom.strip()) < 2:
            raise ValidationError("Le prénom doit contenir au moins 2 caractères.")
    
    def _validate_classe_exists(self, classe_id: int) -> None:
        """
        Valide que la classe existe dans la base de données.
        
        Règle : L'identifiant de classe doit correspondre à une classe existante.
        
        Args:
            classe_id: Identifiant de la classe à valider
        
        Raises:
            ValidationError: Si la classe n'existe pas.
        
        Pourquoi cette validation : Empêche de créer un élève avec une classe
        qui n'existe pas, ce qui casserait l'intégrité référentielle.
        """
        classes = self.repository.list_classes()
        classe_ids = [c['id'] for c in classes]
        
        if classe_id not in classe_ids:
            raise ValidationError("La classe sélectionnée n'existe pas.")
    
    def _validate_annee_scolaire(self, annee_scolaire: str) -> None:
        """
        Valide le format de l'année scolaire.
        
        Règle : L'année scolaire doit être au format YYYY-YYYY ou YYYY/YYYY
        avec une différence de 1 entre les deux années (ex: 2024-2025, 2025/2026).
        
        Args:
            annee_scolaire: Année scolaire à valider
        
        Raises:
            ValidationError: Si le format est incorrect.
        
        Pourquoi cette validation : Garantit un format cohérent pour toutes les
        années scolaires et facilite le tri et le filtrage.
        """
        # Expression régulière pour valider le format
        # Pourquoi regex : Permet de valider le format précis YYYY-YYYY ou YYYY/YYYY
        pattern = r'^(\d{4})[-/](\d{4})$'
        match = re.match(pattern, annee_scolaire)
        
        if not match:
            raise ValidationError(
                "L'année scolaire doit être au format YYYY-YYYY ou YYYY/YYYY (ex: 2024-2025)."
            )
        
        # Extraction des deux années
        annee1 = int(match.group(1))
        annee2 = int(match.group(2))
        
        # Vérification que la deuxième année est la première + 1
        # Pourquoi : Une année scolaire couvre toujours deux années consécutives
        if annee2 != annee1 + 1:
            raise ValidationError(
                "L'année scolaire doit couvrir deux années consécutives (ex: 2024-2025)."
            )
    
    def _validate_total_du(self, total_du: int) -> None:
        """
        Valide le montant total dû.
        
        Règle : Le montant doit être un entier positif ou nul.
        
        Args:
            total_du: Montant total dû à valider
        
        Raises:
            ValidationError: Si le montant est négatif.
        
        Pourquoi cette validation : Une dette négative n'a pas de sens métier.
        """
        if total_du < 0:
            raise ValidationError("Le montant total dû ne peut pas être négatif.")
    
    # ===== Section : Opérations CRUD =====
    
    def create_student(self, nom: str, prenom: str, classe_id: int, 
                       annee_scolaire: str, total_du: int) -> int:
        """
        Crée un nouvel élève après validation.
        
        Args:
            nom: Nom de famille de l'élève
            prenom: Prénom de l'élève
            classe_id: Identifiant de la classe
            annee_scolaire: Année scolaire
            total_du: Montant total dû
        
        Returns:
            L'identifiant de l'élève créé.
        
        Raises:
            ValidationError: Si une validation échoue.
            sqlite3.IntegrityError: Si une erreur de base de données survient.
        
        Pourquoi valider avant d'insérer : Évite d'insérer des données invalides
        dans la base de données et fournit des messages d'erreur clairs à l'utilisateur.
        """
        # Validation de tous les champs
        self._validate_nom(nom)
        self._validate_prenom(prenom)
        self._validate_classe_exists(classe_id)
        self._validate_annee_scolaire(annee_scolaire)
        self._validate_total_du(total_du)
        
        # Insertion dans la base de données
        return self.repository.add(nom, prenom, classe_id, annee_scolaire, total_du)
    
    def update_student(self, eleve_id: int, nom: str, prenom: str, classe_id: int,
                       annee_scolaire: str, total_du: int) -> None:
        """
        Met à jour un élève existant après validation.
        
        Args:
            eleve_id: Identifiant de l'élève à modifier
            nom: Nouveau nom de famille
            prenom: Nouveau prénom
            classe_id: Nouvel identifiant de classe
            annee_scolaire: Nouvelle année scolaire
            total_du: Nouveau montant total dû
        
        Raises:
            ValidationError: Si une validation échoue.
            NotFoundError: Si l'élève n'existe pas.
            sqlite3.IntegrityError: Si une erreur de base de données survient.
        
        Pourquoi vérifier l'existence avant de modifier : Évite de modifier
        un élève qui n'existe pas et fournit un message d'erreur clair.
        """
        # Vérification que l'élève existe
        student = self.repository.get_by_id(eleve_id)
        if student is None:
            raise NotFoundError(f"Aucun élève trouvé avec l'identifiant {eleve_id}.")
        
        # Validation de tous les champs
        self._validate_nom(nom)
        self._validate_prenom(prenom)
        self._validate_classe_exists(classe_id)
        self._validate_annee_scolaire(annee_scolaire)
        self._validate_total_du(total_du)
        
        # Mise à jour dans la base de données
        self.repository.update(eleve_id, nom, prenom, classe_id, annee_scolaire, total_du)
    
    def delete_student(self, eleve_id: int) -> None:
        """
        Supprime un élève après vérification des contraintes.
        
        Args:
            eleve_id: Identifiant de l'élève à supprimer
        
        Raises:
            NotFoundError: Si l'élève n'existe pas.
            BusinessRuleError: Si l'élève a des paiements (contrainte ON DELETE RESTRICT).
            sqlite3.IntegrityError: Si une erreur de base de données survient.
        
        Pourquoi refuser la suppression avec paiements : Les paiements sont des
        données comptables importantes qui ne doivent pas être perdues. La contrainte
        ON DELETE RESTRICT dans le schéma garantit cela au niveau de la base de données.
        """
        # Vérification que l'élève existe
        student = self.repository.get_by_id(eleve_id)
        if student is None:
            raise NotFoundError(f"Aucun élève trouvé avec l'identifiant {eleve_id}.")
        
        try:
            # Tentative de suppression
            self.repository.delete(eleve_id)
        except Exception as e:
            # Si l'erreur est liée à une contrainte de clé étrangère
            # Pourquoi str(e) : Le message d'erreur SQLite contient "FOREIGN KEY constraint failed"
            if "FOREIGN KEY" in str(e) or "constraint" in str(e).lower():
                raise BusinessRuleError(
                    "Impossible de supprimer cet élève car il a des paiements enregistrés. "
                    "Supprimez d'abord les paiements associés."
                )
            else:
                # Autre erreur : la propager
                raise
    
    def get_student(self, eleve_id: int) -> Dict[str, Any]:
        """
        Récupère un élève par son identifiant.
        
        Args:
            eleve_id: Identifiant de l'élève
        
        Returns:
            Dictionnaire contenant les informations de l'élève.
        
        Raises:
            NotFoundError: Si l'élève n'existe pas.
        """
        student = self.repository.get_by_id(eleve_id)
        if student is None:
            raise NotFoundError(f"Aucun élève trouvé avec l'identifiant {eleve_id}.")
        
        return student
    
    def search_students(self, texte: str = "", classe_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Recherche des élèves avec filtres.
        
        Args:
            texte: Texte à rechercher dans le nom ou le prénom
            classe_id: Optionnel, identifiant de classe pour filtrer
        
        Returns:
            Liste de dictionnaires contenant les informations des élèves trouvés.
        
        Pourquoi déléguer au repository : La logique de recherche est purement
        d'accès aux données, pas de validation nécessaire ici.
        """
        return self.repository.search(texte, classe_id)
    
    def list_all_students(self) -> List[Dict[str, Any]]:
        """
        Liste tous les élèves.
        
        Returns:
            Liste de dictionnaires contenant les informations de tous les élèves.
        """
        return self.repository.list_all()
    
    def list_classes(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les classes disponibles.
        
        Returns:
            Liste de dictionnaires contenant les informations des classes.
        
        Pourquoi cette méthode : Fournit la liste des classes pour les filtres
        et les formulaires de l'interface.
        """
        return self.repository.list_classes()
    
    def get_student_with_class_name(self, eleve_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un élève avec le nom de sa classe au lieu de l'ID.
        
        Args:
            eleve_id: Identifiant de l'élève
        
        Returns:
            Dictionnaire contenant les informations de l'élève avec nom_classe
            au lieu de classe_id, ou None si non trouvé.
        
        Pourquoi remplacer classe_id par nom_classe : Plus lisible pour l'affichage
        dans l'interface utilisateur.
        """
        student = self.repository.get_by_id(eleve_id)
        if student is None:
            return None
        
        # Récupération du nom de la classe
        class_name = self.repository.get_class_name(student['classe_id'])
        
        # Remplacement de classe_id par nom_classe
        # Pourquoi dict(student) : Crée une copie pour ne pas modifier l'original
        result = dict(student)
        result['nom_classe'] = class_name or "Classe inconnue"
        del result['classe_id']
        
        return result
    
    def get_students_with_class_names(self, students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ajoute le nom de la classe à une liste d'élèves.
        
        Args:
            students: Liste d'élèves (avec classe_id)
        
        Returns:
            Liste d'élèves avec nom_classe au lieu de classe_id.
        
        Pourquoi cette méthode : Transforme une liste d'élèves pour l'affichage
        en remplaçant les IDs de classe par leurs noms.
        """
        result = []
        for student in students:
            class_name = self.repository.get_class_name(student['classe_id'])
            student_copy = dict(student)
            student_copy['nom_classe'] = class_name or "Classe inconnue"
            del student_copy['classe_id']
            result.append(student_copy)
        
        return result
    
    # ===== Section : Calcul du solde et du statut =====
    
    def solde(self, eleve_id: int) -> int:
        """
        Calcule le solde restant d'un élève.
        
        Règle : solde = total_du - total_paye
        
        Args:
            eleve_id: Identifiant de l'élève
        
        Returns:
            Le solde restant (en FCFA, entier).
            - Si solde > 0 : l'élève doit encore payer
            - Si solde = 0 : l'élève est soldé
            - Si solde < 0 : l'élève a payé plus que dû (remboursement)
        
        Pourquoi cette formule : Le solde représente ce qu'il reste à payer.
        Si l'élève a payé 30 000 sur 50 000, le solde est 20 000.
        
        Pourquoi ne pas stocker le solde : Le solde est une donnée dérivée
        qui peut être recalculée à tout moment à partir du total_du et des paiements.
        Le stocker introduirait un risque d'incohérence si les paiements changent
        sans mettre à jour le solde. Le recalcul garantit toujours la cohérence.
        
        Cas limite total_du = 0 : Si l'élève n'a rien à payer (total_du = 0),
        le solde est toujours 0, même s'il y a des paiements (ce qui ne devrait
        pas arriver métier, mais est géré pour éviter les erreurs).
        """
        # Récupération de l'élève
        student = self.repository.get_by_id(eleve_id)
        if student is None:
            raise NotFoundError(f"Aucun élève trouvé avec l'identifiant {eleve_id}.")
        
        # Récupération du total payé
        total_paye = self.payment_repository.total_paye(eleve_id)
        
        # Calcul du solde
        solde = student['total_du'] - total_paye
        
        return solde
    
    def statut(self, eleve_id: int) -> str:
        """
        Détermine le statut de paiement d'un élève.
        
        Règle de décision (ordre important) :
        1. Si solde = 0 -> "Soldé"
        2. Si aucun paiement -> "Non payé"
        3. Sinon -> "Partiellement payé"
        
        Args:
            eleve_id: Identifiant de l'élève
        
        Returns:
            Le statut de paiement : "Soldé", "Non payé" ou "Partiellement payé".
        
        Pourquoi cet ordre de décision :
        - D'abord vérifier solde = 0 : Car c'est le cas le plus important (soldé)
        - Ensuite vérifier aucun paiement : Car "Non payé" est plus spécifique que "Partiel"
        - Sinon "Partiellement payé" : Cas par défaut quand il y a des paiements mais solde > 0
        
        Cas limite total_du = 0 : Si l'élève n'a rien à payer (total_du = 0),
        le solde est 0, donc le statut est "Soldé" même sans paiements.
        C'est logique : s'il n'a rien à payer, il est considéré comme soldé.
        """
        # Récupération du solde
        solde = self.solde(eleve_id)
        
        # Cas 1 : Solde = 0 -> Soldé
        # Pourquoi en premier : C'est le cas le plus important à afficher
        if solde == 0:
            return "Soldé"
        
        # Cas 2 : Aucun paiement -> Non payé
        # Pourquoi en deuxième : Plus spécifique que "Partiellement payé"
        nombre_paiements = self.payment_repository.nombre_paiements(eleve_id)
        if nombre_paiements == 0:
            return "Non payé"
        
        # Cas 3 : Sinon -> Partiellement payé
        # Pourquoi cas par défaut : Il y a des paiements mais le solde > 0
        return "Partiellement payé"
    
    def get_student_with_solde_and_statut(self, eleve_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un élève avec son solde et son statut.
        
        Args:
            eleve_id: Identifiant de l'élève
        
        Returns:
            Dictionnaire contenant les informations de l'élève avec solde et statut,
            ou None si non trouvé.
        
        Pourquoi cette méthode : Fournit toutes les informations nécessaires
        pour l'affichage dans la fiche détaillée de l'élève.
        """
        student = self.get_student_with_class_name(eleve_id)
        if student is None:
            return None
        
        # Ajout du solde et du statut
        student['solde'] = self.solde(eleve_id)
        student['statut'] = self.statut(eleve_id)
        
        return student
    
    def get_students_with_solde_and_statut(self, students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ajoute le solde, le statut, le total payé et le nom de classe à une liste d'élèves.
        
        Args:
            students: Liste d'élèves (avec id, classe_id)
        
        Returns:
            Liste d'élèves avec solde, statut, total_paye et nom_classe ajoutés.
            classe_id est remplacé par nom_classe.
        
        Pourquoi cette méthode : Transforme une liste d'élèves pour l'affichage
        dans le tableau avec toutes les colonnes nécessaires.
        """
        result = []
        for student in students:
            student_copy = dict(student)
            solde = self.solde(student['id'])
            total_paye = self.payment_repository.total_paye(student['id'])
            class_name = self.repository.get_class_name(student.get('classe_id', -1))
            
            student_copy['solde'] = solde
            student_copy['statut'] = self.statut(student['id'])
            student_copy['total_paye'] = total_paye
            student_copy['nom_classe'] = class_name or "Classe inconnue"
            
            if 'classe_id' in student_copy:
                del student_copy['classe_id']
            
            result.append(student_copy)
        
        return result
    
    def search_students_with_solde(self, texte: str = "", classe_id: Optional[int] = None, 
                                  statut: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recherche des élèves avec filtres et calcul du solde/statut.
        
        Args:
            texte: Texte à rechercher dans le nom ou le prénom
            classe_id: Optionnel, identifiant de classe pour filtrer
            statut: Optionnel, statut pour filtrer ("Soldé", "Non payé", "Partiellement payé")
        
        Returns:
            Liste d'élèves avec solde, statut, total_paye et nom_classe, filtrés selon les critères.
        
        Pourquoi cette méthode : Combine la recherche et le calcul du solde/statut
        pour fournir directement les données prêtes à afficher.
        """
        # Recherche des élèves
        students = self.repository.search(texte, classe_id)
        
        # Ajout du solde, du statut, du total_paye et du nom de classe
        students_enriched = self.get_students_with_solde_and_statut(students)
        
        # Filtrage par statut si spécifié
        if statut:
            students_enriched = [s for s in students_enriched if s['statut'] == statut]
        
        return students_enriched