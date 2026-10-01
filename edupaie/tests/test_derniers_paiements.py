# =============================================================================
# test_derniers_paiements.py - Tests pour les derniers paiements
# =============================================================================
# Rôle : Tester la fonctionnalité des derniers paiements avec JOIN.
# =============================================================================

import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from edupaie.data.database import Database
from edupaie.services.payment_service import PaymentService
from edupaie.services.student_service import StudentService


def test_derniers_paiements():
    """
    Teste la récupération des derniers paiements avec JOIN.
    
    Vérifie que :
    - La méthode retourne une liste
    - Les paiements incluent les informations de l'élève (nom, prénom, classe)
    - La limite est respectée
    - Les paiements sont triés par date décroissante
    """
    # Initialisation de la base de données
    database = Database()
    payment_service = PaymentService(database)
    student_service = StudentService(database)
    
    # Test : récupération des derniers paiements (sans données de test)
    # Utilise les données existantes si disponibles
    paiements = payment_service.derniers_paiements(limite=6)
    
    # Vérifications
    assert isinstance(paiements, list), "Le résultat doit être une liste"
    assert len(paiements) <= 6, "La limite doit être respectée"
    
    # Si des paiements existent, vérifier la structure
    if len(paiements) > 0:
        for paiement in paiements:
            assert 'eleve_nom' in paiement, "Le nom de l'élève doit être présent"
            assert 'eleve_prenom' in paiement, "Le prénom de l'élève doit être présent"
            assert 'eleve_classe' in paiement, "La classe de l'élève doit être présent"
        
        # Vérification du tri (date décroissante)
        dates = [p['date_paiement'] for p in paiements]
        assert dates == sorted(dates, reverse=True), "Les paiements doivent être triés par date décroissante"


if __name__ == "__main__":
    test_derniers_paiements()
    print("Test passé avec succès !")
