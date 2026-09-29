# =============================================================================
# test_dashboard.py - Tests pour le tableau de bord
# =============================================================================
# Rôle : Tester la fonctionnalité de tableau de bord.
# =============================================================================
# Ce fichier utilise :
# - pytest pour les tests unitaires
# - data.database.Database pour la base de données en mémoire
# - services.dashboard_service.DashboardService pour les statistiques
# - services.student_service.StudentService pour créer des données de test
# =============================================================================
# Ce fichier est utilisé par :
# - pytest pour exécuter les tests
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/tests/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from edupaie.data.database import Database
from edupaie.services.dashboard_service import DashboardService
from edupaie.services.student_service import StudentService
from edupaie.services.payment_service import PaymentService


# ===== Fixtures =====

@pytest.fixture
def in_memory_db():
    """
    Crée une base de données en mémoire pour les tests.
    
    Pourquoi base en mémoire : Isolation complète entre les tests,
    vitesse d'exécution, nettoyage automatique après chaque test.
    
    Pourquoi nom unique : Évite les conflits si plusieurs tests s'exécutent
    en parallèle sur la même machine.
    
    Pourquoi file:?mode=memory : Crée une base en mémoire isolée pour ce test.
    
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
    Crée un service d'élèves pour les tests.
    """
    return StudentService(in_memory_db)


@pytest.fixture
def payment_service(student_service):
    """
    Crée un service de paiements pour les tests.
    """
    return PaymentService(student_service.database)


@pytest.fixture
def dashboard_service(student_service, payment_service):
    """
    Crée un service de tableau de bord pour les tests.
    """
    return DashboardService(
        student_service.repository,
        payment_service.payment_repository
    )


@pytest.fixture
def sample_classe(student_service):
    """
    Crée une classe de test.
    """
    # Insertion directe dans la base pour éviter les validations du service
    with student_service.database.transaction() as cursor:
        cursor.execute("INSERT INTO classe (nom) VALUES (?)", ("6ème A",))
        return cursor.lastrowid


@pytest.fixture
def sample_student(student_service, sample_classe):
    """
    Crée un élève de test.
    """
    student_id = student_service.create_student(
        nom="Dupont",
        prenom="Jean",
        classe_id=sample_classe,
        annee_scolaire="2024-2025",
        total_du=50000
    )
    return student_id


# ===== Tests =====

def test_dashboard_stats_base_vide(dashboard_service):
    """
    Test : Les statistiques sont correctes sur une base vide.
    
    Pourquoi ce test : Vérifie que le service gère correctement le cas
    d'une base vide (aucun élève, aucun paiement).
    """
    stats = dashboard_service.dashboard_stats()
    
    assert stats['nombre_eleves'] == 0
    assert stats['total_encaisse'] == 0
    assert stats['total_restant_du'] == 0
    assert stats['eleves_non_soldes'] == 0


def test_dashboard_stats_jeu_donnees(dashboard_service, student_service, sample_classe):
    """
    Test : Les statistiques sont exactes sur un jeu de données connu.
    
    Pourquoi ce test : Vérifie que les agrégations SQL calculent correctement
    les indicateurs sur un jeu de données contrôlé.
    
    Jeu de données :
    - 3 élèves : total_du = 50000, 30000, 40000
    - Paiements : 20000 (élève 1), 30000 (élève 2 soldé), 0 (élève 3)
    - Attendu : nombre_eleves = 3, total_encaisse = 50000, total_restant_du = 70000, non_soldes = 2
    """
    # Création de 3 élèves
    eleve1_id = student_service.create_student(
        nom="Dupont", prenom="Jean", classe_id=sample_classe,
        annee_scolaire="2024-2025", total_du=50000
    )
    eleve2_id = student_service.create_student(
        nom="Martin", prenom="Marie", classe_id=sample_classe,
        annee_scolaire="2024-2025", total_du=30000
    )
    eleve3_id = student_service.create_student(
        nom="Bernard", prenom="Pierre", classe_id=sample_classe,
        annee_scolaire="2024-2025", total_du=40000
    )
    
    # Paiements
    payment_service = PaymentService(student_service.database)
    payment_service.enregistrer_paiement(
        eleve_id=eleve1_id, montant=20000, date_paiement="2024-01-15", mode="especes"
    )
    payment_service.enregistrer_paiement(
        eleve_id=eleve2_id, montant=30000, date_paiement="2024-02-20", mode="cheque"
    )
    # élève3 : aucun paiement
    
    # Récupération des statistiques
    stats = dashboard_service.dashboard_stats()
    
    # Vérifications
    assert stats['nombre_eleves'] == 3
    assert stats['total_encaisse'] == 50000  # 20000 + 30000
    assert stats['total_restant_du'] == 70000  # (50000+30000+40000) - 50000
    assert stats['eleves_non_soldes'] == 2  # élève1 et élève3


