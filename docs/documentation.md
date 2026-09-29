# Documentation technique EduPaie

## Architecture en 3 couches

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                     UI (Couche Présentation)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │students_view│  │payment_dialog│  │  dashboard   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Services (Couche Métier)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │student_service│ │payment_service│ │receipt_service│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data (Couche Accès Données)               │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │student_repo  │  │payment_repo  │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     SQLite (Base de données)                │
└─────────────────────────────────────────────────────────────┘
```

### Règles d'architecture

1. **Couche UI (edupaie/ui/)**
   - Widgets PySide6 (QWidget, QTableWidget, QDialog, etc.)
   - Gestion des événements utilisateur
   - Appel des services pour la logique métier
   - Aucun SQL direct
   - Aucun import de repository
   - Affichage des erreurs via QMessageBox

2. **Couche Services (edupaie/services/)**
   - Logique métier et validations
   - Calculs (solde, statut, numéro de reçu)
   - Orchestration des repositories
   - Gestion des transactions
   - Exceptions métier personnalisées (ValidationError, NotFoundError, BusinessRuleError)

3. **Couche Data (edupaie/data/)**
   - Accès aux données via sqlite3
   - Requêtes SQL (SELECT, INSERT, UPDATE, DELETE)
   - Gestion de la connexion
   - Aucune logique métier
   - Aucune validation

## Choix techniques justifiés

### Pourquoi Python 3.10+ ?

- **Typing** : Support des annotations de type (`List[Dict]`, `Optional`, etc.)
- **Performance** : Améliorations de performance par rapport aux versions précédentes
- **Compatibilité** : PySide6 nécessite Python 3.6+
- **Disponibilité** : Python 3.10 est largement supporté

### Pourquoi PySide6 ?

- **Qt officiel** : Binding officiel de Qt pour Python
- **Licence LGPL** : Compatible avec les projets commerciaux
- **Documentation** : Documentation complète et maintenue
- **Stabilité** : Plus stable que PyQt5 et PySide2
- **Widgets riches** : TableWidget, Dialog, Signal/Slot puissants

### Pourquoi SQLite (sqlite3) ?

- **Standard library** : Aucune dépendance externe
- **Base locale** : Parfait pour une application desktop standalone
- **Transactionnalité** : Support des transactions ACID
- **Portabilité** : Base de données portable (fichier unique)
- **Suffisant** : Convient pour une application mono-utilisateur

### Pourquoi SQL écrit à la main (pas d'ORM) ?

- **Contrôle total** : Optimisation fine des requêtes
- **Simplicité** : Pas de surcouche d'abstraction inutile
- **Performance** : Évite l'overhead de l'ORM
- **Apprentissage** : Meilleure compréhension du SQL
- **Transparence** : Requêtes visibles et auditable

### Pourquoi les montants en entiers (FCFA) ?

- **Précision** : Évite les erreurs d'arrondi des nombres flottants
- **FCFA non décimal** : Le franc CFA n'a pas de sous-unités (cents)
- **Calculs exacts** : Les calculs de solde sont exacts avec des entiers
- **Comparaison** : Les comparaisons monétaires sont exactes

### Pourquoi dates ISO YYYY-MM-DD ?

- **Standard** : Format international ISO 8601
- **Tri** : Tri chronologique naturel
- **SQL** : Format natif de SQLite (DATE functions)
- **Portabilité** : Compatible avec tous les systèmes

### Pourquoi `solde_apres` figé dans PAIEMENT ?

- **Historique immuable** : Chaque paiement enregistre l'état du solde APRÈS ce paiement
- **Reconstitution** : Le solde actuel peut être recalculé en prenant le dernier paiement
- **Audit financier** : Permet de retracer l'évolution du solde au fil du temps
- **Correction** : Si un paiement doit être corrigé, on insère un nouveau paiement

### Pourquoi les clés étrangères en RESTRICT ?

- **Intégrité** : Empêche la suppression accidentelle de données référencées
- **Historique** : L'historique des paiements ne peut pas être modifié
- **Cohérence** : Garantit la cohérence des données
- **Sécurité** : Protège contre les suppressions en cascade

### Pourquoi les exceptions métier personnalisées ?

- **Clarté** : Différenciation entre erreurs utilisateur et erreurs techniques
- **Traitement UI** : Messages adaptés selon le type d'erreur
- **Logging** : Différenciation des niveaux de log
- **Maintenabilité** : Code plus lisible et testable

### Pourquoi le décorateur `@handle_slot_errors` ?

- **Protection** : Capture toutes les exceptions dans les slots Qt
- **Feedback utilisateur** : Affiche des QMessageBox pour les erreurs
- **Logging** : Enregistre les erreurs techniques dans edupaie_errors.log
- **Stabilité** : Empêche les crashes silencieux de l'application

### Pourquoi le numéro de reçu séquentiel par année ?

- **Organisation** : Facilite l'organisation par année
- **Unicité** : Garantit l'unicité des numéros
- **Réinitialisation** : Permet de réinitialiser chaque année
- **Format standard** : REC-2024-000001, REC-2025-000001

### Pourquoi la base de données dans %APPDATA% ?

- **Standard Windows** : %APPDATA% est le dossier standard pour les données utilisateur
- **Multi-utilisateur** : Chaque utilisateur a son propre dossier
- **Sauvegarde** : Facilite la sauvegarde (dossier unique)
- **Permission** : Écriture garantie sans droits admin

### Pourquoi PyInstaller --onefile ?

- **Distribution simple** : Un seul fichier .exe facile à distribuer
- **Installation** : Pas d'installation requise pour l'utilisateur
- **Portable** : Peut être exécuté depuis n'importe quel dossier
- **Professional** : Apparence professionnelle

## Limites connues

### Limites fonctionnelles

1. **Multi-utilisateur non supporté**
   - Application conçue pour un seul utilisateur
   - Pas de gestion des droits d'accès
   - Pas de connexion réseau

2. **Sauvegarde manuelle**
   - Pas de sauvegarde automatique
   - L'utilisateur doit copier manuellement le dossier %APPDATA%/EduPaie

3. **Pas d'exportation**
   - Pas d'export Excel/CSV
   - Pas d'impression de liste d'élèves

4. **Statuts figés**
   - Seuls 3 statuts : Soldé, Partiellement payé, Non payé
   - Pas de personnalisation des statuts

### Limites techniques

1. **Taille de la base**
   - SQLite convient pour des bases de petite à moyenne taille
   - Pas optimisé pour des millions d'enregistrements

2. **Performance**
   - Pas d'index avancés
   - Pas de cache applicatif
   - Requêtes simples uniquement

3. **Concurrence**
   - Pas de gestion de la concurrence
   - Un seul accès à la base à la fois

## Emplacements des captures d'écran

Les captures d'écran doivent être placées dans `docs/screenshots/` :

1. **accueil.png** : Tableau de bord avec les 4 KPI
2. **liste_eleves.png** : Liste des élèves avec filtres
3. **ajout_eleve.png** : Formulaire d'ajout d'élève
4. **enregistrement_paiement.png** : Dialogue de paiement
5. **recu_pdf.png** : Reçu PDF généré
6. **historique_paiements.png** : Historique des paiements d'un élève

## Structure du projet

```
EduPaie/
├── edupaie/
│   ├── ui/              # Couche présentation (PySide6)
│   │   ├── main_window.py
│   │   ├── students_view.py
│   │   ├── student_form.py
│   │   ├── student_detail.py
│   │   ├── payment_dialog.py
│   │   ├── dashboard.py
│   │   └── error_handler.py
│   ├── services/        # Couche métier
│   │   ├── student_service.py
│   │   ├── payment_service.py
│   │   ├── receipt_service.py
│   │   ├── dashboard_service.py
│   │   └── exceptions.py
│   ├── data/            # Couche accès données
│   │   ├── database.py
│   │   ├── student_repository.py
│   │   └── payment_repository.py
│   ├── utils/           # Utilitaires
│   │   └── paths.py
│   ├── db/              # Schéma et seed
│   │   ├── schema.sql
│   │   ├── seed.py
│   │   └── create_model_db.py
│   ├── tests/           # Tests pytest
│   │   ├── test_students.py
│   │   ├── test_payments.py
│   │   ├── test_solde.py
│   │   ├── test_historique.py
│   │   ├── test_recu.py
│   │   └── test_dashboard.py
│   ├── main.py          # Point d'entrée
│   └── edupaie.db       # Base modèle (embarquée)
├── docs/                # Documentation
│   ├── modelisation.md
│   ├── documentation.md
│   ├── manuel_utilisateur.md
│   ├── guide_installation.md
│   ├── soutenance.md
│   └── screenshots/
├── dist/                # Exécutable PyInstaller
│   └── Edupaie.exe
├── edupaie.spec         # Configuration PyInstaller
├── build.bat            # Script de build Windows
├── requirements.txt     # Dépendances Python
└── README.md            # Documentation du projet
```
