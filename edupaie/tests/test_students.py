# =============================================================================
# test_students.py - Tests pour la gestion des élèves
# =============================================================================
# Rôle : Tests unitaires et d'intégration pour la gestion des élèves.
# =============================================================================
# Ce fichier utilise :
# - pytest pour le framework de tests
# - data.database.Database pour la connexion à la base de données (en mémoire)
# - services.student_service pour la logique métier
# - services.exceptions pour vérifier les exceptions levées
# =============================================================================
# Ce fichier est utilisé par :
# - pytest pour exécuter les tests
# =============================================================================

import sys
from pathlib import Path
import pytest
import sqlite3

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/tests/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from edupaie.data.database import Database
from edupaie.services.student_service import StudentService
from edupaie.services.exceptions import ValidationError, NotFoundError, BusinessRuleError


# ===== Fixtures =====

@pytest.fixture
def in_memory_db():
    """
    Fixture qui crée une base de données en mémoire pour les tests.
    
    Pourquoi une base en mémoire : Les tests doivent être isolés et rapides.
    Une base en mémoire est créée pour chaque test et détruite après,
    évitant toute pollution entre les tests.
    
    Pourquoi un nom unique pour :memory: : Chaque test doit avoir sa propre
    base en mémoire pour éviter les interférences. SQLite utilise le même
    objet mémoire pour ":memory:" dans la même connexion, donc on utilise
    un nom unique avec file:mode=memory.
    
    Returns:
        Instance de Database connectée à une base en mémoire.
    """
    # Création d'une base en mémoire avec un nom unique
    # Pourquoi file:?mode=memory : Crée une base en mémoire isolée pour ce test
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


# ===== Tests : Création d'élève =====

def test_create_student_success(student_service, sample_classe):
    """
    Test : Création réussie d'un élève.
    
    Règle vérifiée : Un élève peut être créé avec des données valides.
    
    Pourquoi ce test : Vérifie le chemin nominal de création d'élève.
    """
    # Création de l'élève
    student_id = student_service.create_student(
        nom="Martin",
        prenom="Marie",
        classe_id=sample_classe,
        annee_scolaire="2024-2025",
        total_du=50000
    )
    
    # Vérification que l'ID est retourné
    assert student_id > 0
    
    # Vérification que l'élève existe dans la base
    student = student_service.get_student(student_id)
    assert student is not None
    assert student['nom'] == "Martin"
    assert student['prenom'] == "Marie"
    assert student['classe_id'] == sample_classe
    assert student['annee_scolaire'] == "2024-2025"
    assert student['total_du'] == 50000


def test_create_student_empty_nom(student_service, sample_classe):
    """
    Test : Validation refusée - nom vide.
    
    Règle vérifiée : Le nom ne peut pas être vide.
    Message attendu : "Le nom ne peut pas être vide."
    
    Pourquoi ce test : Vérifie que la validation des champs vides fonctionne.
    """
    with pytest.raises(ValidationError) as exc_info:
        student_service.create_student(
            nom="",
            prenom="Jean",
            classe_id=sample_classe,
            annee_scolaire="2024-2025",
            total_du=50000
        )
    
    assert "nom ne peut pas être vide" in str(exc_info.value.message).lower()


def test_create_student_short_nom(student_service, sample_classe):
    """
    Test : Validation refusée - nom trop court.
    
    Règle vérifiée : Le nom doit contenir au moins 2 caractères.
    Message attendu : "Le nom doit contenir au moins 2 caractères."
    
    Pourquoi ce test : Vérifie que la validation de longueur minimale fonctionne.
    """
    with pytest.raises(ValidationError) as exc_info:
        student_service.create_student(
            nom="A",
            prenom="Jean",
            classe_id=sample_classe,
            annee_scolaire="2024-2025",
            total_du=50000
        )
    
    assert "au moins 2 caractères" in str(exc_info.value.message).lower()


