# =============================================================================
# exceptions.py - Exceptions métier personnalisées
# =============================================================================
# Rôle : Définit les exceptions métier utilisées dans toute l'application.
# =============================================================================
# Ce fichier utilise :
# - Aucune dépendance externe
# =============================================================================
# Ce fichier est utilisé par :
# - La couche services pour lever des erreurs métier
# - La couche ui pour afficher des messages d'erreur appropriés
# =============================================================================


class ValidationError(Exception):
    """
    Exception levée lorsqu'une validation de données échoue.
    
    Responsabilité : Signaler que les données fournies par l'utilisateur ne sont pas
    valides selon les règles métier (ex: montant négatif, champ vide, format invalide).
    
    Quand utiliser cette exception :
    - Lorsqu'un champ obligatoire est vide
    - Lorsqu'un montant est négatif ou nul
    - Lorsqu'un format de données est invalide (ex: date incorrecte)
    - Lorsqu'une contrainte de validation métier n'est pas respectée
    
    Pourquoi une exception dédiée : Permet à la couche UI de faire la distinction
    entre une erreur de validation (à afficher avec QMessageBox.warning) et une
    erreur technique (à afficher avec QMessageBox.critical).
    
    Attributes:
        message: Message d'erreur destiné à l'utilisateur (en français).
    
    Example:
        if montant <= 0:
            raise ValidationError("Le montant doit être supérieur à 0.")
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialise l'exception avec un message d'erreur.
        
        Args:
            message: Message d'erreur destiné à l'utilisateur (en français).
                     Ce message sera affiché directement dans l'interface.
        """
        self.message = message
        super().__init__(self.message)


class NotFoundError(Exception):
    """
    Exception levée lorsqu'une ressource demandée n'existe pas.
    
    Responsabilité : Signaler qu'une entité (élève, classe, paiement) recherchée
    n'existe pas dans la base de données.
    
    Quand utiliser cette exception :
    - Lorsqu'on recherche un élève par son ID et qu'il n'existe pas
    - Lorsqu'on recherche une classe et qu'elle n'existe pas
    - Lorsqu'on essaie de modifier un paiement qui n'existe pas
    
    Pourquoi une exception dédiée : Permet à la couche UI de distinguer le cas
    "non trouvé" (afficher un message informatif) d'autres types d'erreurs.
    
    Attributes:
        message: Message d'erreur destiné à l'utilisateur (en français).
    
    Example:
        if eleve is None:
            raise NotFoundError("Aucun élève trouvé avec cet identifiant.")
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialise l'exception avec un message d'erreur.
        
        Args:
            message: Message d'erreur destiné à l'utilisateur (en français).
                     Ce message sera affiché directement dans l'interface.
        """
        self.message = message
        super().__init__(self.message)


class BusinessRuleError(Exception):
    """
    Exception levée lorsqu'une règle métier n'est pas respectée.
    
    Responsabilité : Signaler qu'une opération ne peut pas être effectuée car
    elle viole une règle métier de l'application.
    
    Quand utiliser cette exception :
    - Lorsqu'on essaie de supprimer une classe qui contient des élèves
    - Lorsqu'on essaie de supprimer un élève qui a des paiements
    - Lorsqu'on essaie d'effectuer un paiement qui dépasserait le montant dû
    - Lorsqu'on essaie de créer un duplicata (ex: classe avec même nom)
    
    Pourquoi une exception dédiée : Les erreurs de règles métier sont différentes
    des erreurs de validation (ValidationError) car elles concernent l'état
    du système et non les données fournies par l'utilisateur.
    
    Attributes:
        message: Message d'erreur destiné à l'utilisateur (en français).
    
    Example:
        if solde_apres < 0:
            raise BusinessRuleError("Le paiement dépasse le montant dû.")
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialise l'exception avec un message d'erreur.
        
        Args:
            message: Message d'erreur destiné à l'utilisateur (en français).
                     Ce message sera affiché directement dans l'interface.
        """
        self.message = message
        super().__init__(self.message)
