# =============================================================================
# test_solde.py - Tests pour le calcul du solde et des statuts
# =============================================================================
# Rôle : Tests unitaires pour le calcul automatique du solde et des statuts.
# =============================================================================
# Ce fichier utilise :
# - pytest pour le framework de tests
# - data.database.Database pour la connexion à la base de données (en mémoire)
# - services.student_service pour la logique métier
# =============================================================================
# Ce fichier est utilisé par :
# - pytest pour exécuter les tests
# =============================================================================

import sys
from pathlib import Path
import pytest

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/tests/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from edupaie.data.database import Database
from edupaie.services.student_service import StudentService


# ===== Fixtures =====

@pytest.fixture
def in_memory_db():
    """
    Fixture qui crée une base de données en mémoire pour les tests.
    
    Pourquoi une base en mémoire : Les tests doivent être isolés et rapides.
    Une base en mémoire est créée pour chaque test et détruite après,
    évitant toute pollution entre les tests.
    
    Pourquoi un nom unique : Chaque test doit avoir sa propre
    base en mémoire pour éviter les interférences. SQLite utilise le même
    objet mémoire pour \":memory:\" dans la même connexion, donc on utilise
    un nom unique avec file:mode=memory.
    
    Returns:
        Instance de Database connectée à une base en mémoire.
    """
    # Création d'une base en mémoire avec un nom unique
    import uuid
    db_name = f"file:test_{uuid.uuid4()}?mode=memory&cache=shared"
    db = Database(db_name)
    
    # Initialisation du schéma (automatique via Database.connect())
    db.connect()
    
    yield db
    
    # Nettoyage : fermeture de la connexion
    db.close()


@pytest.fixture
def student_service(in_memory_db):
    """
    Fixture qui crée un service d'élèves avec une base en mémoire.
    
    Returns:
        Instance de StudentService connectée à la base de test.
    """
    return StudentService(in_memory_db)


@pytest.fixture
def sample_classe(student_service):
    """
    Fixture qui crée une classe de test.
    
    Returns:
        L'ID de la classe créée.
    """
    # Insertion directe dans la base pour éviter les validations du service
    with student_service.database.transaction() as cursor:
        cursor.execute("INSERT INTO classe (nom) VALUES (?)", ("6ème A",))
        return cursor.lastrowid


@pytest.fixture
def sample_student(student_service, sample_classe):
    """
    Fixture qui crée un élève de test.
    
    Returns:
        L'ID de l'élève créé.
    """
    return student_service.create_student(
        nom="Dupont",
        prenom="Jean",
        classe_id=sample_classe,
        annee_scolaire="2024-2025",
        total_du=50000
    )


# ===== Tests : Calcul du solde =====

def test_solde_sans_paiement(student_service, sample_student):
    """
    Test : Solde d'un élève sans paiement.
    
    Règle vérifiée : solde = total_du - 0 = total_du.
    
    Pourquoi ce test : Vérifie le cas nominal d'un élève qui n'a encore rien payé.
    """
    solde = student_service.solde(sample_student)
    assert solde == 50000  # total_du


def test_solde_partiellement_paye(student_service, sample_student):
    """
    Test : Solde d'un élève partiellement payé.
    
    Règle vérifiée : solde = total_du - total_paye.
    
    Pourquoi ce test : Vérifie que le solde diminue correctement avec les paiements.
    """
    # Ajout d'un paiement de 20 000
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_student, 20000, "2024-09-15", "especes", "REC-2024-000001", 30000)
        )
    
    solde = student_service.solde(sample_student)
    assert solde == 30000  # 50000 - 20000


def test_solde_soldé(student_service, sample_student):
    """
    Test : Solde d'un élève soldé.
    
    Règle vérifiée : solde = 0 quand total_paye = total_du.
    
    Pourquoi ce test : Vérifie que le solde est 0 quand l'élève a tout payé.
    """
    # Ajout d'un paiement complet
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_student, 50000, "2024-09-15", "especes", "REC-2024-000001", 0)
        )
    
    solde = student_service.solde(sample_student)
    assert solde == 0


def test_solde_total_du_zero(student_service, sample_classe):
    """
    Test : Solde d'un élève avec total_du = 0.
    
    Règle vérifiée : solde = total_du - total_paye (peut être négatif).
    
    Pourquoi ce test : Vérifie le cas limite où l'élève n'a rien à payer.
    Si des paiements existent, le solde devient négatif (remboursement dû).
    """
    # Création d'un élève avec total_du = 0
    student_id = student_service.create_student(
        nom="Test",
        prenom="Test",
        classe_id=sample_classe,
        annee_scolaire="2024-2025",
        total_du=0
    )
    
    # Ajout d'un paiement (anomalie métier, mais gérée)
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (student_id, 10000, "2024-09-15", "especes", "REC-2024-000001", -10000)
        )
    
    solde = student_service.solde(student_id)
    assert solde == -10000  # total_du - total_paye = 0 - 10000 = -10000 (remboursement dû)


# ===== Tests : Détermination du statut =====

def test_statut_sans_paiement(student_service, sample_student):
    """
    Test : Statut d'un élève sans paiement.
    
    Règle vérifiée : "Non payé" quand aucun paiement.
    
    Pourquoi ce test : Vérifie que le statut est correct pour un élève qui n'a rien payé.
    """
    statut = student_service.statut(sample_student)
    assert statut == "Non payé"