def test_create_student_empty_prenom(student_service, sample_classe):
    """
    Test : Validation refusée - prénom vide.
    
    Règle vérifiée : Le prénom ne peut pas être vide.
    Message attendu : "Le prénom ne peut pas être vide."
    
    Pourquoi ce test : Vérifie que la validation du prénom fonctionne.
    """
    with pytest.raises(ValidationError) as exc_info:
        student_service.create_student(
            nom="Dupont",
            prenom="",
            classe_id=sample_classe,
            annee_scolaire="2024-2025",
            total_du=50000
        )
    
    assert "prénom ne peut pas être vide" in str(exc_info.value.message).lower()


def test_create_student_invalid_classe(student_service):
    """
    Test : Validation refusée - classe inexistante.
    
    Règle vérifiée : La classe doit exister dans la base de données.
    Message attendu : "La classe sélectionnée n'existe pas."
    
    Pourquoi ce test : Vérifie que la validation de l'intégrité référentielle fonctionne.
    """
    with pytest.raises(ValidationError) as exc_info:
        student_service.create_student(
            nom="Dupont",
            prenom="Jean",
            classe_id=999,  # ID qui n'existe pas
            annee_scolaire="2024-2025",
            total_du=50000
        )
    
    assert "classe" in str(exc_info.value.message).lower() and "existe pas" in str(exc_info.value.message).lower()


def test_create_student_invalid_annee_format(student_service, sample_classe):
    """
    Test : Validation refusée - format d'année invalide.
    
    Règle vérifiée : L'année scolaire doit être au format YYYY-YYYY ou YYYY/YYYY.
    Message attendu : "L'année scolaire doit être au format YYYY-YYYY ou YYYY/YYYY"
    
    Pourquoi ce test : Vérifie que la validation du format de l'année fonctionne.
    """
    with pytest.raises(ValidationError) as exc_info:
        student_service.create_student(
            nom="Dupont",
            prenom="Jean",
            classe_id=sample_classe,
            annee_scolaire="2024",  # Format invalide
            total_du=50000
        )
    
    assert "format" in str(exc_info.value.message).lower()


def test_create_student_invalid_annee_consecutive(student_service, sample_classe):
    """
    Test : Validation refusée - années non consécutives.
    
    Règle vérifiée : L'année scolaire doit couvrir deux années consécutives.
    Message attendu : "L'année scolaire doit couvrir deux années consécutives"
    
    Pourquoi ce test : Vérifie que la validation de la logique des années fonctionne.
    """
    with pytest.raises(ValidationError) as exc_info:
        student_service.create_student(
            nom="Dupont",
            prenom="Jean",
            classe_id=sample_classe,
            annee_scolaire="2024-2026",  # Années non consécutives
            total_du=50000
        )
    
    assert "consécutives" in str(exc_info.value.message).lower()


def test_create_student_negative_total(student_service, sample_classe):
    """
    Test : Validation refusée - total dû négatif.
    
    Règle vérifiée : Le total dû doit être un entier positif ou nul.
    Message attendu : "Le montant total dû ne peut pas être négatif."
    
    Pourquoi ce test : Vérifie que la validation du montant fonctionne.
    """
    with pytest.raises(ValidationError) as exc_info:
        student_service.create_student(
            nom="Dupont",
            prenom="Jean",
            classe_id=sample_classe,
            annee_scolaire="2024-2025",
            total_du=-1000  # Montant négatif
        )
    
    assert "négatif" in str(exc_info.value.message).lower()


# ===== Tests : Modification d'élève =====

