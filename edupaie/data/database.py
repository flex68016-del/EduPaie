# =============================================================================
# database.py - Classe Database
# =============================================================================
# Rôle : Gestion de la connexion à la base de données SQLite et des transactions.
# =============================================================================
# Ce fichier utilise :
# - sqlite3 pour l'accès à la base de données
# =============================================================================
# Ce fichier est utilisé par :
# - Les repositories de la couche data pour exécuter les requêtes SQL
# =============================================================================

import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/data/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from edupaie.utils.paths import resource_path, user_data_dir


class Database:
    """
    Classe gérant la connexion à la base de données SQLite et les transactions.
    
    Responsabilité : Fournir une interface unique pour accéder à la base de données,
    initialiser le schéma si nécessaire, et gérer les transactions de manière sûre.
    
    Pourquoi cette classe : Encapsule la logique de connexion à SQLite pour éviter
    la duplication de code dans les repositories et garantir que le PRAGMA
    foreign_keys est toujours activé.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialise la connexion à la base de données.
        
        Args:
            db_path: Chemin vers le fichier de base de données SQLite.
                     Si None, utilise 'edupaie.db' dans le répertoire courant.
        
        Raises:
            sqlite3.Error: Si la connexion à la base de données échoue.
        """
        # Définition du chemin de la base de données
        # Pourquoi configurable : Permet de facilement changer l'emplacement (tests, prod)
        # Pourquoi user_data_dir : Stocke la DB dans le répertoire utilisateur (AppData, ~/.config)
        # pour respecter les conventions OS et séparer données du code
        if db_path is None:
            self.db_path = str(user_data_dir() / "edupaie.db")
        else:
            self.db_path = db_path
        
        # Initialisation de la connexion
        self._connection: Optional[sqlite3.Connection] = None
        
        # Chargement du schéma SQL depuis le fichier
        # Pourquoi : Sépare la définition du schéma du code Python
        # Pourquoi resource_path : Fonctionne aussi avec PyInstaller (sys._MEIPASS)
        # Pourquoi edupaie/db/schema.sql : Chemin relatif depuis le dossier edupaie/
        self._schema_path = resource_path("edupaie/db/schema.sql")
    
    def connect(self) -> sqlite3.Connection:
        """
        Établit la connexion à la base de données et initialise le schéma si nécessaire.
        
        Returns:
            La connexion SQLite établie.
        
        Raises:
            sqlite3.Error: Si la connexion échoue ou si le schéma est invalide.
            FileNotFoundError: Si le fichier schema.sql n'existe pas.
            RuntimeError: Si la connexion ne peut pas être établie (droits, chemin invalide, etc.)
        """
        # Si la connexion existe déjà, la retourner
        # Pourquoi : Évite de créer plusieurs connexions inutilement
        if self._connection is not None:
            return self._connection
        
        # Création de la connexion SQLite
        # Pourquoi sqlite3.connect : Crée la base si elle n'existe pas
        try:
            self._connection = sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            raise RuntimeError(
                f"Impossible de se connecter à la base de données : {self.db_path}\n"
                f"Erreur SQLite : {e}\n"
                f"Vérifiez que vous avez les droits d'écriture dans ce répertoire."
            ) from e
        
        # Configuration du row_factory pour retourner des objets Row
        # Pourquoi Row : Permet d'accéder aux colonnes par nom (row['nom']) au lieu
        # d'index (row[0]), rendant le code plus lisible et moins sujet aux erreurs
        self._connection.row_factory = sqlite3.Row
        
        # Activation des clés étrangères
        # Pourquoi à chaque connexion : SQLite ne conserve pas cette option entre
        # les connexions, donc il faut la réactiver à chaque fois pour garantir
        # l'intégrité référentielle (ON DELETE RESTRICT, etc.)
        try:
            self._connection.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            raise RuntimeError(
                f"Impossible de configurer la base de données : {e}"
            ) from e
        
        # Vérification si la base est vide (pas de tables)
        # Pourquoi : Détecte si c'est la première création de la base
        try:
            cursor = self._connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='classe'"
            )
        except sqlite3.Error as e:
            raise RuntimeError(
                f"Impossible de vérifier le schéma de la base de données : {e}"
            ) from e
        
        # Si la table classe n'existe pas, la base est vide : initialiser le schéma
        if cursor.fetchone() is None:
            self._initialize_schema()
        
        return self._connection
    
    def _initialize_schema(self) -> None:
        """
        Initialise le schéma de la base de données en exécutant le fichier schema.sql.
        
        Raises:
            FileNotFoundError: Si le fichier schema.sql n'existe pas.
            sqlite3.Error: Si l'exécution du schéma échoue.
        """
        # Vérification que la connexion est établie
        if self._connection is None:
            raise RuntimeError("La connexion à la base de données n'est pas établie")
        
        # Lecture du fichier schema.sql
        # Pourquoi : Le schéma est défini dans un fichier SQL séparé pour plus de clarté
        if not self._schema_path.exists():
            raise FileNotFoundError(f"Fichier schéma introuvable : {self._schema_path}")
        
        with open(self._schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Exécution du script SQL
        # Pourquoi executescript : Permet d'exécuter plusieurs instructions SQL
        # (CREATE TABLE, PRAGMA, CREATE INDEX) en un seul appel
        self._connection.executescript(schema_sql)
        
        # Commit des changements
        # Pourquoi : Le schéma doit être persisté immédiatement
        self._connection.commit()
    
    def initialize_schema_from_string(self, schema_sql: str) -> None:
        """
        Initialise le schéma de la base de données à partir d'une chaîne SQL.
        
        Cette méthode est utilisée lorsque le schema.sql n'est pas disponible
        en tant que fichier (par exemple, dans l'exécutable PyInstaller).
        
        Args:
            schema_sql: Le script SQL complet pour initialiser la base.
        
        Raises:
            sqlite3.Error: Si l'exécution du schéma échoue.
        """
        # Vérification que la connexion est établie
        if self._connection is None:
            raise RuntimeError("La connexion à la base de données n'est pas établie")
        
        # Exécution du script SQL
        # Pourquoi executescript : Permet d'exécuter plusieurs instructions SQL
        self._connection.executescript(schema_sql)
        
        # Commit des changements
        # Pourquoi : Le schéma doit être persisté immédiatement
        self._connection.commit()
    
    @contextmanager
    def transaction(self):
        """
        Context manager pour gérer une transaction avec commit automatique ou rollback en erreur.
        
        Ce context manager garantit que :
        - Si tout se passe bien, la transaction est commitée automatiquement
        - Si une exception survient, la transaction est rollbackée automatiquement
        - La connexion est toujours fermée proprement
        
        Pourquoi un context manager : Évite d'oublier le commit ou le rollback,
        rend le code plus sûr et plus lisible (pattern with).
        
        Yields:
            Le curseur SQLite pour exécuter des requêtes.
        
        Raises:
            sqlite3.Error: Propage les erreurs SQL après avoir rollbacké la transaction.
            Exception: Propage toute autre exception après avoir rollbacké la transaction.
        
        Example:
            with db.transaction() as cursor:
                cursor.execute("INSERT INTO eleve (nom, prenom) VALUES (?, ?)", ("Dupont", "Jean"))
                # Si une exception survient ici, rollback automatique
                cursor.execute("INSERT INTO paiement (...)")
                # Si on arrive ici, commit automatique
        """
        # Récupération de la connexion
        conn = self.connect()
        
        # Début explicite de la transaction
        # Pourquoi BEGIN IMMEDIATE : Verrouille la base en écriture immédiatement,
        # évitant les deadlocks si plusieurs transactions tentent d'écrire
        conn.execute("BEGIN IMMEDIATE")
        
        try:
            # Création d'un curseur
            cursor = conn.cursor()
            
            # Yield du curseur au code utilisateur
            # Le code utilisateur peut exécuter des requêtes avec ce curseur
            yield cursor
            
            # Si on arrive ici sans exception, commit de la transaction
            # Pourquoi commit : Valide toutes les modifications faites dans la transaction
            conn.commit()
            
        except Exception as e:
            # Si une exception survient, rollback de la transaction
            # Pourquoi rollback : Annule toutes les modifications pour laisser la base
            # dans un état cohérent (principe ACID : Atomicity)
            conn.rollback()
            
            # Propagation de l'exception au code appelant
            # Pourquoi : Le code appelant doit savoir que l'opération a échoué
            raise
    
    def close(self) -> None:
        """
        Ferme la connexion à la base de données.
        
        Pourquoi : Libère les ressources et ferme proprement le fichier de base de données.
        Doit être appelé avant de quitter l'application.
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """
        Support du context manager pour la connexion elle-même.
        
        Returns:
            L'instance Database elle-même.
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Ferme la connexion à la sortie du context manager.
        
        Args:
            exc_type: Type de l'exception (si any)
            exc_val: Valeur de l'exception (si any)
            exc_tb: Traceback de l'exception (si any)
        """
        self.close()
