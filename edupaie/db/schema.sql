-- =============================================================================
-- schema.sql - Schéma de la base de données SQLite
-- =============================================================================
-- Rôle : Définit la structure de la base de données EduPaie.
-- =============================================================================
-- Ce fichier utilise :
-- - Syntaxe SQLite standard
-- =============================================================================
-- Ce fichier est utilisé par :
-- - data/database.py pour initialiser la base de données
-- =============================================================================

-- Activation des clés étrangères pour garantir l'intégrité référentielle
-- Pourquoi : Sans cette directive, SQLite ignore les contraintes de clé étrangère
PRAGMA foreign_keys = ON;

-- =============================================================================
-- Table : classe
-- =============================================================================
-- Rôle : Stocke les classes de l'établissement scolaire.
-- Pourquoi cette table : Permet d'organiser les élèves par classe (6ème, 5ème, etc.)
-- =============================================================================
CREATE TABLE classe (
    -- Clé primaire auto-incrémentée
    -- Pourquoi : Identifiant unique pour chaque classe
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Nom de la classe (ex: "6ème A", "5ème B")
    -- Pourquoi UNIQUE : Empêche la création de classes avec le même nom
    -- Pourquoi NOT NULL : Une classe doit obligatoirement avoir un nom
    nom TEXT UNIQUE NOT NULL
);

-- =============================================================================
-- Table : eleve
-- =============================================================================
-- Rôle : Stocke les informations des élèves et leur dette totale.
-- Pourquoi cette table : Base de données des élèves pour le suivi des paiements
-- =============================================================================
CREATE TABLE eleve (
    -- Clé primaire auto-incrémentée
    -- Pourquoi : Identifiant unique pour chaque élève
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Nom de famille de l'élève
    -- Pourquoi NOT NULL : Un élève doit obligatoirement avoir un nom
    nom TEXT NOT NULL,
    
    -- Prénom de l'élève
    -- Pourquoi NOT NULL : Un élève doit obligatoirement avoir un prénom
    prenom TEXT NOT NULL,
    
    -- Clé étrangère vers la table classe
    -- Pourquoi ON DELETE RESTRICT : Empêche de supprimer une classe si des élèves y sont inscrits
    -- Pourquoi : Protège l'intégrité des données (on ne peut pas orpheliner des élèves)
    classe_id INTEGER NOT NULL,
    
    -- Année scolaire (ex: "2024-2025")
    -- Pourquoi TEXT : Format plus flexible pour gérer "2024-2025" ou "2024/2025"
    annee_scolaire TEXT NOT NULL,
    
    -- Total dû par l'élève (en FCFA, stocké comme entier)
    -- Pourquoi INTEGER : Évite les erreurs d'arrondi des nombres flottants (FCFA = centimes)
    -- Pourquoi CHECK >= 0 : Une dette ne peut pas être négative
    -- Pourquoi NOT NULL : Chaque élève a un montant dû (même 0)
    total_du INTEGER NOT NULL CHECK (total_du >= 0),
    
    -- Contrainte de clé étrangère
    FOREIGN KEY (classe_id) REFERENCES classe(id) ON DELETE RESTRICT
);

-- Index sur le nom des élèves pour accélérer les recherches par nom
-- Pourquoi : Les recherches par nom sont fréquentes dans l'interface
CREATE INDEX idx_eleve_nom ON eleve(nom);

-- =============================================================================
-- Table : paiement
-- =============================================================================
-- Rôle : Stocke l'historique des paiements effectués par les élèves.
-- Pourquoi cette table : Permet de tracer tous les paiements et de calculer les soldes
-- =============================================================================
CREATE TABLE paiement (
    -- Clé primaire auto-incrémentée
    -- Pourquoi : Identifiant unique pour chaque paiement
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Clé étrangère vers la table eleve
    -- Pourquoi ON DELETE RESTRICT : Empêche de supprimer un élève si des paiements existent
    -- Pourquoi : Protège l'historique comptable (on ne peut pas effacer des paiements)
    eleve_id INTEGER NOT NULL,
    
    -- Montant du paiement (en FCFA, stocké comme entier)
    -- Pourquoi INTEGER : Évite les erreurs d'arrondi des nombres flottants
    -- Pourquoi CHECK > 0 : Un paiement doit avoir un montant positif
    -- Pourquoi NOT NULL : Un paiement doit obligatoirement avoir un montant
    montant INTEGER NOT NULL CHECK (montant > 0),
    
    -- Date du paiement au format ISO YYYY-MM-DD
    -- Pourquoi TEXT : SQLite n'a pas de type DATE natif, format ISO permet le tri
    -- Pourquoi NOT NULL : Un paiement doit avoir une date
    date_paiement TEXT NOT NULL,
    
    -- Mode de paiement (espèces, chèque, virement, mobile money)
    -- Pourquoi CHECK : Limite aux modes de paiement acceptés par l'école
    -- Pourquoi NOT NULL : Un paiement doit avoir un mode
    mode TEXT NOT NULL CHECK (mode IN ('especes', 'cheque', 'virement', 'mobile_money')),
    
    -- Numéro de reçu unique (ex: "REC-2024-000001")
    -- Pourquoi UNIQUE : Empêche d'avoir deux paiements avec le même numéro de reçu
    -- Pourquoi NOT NULL : Chaque paiement doit avoir un numéro de reçu
    numero_recu TEXT UNIQUE NOT NULL,
    
    -- Solde après ce paiement (en FCFA, stocké comme entier)
    -- Pourquoi INTEGER : Cohérence avec total_du et montant
    -- Pourquoi NOT NULL : Permet de connaître l'état du solde à ce moment précis
    -- Pourquoi figé : Ne change jamais, permet de retracer l'historique des soldes
    solde_apres INTEGER NOT NULL,
    
    -- Contrainte de clé étrangère
    FOREIGN KEY (eleve_id) REFERENCES eleve(id) ON DELETE RESTRICT
);

-- Index sur eleve_id pour accélérer les recherches de paiements par élève
-- Pourquoi : Les requêtes "tous les paiements d'un élève" sont très fréquentes
CREATE INDEX idx_paiement_eleve_id ON paiement(eleve_id);