def test_update_student_success(student_service, sample_student, sample_classe):
    """
    Test : Modification réussie d'un élève.
    
    Règle vérifiée : Un élève peut être modifié avec des données valides.
    
    Pourquoi ce test : Vérifie le chemin nominal de modification d'élève.
    """
    # Modification de l'élève
    student_service.update_student(
        eleve_id=sample_student,
        nom="Durand",
        prenom="Pierre",
        classe_id=sample_classe,
        annee_scolaire="2025-2026",
        total_du=60000
    )
    
    # Vérification que les modifications ont été appliquées
    student = student_service.get_student(sample_student)
    assert student['nom'] == "Durand"
    assert student['prenom'] == "Pierre"
    assert student['annee_scolaire'] == "2025-2026"
    assert student['total_du'] == 60000


def test_update_student_not_found(student_service):
    """
    Test : Modification refusée - élève inexistant.
    
    Règle vérifiée : Impossible de modifier un élève qui n'existe pas.
    Exception attendue : NotFoundError
    
    Pourquoi ce test : Vérifie que la vérification d'existence fonctionne.
    """
    with pytest.raises(NotFoundError) as exc_info:
        student_service.update_student(
            eleve_id=999,  # ID qui n'existe pas
            nom="Dupont",
            prenom="Jean",
            classe_id=1,
            annee_scolaire="2024-2025",
            total_du=50000
        )
    
    assert "élève" in str(exc_info.value.message).lower() or "identifiant" in str(exc_info.value.message).lower()


def test_update_student_validation_empty_nom(student_service, sample_student):
    """
    Test : Modification refusée - nom vide.
    
    Règle vérifiée : Le nom ne peut pas être vide lors de la modification.
    
    Pourquoi ce test : Vérifie que les validations s'appliquent aussi à la modification.
    """
    with pytest.raises(ValidationError):
        student_service.update_student(
            eleve_id=sample_student,
            nom="",  # Nom vide
            prenom="Jean",
            classe_id=1,
            annee_scolaire="2024-2025",
            total_du=50000
        )


# ===== Tests : Suppression d'élève =====

def test_delete_student_success(student_service, sample_student):
    """
    Test : Suppression réussie d'un élève.
    
    Règle vérifiée : Un élève sans paiements peut être supprimé.
    
    Pourquoi ce test : Vérifie le chemin nominal de suppression d'élève.
    """
    # Suppression de l'élève
    student_service.delete_student(sample_student)
    
    # Vérification que l'élève n'existe plus
    with pytest.raises(NotFoundError):
        student_service.get_student(sample_student)


def test_delete_student_not_found(student_service):
    """
    Test : Suppression refusée - élève inexistant.
    
    Règle vérifiée : Impossible de supprimer un élève qui n'existe pas.
    Exception attendue : NotFoundError
    
    Pourquoi ce test : Vérifie que la vérification d'existence fonctionne avant suppression.
    """
    with pytest.raises(NotFoundError):
        student_service.delete_student(999)  # ID qui n'existe pas


def test_delete_student_with_payments(student_service, sample_student):
    """
    Test : Suppression refusée - élève avec paiements.
    
    Règle vérifiée : Impossible de supprimer un élève qui a des paiements.
    Exception attendue : BusinessRuleError
    Message attendu : Contient "paiements"
    
    Pourquoi ce test : Vérifie que la contrainte ON DELETE RESTRICT fonctionne
    et que le service lève une BusinessRuleError appropriée.
    """
    # Ajout d'un paiement pour l'élève
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO paiement 
               (eleve_id, montant, date_paiement, mode, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_student, 25000, "2024-09-15", "especes", "REC-2024-000001", 25000)
        )
    
    # Tentative de suppression
    with pytest.raises(BusinessRuleError) as exc_info:
        student_service.delete_student(sample_student)
    
    assert "paiement" in str(exc_info.value.message).lower()


# ===== Tests : Recherche et filtrage =====

def test_search_students_by_text(student_service, sample_student):
    """
    Test : Recherche par texte (nom).
    
    Règle vérifiée : La recherche par texte fonctionne (insensible à la casse).
    
    Pourquoi ce test : Vérifie que la recherche LIKE avec LOWER() fonctionne.
    """
    # Recherche par nom
    results = student_service.search_students("dupont")
    assert len(results) == 1
    assert results[0]['id'] == sample_student
    
    # Recherche insensible à la casse
    results = student_service.search_students("DUPONT")
    assert len(results) == 1
    
    # Recherche partielle
    results = student_service.search_students("Dup")
    assert len(results) == 1


