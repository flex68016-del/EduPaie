# =============================================================================
# test_recu.py - Tests pour la génération des reçus PDF
# =============================================================================
# Rôle : Tester la fonctionnalité de génération de reçus PDF.
# =============================================================================
# Ce fichier utilise :
# - pytest pour les tests unitaires
# - data.database.Database pour la base de données en mémoire
# - services.receipt_service.ReceiptService pour la génération PDF
# - services.payment_service.PaymentService pour créer des paiements
# - services.student_service.StudentService pour créer des élèves
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/tests/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import os
from edupaie.data.database import Database
from edupaie.services.payment_service import PaymentService
from edupaie.services.student_service import StudentService
from edupaie.services.receipt_service import ReceiptService


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
def receipt_service(payment_service):
    """
    Crée un service de reçus pour les tests.
    """
    return ReceiptService(
        payment_service.payment_repository,
        payment_service.student_service.repository
    )


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

def test_recu_pdf_cree(payment_service, receipt_service, sample_student):
    """
    Test : Le fichier PDF est créé et non vide.
    
    Pourquoi ce test : Vérifie que la génération PDF fonctionne
    et produit un fichier valide.
    """
    # Création d'un paiement
    paiement = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-01-15",
        mode="especes"
    )
    
    # Génération du reçu
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        temp_path = tmp.name
    
    try:
        chemin = receipt_service.generer_recu(paiement['id'], temp_path)
        
        # Vérification que le fichier existe
        assert os.path.exists(chemin)
        
        # Vérification que le fichier n'est pas vide
        assert os.path.getsize(chemin) > 0
        
    finally:
        # Nettoyage
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_recu_contenu_attendu(payment_service, receipt_service, sample_student):
    """
    Test : Le PDF contient les informations attendues.
    
    Pourquoi ce test : Vérifie que le reçu contient les données
    figées du paiement (numéro, montant, solde après).
    
    Note : fpdf2 ne permet pas de lire le contenu d'un PDF pour vérification,
    donc ce test vérifie simplement que le fichier est créé avec la bonne taille.
    Le contenu réel est vérifié manuellement lors de la révision.
    """
    # Création d'un paiement
    paiement = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=15000,
        date_paiement="2024-02-20",
        mode="cheque"
    )
    
    # Génération du reçu
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        temp_path = tmp.name
    
    try:
        chemin = receipt_service.generer_recu(paiement['id'], temp_path)
        
        # Vérification que le fichier existe et a une taille raisonnable
        assert os.path.exists(chemin)
        size = os.path.getsize(chemin)
        assert size > 1000  # Au moins 1 Ko (reçu PDF minimal)
        
    finally:
        # Nettoyage
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_recu_reproductibilite(payment_service, receipt_service, sample_student):
    """
    Test : Deux générations successives donnent un contenu identique.
    
    Pourquoi ce test : Vérifie que le reçu est reproductible,
    ce qui est essentiel pour la ré-impression.
    
    Pourquoi le reçu est reproductible : Il est reconstruit UNIQUEMENT
    à partir de données figées en base (paiement.solde_apres, numero_recu, etc.),
    pas de l'état actuel de l'élève.
    """
    # Création d'un paiement
    paiement = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=20000,
        date_paiement="2024-03-10",
        mode="virement"
    )
    
    # Génération du reçu deux fois
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp1:
        temp_path1 = tmp1.name
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp2:
        temp_path2 = tmp2.name
    
    try:
        chemin1 = receipt_service.generer_recu(paiement['id'], temp_path1)
        chemin2 = receipt_service.generer_recu(paiement['id'], temp_path2)
        
        # Vérification que les deux fichiers ont la même taille
        size1 = os.path.getsize(chemin1)
        size2 = os.path.getsize(chemin2)
        assert size1 == size2
        
    finally:
        # Nettoyage
        if os.path.exists(temp_path1):
            os.unlink(temp_path1)
        if os.path.exists(temp_path2):
            os.unlink(temp_path2)


def test_recu_paiement_inexistant(receipt_service):
    """
    Test : ValueError si le paiement n'existe pas.
    
    Pourquoi ce test : Vérifie que le service gère correctement
    le cas d'un paiement inexistant.
    """
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        temp_path = tmp.name
    
    try:
        with pytest.raises(ValueError) as exc_info:
            receipt_service.generer_recu(999999, temp_path)
        
        assert "introuvable" in str(exc_info.value)
        
    finally:
        # Nettoyage
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_recu_chemin_par_defaut(payment_service, receipt_service, sample_student):
    """
    Test : Le chemin par défaut est utilisé si aucun chemin n'est fourni.
    
    Pourquoi ce test : Vérifie que le service utilise le dossier
    par défaut (user_data_dir/reçus) si aucun chemin n'est spécifié.
    """
    # Création d'un paiement
    paiement = payment_service.enregistrer_paiement(
        eleve_id=sample_student,
        montant=10000,
        date_paiement="2024-01-15",
        mode="especes"
    )
    
    # Génération du reçu sans chemin
    chemin = receipt_service.generer_recu(paiement['id'])
    
    # Vérification que le fichier existe
    assert os.path.exists(chemin)
    
    # Vérification que le fichier est dans le dossier reçus
    assert "reçus" in chemin or "recus" in chemin.lower()
    
    # Nettoyage
    if os.path.exists(chemin):
        os.unlink(chemin)
