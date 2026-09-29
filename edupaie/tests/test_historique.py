# =============================================================================
# test_historique.py - Tests pour l'historique des paiements
# =============================================================================
# Rôle : Tester la fonctionnalité d'historique des paiements.
# =============================================================================
# Ce fichier utilise :
# - pytest pour les tests unitaires
# - data.database.Database pour la base de données en mémoire
# - data.payment_repository.PaymentRepository pour l'accès aux données
# - services.payment_service.PaymentService pour la logique métier
# - services.student_service.StudentService pour la gestion des élèves
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/tests/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from edupaie.data.database import Database
from edupaie.data.payment_repository import PaymentRepository
from edupaie.data.student_repository import StudentRepository
from edupaie.services.payment_service import PaymentService
from edupaie.services.student_service import StudentService
from edupaie.services.exceptions import NotFoundError


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
def payment_service(in_memory_db):
    """
    Crée un service de paiements pour les tests.
    """
    return PaymentService(in_memory_db)


@pytest.fixture
def sample_classe(payment_service):
    """
    Crée une classe de test.
    """
    # Insertion directe dans la base pour éviter les validations du service
    with payment_service.database.transaction() as cursor:
        cursor.execute("INSERT INTO classe (nom) VALUES (?)", ("6ème A",))
        return cursor.lastrowid


@pytest.fixture
def sample_student(payment_service, sample_classe):
    """
    Crée un élève de test.
    """
    student_id = payment_service.student_service.create_student(
        nom="Dupont",
        prenom="Jean",
        classe_id=sample_classe,
        annee_scolaire="2024-2025",
        total_du=50000
    )
    return student_id


# ===== Tests =====

def test_historique_ordre_chronologique(payment_service, sample_student):
    """
    Test : L'historique est trié chronologiquement (du plus ancien au plus récent).
    
    Pourquoi ce test : Vérifie que l'historique respecte l'ordre chronologique,
    ce qui est essentiel pour comprendre l'évolution des paiements.
    """
    # Création de trois paiements à des dates différentes
    payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-01-15",
        mode="especes"
    )
    payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=20000,
        date_paiement="2024-02-20",
        mode="cheque"
    )
    payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=15000,
        date_paiement="2024-03-10",
        mode="virement"
    )
    
    # Récupération de l'historique
    historique = payment_service.historique(sample_student)
    
    # Vérification de l'ordre chronologique
    assert len(historique) == 3
    assert historique[0]['date_paiement'] == "2024-01-15"
    assert historique[1]['date_paiement'] == "2024-02-20"
    assert historique[2]['date_paiement'] == "2024-03-10"


def test_historique_meme_meme_date(payment_service, sample_student):
    """
    Test : Les paiements du même jour sont triés par ID.
    
    Pourquoi ce test : Vérifie que l'ordre est stable même si plusieurs paiements
    ont été effectués le même jour (tri par ID après la date).
    """
    # Création de deux paiements le même jour
    paiement1 = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-01-15",
        mode="especes"
    )
    paiement2 = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=20000,
        date_paiement="2024-01-15",
        mode="cheque"
    )
    
    # Récupération de l'historique
    historique = payment_service.historique(sample_student)
    
    # Vérification que l'ordre respecte l'ID (le premier créé en premier)
    assert len(historique) == 2
    assert historique[0]['id'] == paiement1['id']
    assert historique[1]['id'] == paiement2['id']


def test_historique_eleve_sans_paiement(payment_service, sample_student):
    """
    Test : L'historique d'un élève sans paiement est vide.
    
    Pourquoi ce test : Vérifie que l'historique ne contient aucun paiement
    si l'élève n'a jamais payé.
    """
    # Récupération de l'historique sans paiement
    historique = payment_service.historique(sample_student)
    
    # Vérification que l'historique est vide
    assert len(historique) == 0


def test_historique_eleve_inexistant(payment_service):
    """
    Test : L'historique d'un élève inexistant lève NotFoundError.
    
    Pourquoi ce test : Vérifie que la méthode vérifie l'existence de l'élève
    avant de retourner l'historique, évitant de retourner un historique vide
    pour un élève qui n'existe pas.
    """
    # Tentative de récupération de l'historique d'un élève inexistant
    with pytest.raises(NotFoundError) as exc_info:
        payment_service.historique(999999)
    
    # Vérification du message d'erreur
    assert "Aucun élève trouvé" in str(exc_info.value)


