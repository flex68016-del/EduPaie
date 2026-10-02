# =============================================================================
# student_repository.py - Repository pour la gestion des élèves
# =============================================================================
# Rôle : Fournit les opérations d'accès aux données pour les élèves.
# =============================================================================
# Ce fichier utilise :
# - data.database.Database pour la connexion à la base de données
# - sqlite3 pour l'exécution des requêtes SQL
# =============================================================================
# Ce fichier est utilisé par :
# - services.student_service pour la logique métier des élèves
# =============================================================================

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/data/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from edupaie.data.database import Database


class StudentRepository:
    """
    Repository pour la gestion des élèves dans la base de données.
    
    Responsabilité : Fournir les opérations CRUD (Create, Read, Update, Delete)
    pour les élèves, ainsi que des fonctionnalités de recherche et de filtrage.
    
    Pourquoi un repository : Encapsule toute la logique SQL liée aux élèves,
    permettant à la couche services de se concentrer sur la logique métier
    sans connaître les détails de la base de données.
    
    Toutes les requêtes utilisent des paramètres "?" pour protéger contre
    les injections SQL. Les données sont retournées sous forme de dictionnaires
    pour une manipulation facile dans la couche services.
    """
    
    def __init__(self, database: Database) -> None:
        """
        Initialise le repository avec une connexion à la base de données.
        
        Args:
            database: Instance de la classe Database pour la connexion.
        """
        self.database = database
    
    def add(self, nom: str, prenom: str, classe_id: int, annee_scolaire: str, total_du: int) -> int:
        """
        Ajoute un nouvel élève dans la base de données.
        
        Args:
            nom: Nom de famille de l'élève
            prenom: Prénom de l'élève
            classe_id: Identifiant de la classe (clé étrangère)
            annee_scolaire: Année scolaire (ex: "2024-2025")
            total_du: Montant total dû par l'élève (en FCFA, entier)
        
        Returns:
            L'identifiant de l'élève nouvellement créé.
        
        Raises:
            sqlite3.IntegrityError: Si la classe_id n'existe pas (contrainte de clé étrangère)
        
        Pourquoi l'INSERT avec RETURNING : Permet de récupérer l'ID auto-incrémenté
        directement après l'insertion sans faire une requête supplémentaire.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : insertion d'un nouvel élève
            # Pourquoi les paramètres "?" : Protection contre les injections SQL
            # Pourquoi les colonnes explicites : Évite les erreurs si l'ordre des colonnes change
            cursor.execute(
                """INSERT INTO eleve (nom, prenom, classe_id, annee_scolaire, total_du)
                   VALUES (?, ?, ?, ?, ?)
                   RETURNING id""",
                (nom, prenom, classe_id, annee_scolaire, total_du)
            )
            
            # Récupération de l'ID généré
            result = cursor.fetchone()
            return result['id'] if result else cursor.lastrowid
    
    def update(self, eleve_id: int, nom: str, prenom: str, classe_id: int, 
               annee_scolaire: str, total_du: int) -> None:
        """
        Met à jour les informations d'un élève existant.
        
        Args:
            eleve_id: Identifiant de l'élève à modifier
            nom: Nouveau nom de famille
            prenom: Nouveau prénom
            classe_id: Nouvel identifiant de classe
            annee_scolaire: Nouvelle année scolaire
            total_du: Nouveau montant total dû
        
        Raises:
            sqlite3.IntegrityError: Si la classe_id n'existe pas
        
        Pourquoi UPDATE avec WHERE id : Cible uniquement l'élève spécifié,
        évitant de modifier accidentellement d'autres élèves.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : mise à jour d'un élève
            # Pourquoi les paramètres "?" : Protection contre les injections SQL
            cursor.execute(
                """UPDATE eleve
                   SET nom = ?, prenom = ?, classe_id = ?, annee_scolaire = ?, total_du = ?
                   WHERE id = ?""",
                (nom, prenom, classe_id, annee_scolaire, total_du, eleve_id)
            )
            
            # Vérification que l'élève existe bien
            # Pourquoi cursor.rowcount : Nombre de lignes affectées par l'UPDATE
            # Si 0, l'élève n'existe pas
            if cursor.rowcount == 0:
                raise ValueError(f"Aucun élève trouvé avec l'ID {eleve_id}")
    
    def delete(self, eleve_id: int) -> None:
        """
        Supprime un élève de la base de données.
        
        Args:
            eleve_id: Identifiant de l'élève à supprimer
        
        Raises:
            sqlite3.IntegrityError: Si l'élève a des paiements (ON DELETE RESTRICT)
            ValueError: Si l'élève n'existe pas
        
        Pourquoi DELETE avec WHERE id : Cible uniquement l'élève spécifié.
        La contrainte ON DELETE RESTRICT dans le schéma empêchera la suppression
        si des paiements existent pour cet élève.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : suppression d'un élève
            # Pourquoi le paramètre "?" : Protection contre les injections SQL
            cursor.execute(
                "DELETE FROM eleve WHERE id = ?",
                (eleve_id,)
            )
            
            # Vérification que l'élève existait
            if cursor.rowcount == 0:
                raise ValueError(f"Aucun élève trouvé avec l'ID {eleve_id}")
    
    def get_by_id(self, eleve_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un élève par son identifiant.
        
        Args:
            eleve_id: Identifiant de l'élève à rechercher
        
        Returns:
            Dictionnaire contenant les informations de l'élève, ou None si non trouvé.
            Le dictionnaire contient : id, nom, prenom, classe_id, annee_scolaire, total_du
        
        Pourquoi SELECT avec WHERE id : Recherche efficace par clé primaire (indexé).
        """
        with self.database.transaction() as cursor:
            # Requête SQL : sélection d'un élève par son ID
            # Pourquoi le paramètre "?" : Protection contre les injections SQL
            cursor.execute(
                """SELECT id, nom, prenom, classe_id, annee_scolaire, total_du
                   FROM eleve
                   WHERE id = ?""",
                (eleve_id,)
            )
            
            row = cursor.fetchone()
            
            # Conversion de la ligne Row en dictionnaire
            # Pourquoi dict(row) : Permet d'accéder aux valeurs par nom de colonne
            return dict(row) if row else None
    
    def search(self, texte: str, classe_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Recherche des élèves par texte et/ou filtre par classe.
        
        Args:
            texte: Texte à rechercher dans le nom ou le prénom (recherche partielle)
            classe_id: Optionnel, identifiant de classe pour filtrer
        
        Returns:
            Liste de dictionnaires contenant les informations des élèves trouvés.
            Chaque dictionnaire contient : id, nom, prenom, classe_id, annee_scolaire, total_du
        
        Pourquoi LIKE avec % : Permet la recherche partielle (ex: "Dup" trouve "Dupont")
        Pourquoi LOWER() : Recherche insensible à la casse (ex: "dupont" trouve "Dupont")
        Pourquoi les paramètres "?" : Protection contre les injections SQL
        """
        with self.database.transaction() as cursor:
            # Construction dynamique de la requête selon les filtres
            # Pourquoi la construction dynamique : Adapte la requête selon les paramètres fournis
            if classe_id is not None:
                # Recherche avec filtre par classe
                # Pourquoi AND : Combine les deux conditions (texte ET classe)
                query = """
                    SELECT e.id, e.nom, e.prenom, e.classe_id, e.annee_scolaire, e.total_du
                    FROM eleve e
                    WHERE e.classe_id = ?
                    AND (LOWER(e.nom) LIKE ? OR LOWER(e.prenom) LIKE ?)
                    ORDER BY e.nom, e.prenom
                """
                # Pourquoi LOWER(texte) : Normalise le texte de recherche en minuscules
                params = (classe_id, f"%{texte.lower()}%", f"%{texte.lower()}%")
            else:
                # Recherche sans filtre par classe
                query = """
                    SELECT e.id, e.nom, e.prenom, e.classe_id, e.annee_scolaire, e.total_du
                    FROM eleve e
                    WHERE LOWER(e.nom) LIKE ? OR LOWER(e.prenom) LIKE ?
                    ORDER BY e.nom, e.prenom
                """
                params = (f"%{texte.lower()}%", f"%{texte.lower()}%")
            
            # Si texte est vide, retourner tous les élèves (avec ou sans filtre classe)
            if not texte:
                if classe_id is not None:
                    query = """
                        SELECT e.id, e.nom, e.prenom, e.classe_id, e.annee_scolaire, e.total_du
                        FROM eleve e
                        WHERE e.classe_id = ?
                        ORDER BY e.nom, e.prenom
                    """
                    params = (classe_id,)
                else:
                    query = """
                        SELECT e.id, e.nom, e.prenom, e.classe_id, e.annee_scolaire, e.total_du
                        FROM eleve e
                        ORDER BY e.nom, e.prenom
                    """
                    params = ()
            
            cursor.execute(query, params)
            
            # Conversion de toutes les lignes en dictionnaires
            # Pourquoi list comprehension : Transformation compacte et efficace
            return [dict(row) for row in cursor.fetchall()]
    
    def list_all(self) -> List[Dict[str, Any]]:
        """
        Liste tous les élèves de la base de données.
        
        Returns:
            Liste de dictionnaires contenant les informations de tous les élèves.
            Chaque dictionnaire contient : id, nom, prenom, classe_id, annee_scolaire, total_du
        
        Pourquoi ORDER BY : Trie les résultats par nom puis prénom pour une lisibilité optimale.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : sélection de tous les élèves
            cursor.execute(
                """SELECT id, nom, prenom, classe_id, annee_scolaire, total_du
                   FROM eleve
                   ORDER BY nom, prenom"""
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def list_classes(self) -> List[Dict[str, Any]]:
        """
        Liste toutes les classes disponibles.
        
        Returns:
            Liste de dictionnaires contenant les informations des classes.
            Chaque dictionnaire contient : id, nom
        
        Pourquoi cette méthode : Fournit la liste des classes pour les filtres
        et les formulaires de sélection dans l'interface.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : sélection de toutes les classes
            # Pourquoi ORDER BY nom : Trie alphabétiquement pour l'affichage
            cursor.execute(
                "SELECT id, nom FROM classe ORDER BY nom"
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_class_name(self, classe_id: int) -> Optional[str]:
        """
        Récupère le nom d'une classe par son identifiant.
        
        Args:
            classe_id: Identifiant de la classe
        
        Returns:
            Le nom de la classe, ou None si non trouvée.
        
        Pourquoi cette méthode : Permet d'afficher le nom de la classe au lieu
        de son ID dans l'interface utilisateur.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : sélection du nom de la classe
            cursor.execute(
                "SELECT nom FROM classe WHERE id = ?",
                (classe_id,)
            )
            
            row = cursor.fetchone()
            return row['nom'] if row else None
    
    def add_class(self, nom: str) -> int:
        """
        Ajoute une nouvelle classe dans la base de données.
        
        Args:
            nom: Nom de la classe (ex: "6ème A", "5ème B")
        
        Returns:
            L'identifiant de la classe nouvellement créée.
        
        Raises:
            sqlite3.IntegrityError: Si une classe avec le même nom existe déjà (contrainte UNIQUE)
        
        Pourquoi l'INSERT avec RETURNING : Permet de récupérer l'ID auto-incrémenté
        directement après l'insertion sans faire une requête supplémentaire.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : insertion d'une nouvelle classe
            # Pourquoi les paramètres "?" : Protection contre les injections SQL
            cursor.execute(
                """INSERT INTO classe (nom)
                   VALUES (?)
                   RETURNING id""",
                (nom,)
            )
            
            # Récupération de l'ID généré
            result = cursor.fetchone()
            return result['id'] if result else cursor.lastrowid
    
    def delete_class(self, classe_id: int) -> None:
        """
        Supprime une classe de la base de données.
        
        Args:
            classe_id: Identifiant de la classe à supprimer
        
        Raises:
            sqlite3.IntegrityError: Si la classe a des élèves (ON DELETE RESTRICT)
            ValueError: Si la classe n'existe pas
        
        Pourquoi DELETE avec WHERE id : Cible uniquement la classe spécifiée.
        La contrainte ON DELETE RESTRICT dans le schéma empêchera la suppression
        si des élèves existent dans cette classe.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : suppression d'une classe
            # Pourquoi le paramètre "?" : Protection contre les injections SQL
            cursor.execute(
                "DELETE FROM classe WHERE id = ?",
                (classe_id,)
            )
            
            # Vérification que la classe existait
            if cursor.rowcount == 0:
                raise ValueError(f"Aucune classe trouvée avec l'ID {classe_id}")
    
    def count_students_in_class(self, classe_id: int) -> int:
        """
        Compte le nombre d'élèves dans une classe.
        
        Args:
            classe_id: Identifiant de la classe
        
        Returns:
            Le nombre d'élèves dans cette classe.
        
        Pourquoi cette méthode : Permet de vérifier si une classe peut être supprimée
        (si elle contient des élèves, la suppression sera bloquée par la contrainte FK).
        """
        with self.database.transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as nombre FROM eleve WHERE classe_id = ?",
                (classe_id,)
            )
            result = cursor.fetchone()
            return result['nombre'] if result else 0
    
    # ===== Section : Requêtes d'agrégation pour le tableau de bord =====
    
    def count_all_students(self) -> int:
        """
        Compte le nombre total d'élèves.
        
        Returns:
            Le nombre total d'élèves dans la base de données.
        
        Pourquoi COUNT(*) : Compte toutes les lignes de la table eleve.
        
        Pourquoi cette méthode : Permet d'afficher le nombre total d'élèves
        dans le tableau de bord.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : comptage de tous les élèves
            cursor.execute("SELECT COUNT(*) as nombre FROM eleve")
            result = cursor.fetchone()
            return result['nombre'] if result else 0
    
    def sum_total_du(self) -> int:
        """
        Calcule la somme totale des montants dus par tous les élèves.
        
        Returns:
            La somme totale des montants dus (en FCFA, entier).
            Retourne 0 s'il n'y a aucun élève.
        
        Pourquoi COALESCE(SUM(total_du), 0) : Si la base est vide ou si tous
        les total_du sont NULL, SUM retourne NULL. COALESCE remplace NULL par 0.
        
        Pourquoi cette méthode : Permet d'afficher le total des dettes
        dans le tableau de bord.
        """
        with self.database.transaction() as cursor:
            # Requête SQL : somme des montants dus
            cursor.execute("SELECT COALESCE(SUM(total_du), 0) as total FROM eleve")
            result = cursor.fetchone()
            return result['total'] if result else 0