def test_statut_partiellement_paye(student_service, sample_student):
    """
    Test : Statut d'un élève partiellement payé.
    
    Règle vérifiée : "Partiellement payé" quand solde > 0 et au moins un paiement.
    
    Pourquoi ce test : Vérifie que le statut est correct quand l'élève a payé une partie.
    """
    # Ajout d'un paiement partiel
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_student, 20000, "2024-09-15", "especes", "REC-2024-000001", 30000)
        )
    
    statut = student_service.statut(sample_student)
    assert statut == "Partiellement payé"


def test_statut_soldé(student_service, sample_student):
    """
    Test : Statut d'un élève soldé.
    
    Règle vérifiée : "Soldé" quand solde = 0.
    
    Pourquoi ce test : Vérifie que le statut est correct quand l'élève a tout payé.
    """
    # Ajout d'un paiement complet
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_student, 50000, "2024-09-15", "especes", "REC-2024-000001", 0)
        )
    
    statut = student_service.statut(sample_student)
    assert statut == "Soldé"


def test_statut_total_du_zero(student_service, sample_classe):
    """
    Test : Statut d'un élève avec total_du = 0.
    
    Règle vérifiée : "Soldé" quand total_du = 0 (même sans paiements).
    
    Pourquoi ce test : Vérifie le cas limite où l'élève n'a rien à payer.
    S'il n'a rien à payer, il est considéré comme soldé.
    """
    # Création d'un élève avec total_du = 0
    student_id = student_service.create_student(
        nom="Test",
        prenom="Test",
        classe_id=sample_classe,
        annee_scolaire="2024-2025",
        total_du=0
    )
    
    statut = student_service.statut(student_id)
    assert statut == "Soldé"  # solde = 0 -> Soldé


def test_statut_ordre_decision(student_service, sample_student):
    """
    Test : Ordre de décision du statut.
    
    Règle vérifiée : solde=0 est prioritaire sur aucun paiement.
    
    Pourquoi ce test : Vérifie que l'ordre de décision est correct :
    1. solde=0 -> Soldé (prioritaire)
    2. aucun paiement -> Non payé
    3. sinon -> Partiellement payé
    """
    # Ajout d'un paiement complet (solde = 0)
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_student, 50000, "2024-09-15", "especes", "REC-2024-000001", 0)
        )
    
    statut = student_service.statut(sample_student)
    assert statut == "Soldé"  # solde=0 l'emporte sur nombre_paiements > 0


# ===== Tests : Recherche avec filtre par statut =====

def test_search_by_statut_soldé(student_service, sample_student):
    """
    Test : Recherche filtrée par statut "Soldé".
    
    Règle vérifiée : Le filtre par statut fonctionne correctement.
    
    Pourquoi ce test : Vérifie que la recherche ne retourne que les élèves
    avec le statut demandé.
    """
    # Ajout d'un paiement complet pour soldé
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_student, 50000, "2024-09-15", "especes", "REC-2024-000001", 0)
        )
    
    # Recherche par statut "Soldé"
    results = student_service.search_students_with_solde(statut="Soldé")
    assert len(results) == 1
    assert results[0]['id'] == sample_student
    assert results[0]['statut'] == "Soldé"


def test_search_by_statut_non_paye(student_service, sample_classe):
    """
    Test : Recherche filtrée par statut "Non payé".
    
    Règle vérifiée : Le filtre par statut ne retourne que les élèves non payés.
    
    Pourquoi ce test : Vérifie que la recherche ne retourne que les élèves
    sans paiement.
    """
    # Création d'un élève non payé
    student_id = student_service.create_student(
        nom="Martin",
        prenom="Marie",
        classe_id=sample_classe,
        annee_scolaire="2024-2025",
        total_du=50000
    )
    
    # Recherche par statut "Non payé"
    results = student_service.search_students_with_solde(statut="Non payé")
    assert len(results) == 1
    assert results[0]['id'] == student_id
    assert results[0]['statut'] == "Non payé"


def test_search_by_statut_partiel(student_service, sample_student):
    """
    Test : Recherche filtrée par statut "Partiellement payé".
    
    Règle vérifiée : Le filtre par statut ne retourne que les élèves partiellement payés.
    
    Pourquoi ce test : Vérifie que la recherche ne retourne que les élèves
    avec des paiements mais solde > 0.
    """
    # Ajout d'un paiement partiel
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_student, 20000, "2024-09-15", "especes", "REC-2024-000001", 30000)
        )
    
    # Recherche par statut "Partiellement payé"
    results = student_service.search_students_with_solde(statut="Partiellement payé")
    assert len(results) == 1
    assert results[0]['id'] == sample_student
    assert results[0]['statut'] == "Partiellement payé"


def test_search_with_texte_classe_et_statut(student_service, sample_student, sample_classe):
    """
    Test : Recherche combinée (texte, classe, statut).
    
    Règle vérifiée : Les filtres peuvent être combinés.
    
    Pourquoi ce test : Vérifie que la recherche fonctionne avec
    plusieurs filtres à la fois.
    """
    # Ajout d'un paiement partiel
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_student, 20000, "2024-09-15", "especes", "REC-2024-000001", 30000)
        )
    
    # Recherche combinée
    results = student_service.search_students_with_solde(
        texte="Dupont",
        classe_id=sample_classe,
        statut="Partiellement payé"
    )
    
    assert len(results) == 1
    assert results[0]['id'] == sample_student
    assert results[0]['statut'] == "Partiellement payé"