def test_historique_donnees_completes(payment_service, sample_student):
    """
    Test : L'historique contient toutes les données nécessaires.
    
    Pourquoi ce test : Vérifie que toutes les informations du paiement sont
    présentes dans l'historique (id, numero_recu, date, mode, montant, solde_apres).
    """
    # Création d'un paiement
    payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=15000,
        date_paiement="2024-01-15",
        mode="especes"
    )
    
    # Récupération de l'historique
    historique = payment_service.historique(sample_student)
    
    # Vérification que toutes les données sont présentes
    assert len(historique) == 1
    paiement = historique[0]
    assert 'id' in paiement
    assert 'numero_recu' in paiement
    assert 'date_paiement' in paiement
    assert 'mode' in paiement
    assert 'montant' in paiement
    assert 'solde_apres' in paiement


def test_historique_solde_apres_correct(payment_service, sample_student):
    """
    Test : Le solde_apres dans l'historique est correct.
    
    Pourquoi ce test : Vérifie que le solde après paiement est figé correctement
    dans l'historique, ce qui est essentiel pour l'audit et la traçabilité.
    """
    # Élève avec total_du = 50000
    # Premier paiement de 10000 -> solde_apres = 40000
    payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-01-15",
        mode="especes"
    )
    
    # Deuxième paiement de 20000 -> solde_apres = 20000
    payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=20000,
        date_paiement="2024-02-20",
        mode="cheque"
    )
    
    # Récupération de l'historique
    historique = payment_service.historique(sample_student)
    
    # Vérification des soldes après
    assert historique[0]['solde_apres'] == 40000
    assert historique[1]['solde_apres'] == 20000


def test_historique_numero_recu_unique(payment_service, sample_student):
    """
    Test : Chaque paiement dans l'historique a un numéro de reçu unique.
    
    Pourquoi ce test : Vérifie que les numéros de reçu sont uniques, ce qui est
    essentiel pour l'identification administrative des paiements.
    """
    # Création de trois paiements
    payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-01-15",
        mode="especes"
    )
    payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=20000,
        date_paiement="2024-02-20",
        mode="cheque"
    )
    payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=15000,
        date_paiement="2024-03-10",
        mode="virement"
    )
    
    # Récupération de l'historique
    historique = payment_service.historique(sample_student)
    
    # Vérification que les numéros de reçu sont uniques
    numeros_recu = [p['numero_recu'] for p in historique]
    assert len(numeros_recu) == len(set(numeros_recu))


def test_historique_plusieurs_eleves(payment_service, sample_classe):
    """
    Test : L'historique est bien isolé par élève.
    
    Pourquoi ce test : Vérifie que l'historique d'un élève ne contient que
    ses propres paiements, pas ceux des autres élèves.
    """
    # Création de deux élèves
    eleve1_id = payment_service.student_service.create_student(
        nom="Dupont",
        prenom="Jean",
        classe_id=sample_classe,
        annee_scolaire="2024-2025",
        total_du=50000
    )
    eleve2_id = payment_service.student_service.create_student(
        nom="Martin",
        prenom="Marie",
        classe_id=sample_classe,
        annee_scolaire="2024-2025",
        total_du=60000
    )
    
    # Paiements pour l'élève 1
    payment_service.enregistrer_paiement(
        eleve_id=eleve1_id,
        montant=10000,
        date_paiement="2024-01-15",
        mode="especes"
    )
    
    # Paiements pour l'élève 2
    payment_service.enregistrer_paiement(
        eleve_id=eleve2_id,
        montant=20000,
        date_paiement="2024-02-20",
        mode="cheque"
    )
    
    # Récupération des historiques
    historique1 = payment_service.historique(eleve1_id)
    historique2 = payment_service.historique(eleve2_id)
    
    # Vérification de l'isolation
    assert len(historique1) == 1
    assert len(historique2) == 1
    assert historique1[0]['montant'] == 10000
    assert historique2[0]['montant'] == 20000
