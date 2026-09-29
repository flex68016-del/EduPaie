# =============================================================================
# test_payments.py - Tests pour l'enregistrement des paiements
# =============================================================================
# Rôle : Tests unitaires pour l'enregistrement des paiements.
# =============================================================================
# Ce fichier utilise :
# - pytest pour le framework de tests
# - data.database.Database pour la connexion à la base de données (en mémoire)
# - services.payment_service pour la logique métier
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
from edupaie.services.payment_service import PaymentService
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
    base en mémoire pour éviter les interférences.
    
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
def payment_service(in_memory_db):
    """
    Fixture qui crée un service de paiement avec une base en mémoire.
    
    Returns:
        Instance de PaymentService connectée à la base de test.
    """
    return PaymentService(in_memory_db)


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
    Fixture qui crée un élève de test avec un solde de 50000.
    
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


# ===== Tests : Paiement valide =====

def test_paiement_valide(payment_service, sample_student):
    """
    Test : Enregistrement d'un paiement valide.
    
    Règle vérifiée : Un paiement valide est enregistré avec succès.
    
    Pourquoi ce test : Vérifie le cas nominal d'un paiement correct.
    """
    paiement = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=20000,
        date_paiement="2024-09-15",
        mode="especes"
    )
    
    assert paiement is not None
    assert paiement['montant'] == 20000
    assert paiement['date_paiement'] == "2024-09-15"
    assert paiement['mode'] == "especes"
    assert paiement['solde_apres'] == 30000  # 50000 - 20000
    assert paiement['numero_recu'].startswith("REC-2024-")


# ===== Tests : Refus si dépassement =====

def test_refus_si_depassement(payment_service, sample_student):
    """
    Test : Refus si le montant dépasse le solde.
    
    Règle vérifiée : Un paiement qui dépasse le solde est refusé.
    
    Pourquoi ce test : Vérifie que la règle du solde est appliquée.
    """
    from edupaie.services.exceptions import ValidationError
    
    with pytest.raises(ValidationError) as exc_info:
        payment_service.enregistrer_paiement(
            eleve_id=sample_student,
            montant=60000,  # Plus que le solde (50000)
            date_paiement="2024-09-15",
            mode="especes"
        )
    
    assert "dépasse le solde restant" in str(exc_info.value.message)


# ===== Tests : Montant <= 0 =====

def test_montant_zero(payment_service, sample_student):
    """
    Test : Refus si le montant est nul.
    
    Règle vérifiée : Un montant nul est refusé.
    
    Pourquoi ce test : Vérifie que la validation du montant fonctionne.
    """
    from edupaie.services.exceptions import ValidationError
    
    with pytest.raises(ValidationError) as exc_info:
        payment_service.enregistrer_paiement(
            eleve_id=sample_student,
            montant=0,
            date_paiement="2024-09-15",
            mode="especes"
        )
    
    assert "strictement positif" in str(exc_info.value.message)


def test_montant_negatif(payment_service, sample_student):
    """
    Test : Refus si le montant est négatif.
    
    Règle vérifiée : Un montant négatif est refusé.
    
    Pourquoi ce test : Vérifie que la validation du montant fonctionne.
    """
    from edupaie.services.exceptions import ValidationError
    
    with pytest.raises(ValidationError) as exc_info:
        payment_service.enregistrer_paiement(
            eleve_id=sample_student,
            montant=-1000,
            date_paiement="2024-09-15",
            mode="especes"
        )
    
    assert "strictement positif" in str(exc_info.value.message)


# ===== Tests : Date invalide =====

def test_date_format_invalide(payment_service, sample_student):
    """
    Test : Refus si le format de la date est invalide.
    
    Règle vérifiée : Une date au mauvais format est refusée.
    
    Pourquoi ce test : Vérifie que la validation du format de date fonctionne.
    """
    from edupaie.services.exceptions import ValidationError
    
    with pytest.raises(ValidationError) as exc_info:
        payment_service.enregistrer_paiement(
            eleve_id=sample_student,
            montant=10000,
            date_paiement="15/09/2024",  # Mauvais format (DD/MM/YYYY au lieu de YYYY-MM-DD)
            mode="especes"
        )
    
    assert "format YYYY-MM-DD" in str(exc_info.value.message)


def test_date_future(payment_service, sample_student):
    """
    Test : Refus si la date est dans le futur.
    
    Règle vérifiée : Une date future est refusée.
    
    Pourquoi ce test : Vérifie que la validation de la date fonctionne.
    """
    from edupaie.services.exceptions import ValidationError
    from datetime import datetime, timedelta
    
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    with pytest.raises(ValidationError) as exc_info:
        payment_service.enregistrer_paiement(
            eleve_id=sample_student,
            montant=10000,
            date_paiement=future_date,
            mode="especes"
        )
    
    assert "futur" in str(exc_info.value.message).lower()


# ===== Tests : Mode non autorisé =====