def test_dashboard_stats_coherence(dashboard_service, student_service, sample_classe):
    """
    Test : La cohérence des données est vérifiée.
    
    Pourquoi ce test : Vérifie que le service détecte les anomalies
    (total_encaissé + total_restant_du != total_du).
    
    La cohérence est vérifiée par un assert dans dashboard_stats().
    Si les données sont cohérentes, aucune exception n'est levée.
    """
    # Création d'un élève
    student_service.create_student(
        nom="Dupont", prenom="Jean", classe_id=sample_classe,
        annee_scolaire="2024-2025", total_du=50000
    )
    
    # Récupération des statistiques (ne doit pas lever d'exception)
    stats = dashboard_service.dashboard_stats()
    
    # Vérification de la cohérence
    assert stats['total_encaisse'] + stats['total_restant_du'] == 50000


def test_dashboard_stats_apres_paiement(dashboard_service, payment_service, sample_student):
    """
    Test : Les statistiques sont mises à jour après un paiement.
    
    Pourquoi ce test : Vérifie que les KPI reflètent le nouveau paiement
    (total_encaissé augmente, total_restant_du diminue).
    """
    # Statistiques avant paiement
    stats_avant = dashboard_service.dashboard_stats()
    assert stats_avant['total_encaisse'] == 0
    assert stats_avant['total_restant_du'] == 50000
    
    # Paiement de 10000
    payment_service.enregistrer_paiement(
        eleve_id=sample_student, montant=10000, date_paiement="2024-01-15", mode="especes"
    )
    
    # Statistiques après paiement
    stats_apres = dashboard_service.dashboard_stats()
    
    # Vérifications
    assert stats_apres['total_encaisse'] == 10000
    assert stats_apres['total_restant_du'] == 40000
    assert stats_apres['eleves_non_soldes'] == 1  # solde > 0


def test_dashboard_stats_solidation(dashboard_service, student_service, sample_classe):
    """
    Test : Le nombre d'élèves non soldés diminue après soldation.
    
    Pourquoi ce test : Vérifie que le comptage des élèves non soldés
    est correctement mis à jour quand un élève devient soldé.
    """
    # Création de 2 élèves
    eleve1_id = student_service.create_student(
        nom="Dupont", prenom="Jean", classe_id=sample_classe,
        annee_scolaire="2024-2025", total_du=50000
    )
    eleve2_id = student_service.create_student(
        nom="Martin", prenom="Marie", classe_id=sample_classe,
        annee_scolaire="2024-2025", total_du=30000
    )
    
    payment_service = PaymentService(student_service.database)
    
    # Avant paiement : 2 non soldés
    stats_avant = dashboard_service.dashboard_stats()
    assert stats_avant['eleves_non_soldes'] == 2
    
    # Soldat de l'élève 1
    payment_service.enregistrer_paiement(
        eleve_id=eleve1_id, montant=50000, date_paiement="2024-01-15", mode="especes"
    )
    
    # Après paiement : 1 non soldé (élève 2)
    stats_apres = dashboard_service.dashboard_stats()
    assert stats_apres['eleves_non_soldes'] == 1
