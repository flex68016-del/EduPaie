# =============================================================================
# dashboard_service.py - Service pour les statistiques du tableau de bord
# =============================================================================
# Rôle : Fournir les indicateurs statistiques pour le tableau de bord.
# =============================================================================
# Ce fichier utilise :
# - data.student_repository.StudentRepository pour les agrégations élèves
# - data.payment_repository.PaymentRepository pour les agrégations paiements
# - services.student_service.StudentService pour les enrichissements de statut
# =============================================================================
# Ce fichier est utilisé par :
# - ui.dashboard pour afficher les statistiques
# =============================================================================

import sys
from pathlib import Path
from typing import Dict, Any

# Ajout du répertoire parent au PYTHONPATH pour permettre l'import du module edupaie
# Pourquoi : Le fichier est dans edupaie/services/, donc edupaie n'est pas dans le path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from edupaie.data.student_repository import StudentRepository
from edupaie.data.payment_repository import PaymentRepository


class DashboardService:
    """
    Service pour les statistiques du tableau de bord.
    
    Responsabilité : Fournir les indicateurs clés de performance (KPI)
    pour le tableau de bord : nombre d'élèves, total encaissé, total restant dû,
    nombre d'élèves non soldés.
    
    Pourquoi un service séparé : Sépare la logique de calcul des statistiques
    de l'interface, facilitant les tests et les modifications futures.
    
    Cohérence des données : Le service vérifie que total_encaissé + total_restant_du
    est égal au total_du global, ce qui garantit l'intégrité des données.
    """
    
    def __init__(self, student_repository: StudentRepository,
                 payment_repository: PaymentRepository) -> None:
        """
        Initialise le service avec les repositories nécessaires.
        
        Args:
            student_repository: Repository pour accéder aux données des élèves.
            payment_repository: Repository pour accéder aux données des paiements.
        """
        self.student_repository = student_repository
        self.payment_repository = payment_repository
    
    def dashboard_stats(self) -> Dict[str, Any]:
        """
        Calcule les statistiques pour le tableau de bord.
        
        Returns:
            Dictionnaire contenant les 4 indicateurs :
            - nombre_eleves : nombre total d'élèves
            - total_encaisse : somme totale des paiements (en FCFA)
            - total_restant_du : somme totale des soldes restants (en FCFA)
            - eleves_non_soldes : nombre d'élèves dont le solde > 0
        
        Raises:
            AssertionError : Si la cohérence des données n'est pas vérifiée
            (total_encaissé + total_restant_du != total_du).
        
        Pourquoi ces 4 indicateurs : Ce sont les KPI essentiels pour une vue
        d'ensemble de la situation financière de l'établissement.
        
        Pourquoi vérification de cohérence : Garantit que les données sont
        cohérentes et qu'il n'y a pas d'anomalie dans les calculs.
        """
        # Nombre total d'élèves
        nombre_eleves = self.student_repository.count_all_students()
        
        # Total encaissé (somme de tous les paiements)
        total_encaisse = self.payment_repository.sum_all_payments()
        
        # Total dû (somme de tous les total_du des élèves)
        total_du = self.student_repository.sum_total_du()
        
        # Calcul du total restant dû (total_du - total_encaisse)
        # Pourquoi cette formule : Le solde restant est la différence entre
        # ce qui est dû et ce qui a été payé
        total_restant_du = total_du - total_encaisse
        
        # Vérification de cohérence : total_encaissé + total_restant_du doit être égal à total_du
        # Pourquoi cette vérification : Détecte les anomalies de calcul
        assert total_encaisse + total_restant_du == total_du, \
            f"Incohérence des données : {total_encaisse:,} + {total_restant_du:,} != {total_du:,}"
        
        # Nombre d'élèves non soldés (solde > 0)
        # Pourquoi calculer ce nombre : Permet de savoir combien d'élèves
        # doivent encore payer
        eleves_non_soldes = self._count_students_with_balance()
        
        return {
            "nombre_eleves": nombre_eleves,
            "total_encaisse": total_encaisse,
            "total_restant_du": total_restant_du,
            "eleves_non_soldes": eleves_non_soldes
        }
    
    def _count_students_with_balance(self) -> int:
        """
        Compte le nombre d'élèves dont le solde est strictement positif.
        
        Returns:
            Le nombre d'élèves non soldés (solde > 0).
        
        Pourquoi solde > 0 : Un élève est considéré non soldé s'il doit encore
        de l'argent (solde positif). Un solde de 0 signifie que l'élève est soldé.
        
        Pourquoi requête SQL directe : Plus performant que d'itérer sur tous
        les élèves et de calculer le solde pour chacun. Une seule requête SQL
        avec une sous-requête est beaucoup plus rapide.
        """
        with self.student_repository.database.transaction() as cursor:
            # Requête SQL : compte les élèves dont le solde est > 0
            # Pourquoi la sous-requête : Le solde est calculé dynamiquement
            # (total_du - SUM(paiements.montant)), donc on doit le calculer
            # pour chaque élève avant de filtrer
            cursor.execute(
                """SELECT COUNT(*) as nombre
                   FROM eleve e
                   WHERE (e.total_du - COALESCE(
                       (SELECT SUM(p.montant) FROM paiement p WHERE p.eleve_id = e.id), 0
                   )) > 0"""
            )
            result = cursor.fetchone()
            return result['nombre'] if result else 0