def test_mode_non_autorise(payment_service, sample_student):
    """
    Test : Refus si le mode n'est pas autorisé.
    
    Règle vérifiée : Un mode non autorisé est refusé.
    
    Pourquoi ce test : Vérifie que la validation du mode fonctionne.
    """
    from edupaie.services.exceptions import ValidationError
    
    with pytest.raises(ValidationError) as exc_info:
        payment_service.enregistrer_paiement(
            eleve_id=sample_student,
            montant=10000,
            date_paiement="2024-09-15",
            mode="carte"  # Mode non autorisé
        )
    
    assert "mode de paiement" in str(exc_info.value.message).lower()


# ===== Tests : Unicité des numéros de reçu =====

def test_unicite_numero_recu(payment_service, sample_student):
    """
    Test : Les numéros de reçu sont uniques.
    
    Règle vérifiée : Chaque paiement a un numéro de reçu unique.
    
    Pourquoi ce test : Vérifie que la génération de numéros fonctionne correctement.
    """
    paiement1 = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-09-15",
        mode="especes"
    )
    
    paiement2 = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-09-16",
        mode="especes"
    )
    
    assert paiement1['numero_recu'] != paiement2['numero_recu']
    assert paiement1['numero_recu'].startswith("REC-2024-")
    assert paiement2['numero_recu'].startswith("REC-2024-")
    # Vérifie que la séquence est incrémentée
    seq1 = int(paiement1['numero_recu'].split('-')[-1])
    seq2 = int(paiement2['numero_recu'].split('-')[-1])
    assert seq2 == seq1 + 1


def test_sequence_recu_par_annee(payment_service, sample_student):
    """
    Test : La séquence des numéros de reçu est par année.
    
    Règle vérifiée : La séquence recommence à 1 pour chaque année.
    
    Pourquoi ce test : Vérifie que la génération de numéros respecte les années.
    """
    paiement1 = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-09-15",
        mode="especes"
    )
    
    paiement2 = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2025-01-10",
        mode="especes"
    )
    
    # Vérifie que les années sont différentes
    assert paiement1['numero_recu'].startswith("REC-2024-")
    assert paiement2['numero_recu'].startswith("REC-2025-")
    
    # Vérifie que chaque année a sa propre séquence (commence à 001 pour 2025)
    assert paiement2['numero_recu'] == "REC-2025-000001"


# ===== Tests : Atomicité (rollback) =====

def test_atomicite_rollback_erreur_validation(payment_service, sample_student):
    """
    Test : Rollback en cas d'erreur de validation.
    
    Règle vérifiée : Si une validation échoue, rien n'est inséré.
    
    Pourquoi ce test : Vérifie l'atomicité de la transaction.
    """
    from edupaie.services.exceptions import ValidationError
    
    # Tentative de paiement invalide
    with pytest.raises(ValidationError):
        payment_service.enregistrer_paiement(
            eleve_id=sample_student,
            montant=0,  # Invalide
            date_paiement="2024-09-15",
            mode="especes"
        )
    
    # Vérification qu'aucun paiement n'a été inséré
    paiements = payment_service.payment_repository.get_paiements_by_eleve(sample_student)
    assert len(paiements) == 0


# ===== Tests : Solde après exact =====

def test_solde_apres_exact(payment_service, sample_student):
    """
    Test : Le solde après paiement est exact.
    
    Règle vérifiée : solde_apres = solde_avant - montant.
    
    Pourquoi ce test : Vérifie que le calcul du solde après est correct.
    """
    solde_avant = payment_service.student_service.solde(sample_student)
    
    paiement = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=20000,
        date_paiement="2024-09-15",
        mode="especes"
    )
    
    assert paiement['solde_apres'] == solde_avant - 20000
    assert paiement['solde_apres'] == 30000


def test_solde_apres_multiple_paiements(payment_service, sample_student):
    """
    Test : Le solde après paiement est exact avec plusieurs paiements.
    
    Règle vérifiée : solde_apres est recalculé pour chaque paiement.
    
    Pourquoi ce test : Vérifie que le calcul du solde après fonctionne
    avec plusieurs paiements successifs.
    """
    # Premier paiement
    paiement1 = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=20000,
        date_paiement="2024-09-15",
        mode="especes"
    )
    assert paiement1['solde_apres'] == 30000
    
    # Deuxième paiement
    paiement2 = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-09-16",
        mode="especes"
    )
    assert paiement2['solde_apres'] == 20000
    
    # Troisième paiement (soldé)
    paiement3 = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=20000,
        date_paiement="2024-09-17",
        mode="especes"
    )
    assert paiement3['solde_apres'] == 0


# ===== Tests : Élève inexistant =====

def test_eleve_inexistant(payment_service):
    """
    Test : Refus si l'élève n'existe pas.
    
    Règle vérifiée : Un paiement pour un élève inexistant est refusé.
    
    Pourquoi ce test : Vérifie que la validation de l'existence de l'élève fonctionne.
    """
    from edupaie.services.exceptions import NotFoundError
    
    with pytest.raises(NotFoundError):
        payment_service.enregistrer_paiement(
            eleve_id=99999,  # ID inexistant
            montant=10000,
            date_paiement="2024-09-15",
            mode="especes"
        )