def test_search_students_by_class(student_service, sample_student, sample_classe):
    """
    Test : Filtrage par classe.
    
    Règle vérifiée : Le filtrage par classe fonctionne.
    
    Pourquoi ce test : Vérifie que le filtre par classe_id fonctionne.
    """
    # Création d'un autre élève dans une autre classe
    with student_service.database.transaction() as cursor:
        cursor.execute("INSERT INTO classe (nom) VALUES (?)", ("6ème B",))
        classe_b_id = cursor.lastrowid
        cursor.execute(
            """INSERT INTO eleve (nom, prenom, classe_id, annee_scolaire, total_du)
               VALUES (?, ?, ?, ?, ?)""",
            ("Martin", "Marie", classe_b_id, "2024-2025", 50000)
        )
        student_b_id = cursor.lastrowid
    
    # Filtrage par classe A
    results = student_service.search_students("", classe_id=sample_classe)
    assert len(results) == 1
    assert results[0]['id'] == sample_student
    
    # Filtrage par classe B
    results = student_service.search_students("", classe_id=classe_b_id)
    assert len(results) == 1
    assert results[0]['id'] == student_b_id


def test_search_students_combined(student_service, sample_student, sample_classe):
    """
    Test : Recherche combinée (texte + classe).
    
    Règle vérifiée : La recherche combinée texte et classe fonctionne.
    
    Pourquoi ce test : Vérifie que les deux filtres peuvent être combinés.
    """
    # Recherche combinée
    results = student_service.search_students("dupont", classe_id=sample_classe)
    assert len(results) == 1
    assert results[0]['id'] == sample_student


def test_list_all_students(student_service, sample_student):
    """
    Test : Liste de tous les élèves.
    
    Règle vérifiée : La liste de tous les élèves fonctionne.
    
    Pourquoi ce test : Vérifie que list_all_students retourne tous les élèves.
    """
    # Création d'un deuxième élève
    with student_service.database.transaction() as cursor:
        cursor.execute(
            """INSERT INTO eleve (nom, prenom, classe_id, annee_scolaire, total_du)
               VALUES (?, ?, ?, ?, ?)""",
            ("Martin", "Marie", 1, "2024-2025", 50000)
        )
    
    # Liste de tous les élèves
    results = student_service.list_all_students()
    assert len(results) >= 2  # Au moins les deux élèves créés


def test_list_classes(student_service):
    """
    Test : Liste des classes.
    
    Règle vérifiée : La liste des classes fonctionne.
    
    Pourquoi ce test : Vérifie que list_classes retourne toutes les classes.
    """
    # Création de classes
    with student_service.database.transaction() as cursor:
        cursor.execute("INSERT INTO classe (nom) VALUES (?)", ("6ème A",))
        cursor.execute("INSERT INTO classe (nom) VALUES (?)", ("6ème B",))
    
    # Liste des classes
    classes = student_service.list_classes()
    assert len(classes) >= 2
    assert any(c['nom'] == "6ème A" for c in classes)
    assert any(c['nom'] == "6ème B" for c in classes)


def test_get_student_with_class_name(student_service, sample_student):
    """
    Test : Récupération d'élève avec nom de classe.
    
    Règle vérifiée : La transformation classe_id -> nom_classe fonctionne.
    
    Pourquoi ce test : Vérifie que get_student_with_class_name remplace
    l'ID de classe par son nom pour l'affichage.
    """
    student = student_service.get_student_with_class_name(sample_student)
    
    assert student is not None
    assert 'nom_classe' in student
    assert 'classe_id' not in student
    assert student['nom_classe'] == "6ème A"