# Plan de soutenance EduPaie

## Plan de démo (10-15 minutes)

### Introduction (2 min)
- Présentation du projet EduPaie
- Objectif : Application de gestion des paiements scolaires
- Technologies : Python, PySide6, SQLite
- Architecture en 3 couches

### Démonstration (8-10 min)

1. **Tableau de bord** (1 min)
   - Affichage des 4 KPI (nombre d'élèves, total encaissé, total restant, non soldés)
   - Liste des élèves avec statuts colorés

2. **Gestion des élèves** (3 min)
   - Ajout d'un nouvel élève
   - Recherche par nom/prénom
   - Filtrage par classe
   - Modification d'un élève
   - Suppression d'un élève

3. **Enregistrement d'un paiement** (3 min)
   - Ouverture de la fiche d'un élève
   - Enregistrement d'un paiement
   - Génération automatique du numéro de reçu
   - Affichage du reçu PDF
   - Mise à jour automatique du solde

4. **Historique des paiements** (2 min)
   - Consultation de l'historique
   - Réimpression d'un reçu
   - Visualisation de l'évolution du solde

5. **Couleurs de statut** (1 min)
   - Vert : Soldé
   - Orange : Partiellement payé
   - Rouge : Non payé

### Conclusion (2 min)
- Résumé des fonctionnalités
- Limites connues
- Perspectives d'amélioration

## Historique Git à présenter

```bash
git log --oneline --graph --all
```

Cette commande affichera :
- Les branches de développement (feature/*, build/*, fix/*)
- Les tags de version (v0.1-fondations, v0.2-eleves, etc.)
- L'historique chronologique des commits

### Étiquettes Git importantes

- `v0.1-fondations` : Architecture et couche données
- `v0.2-eleves` : Gestion des élèves
- `v0.3-solde` : Calcul automatique du solde
- `v0.4-paiement` : Enregistrement des paiements
- `v0.5-historique` : Historique des paiements
- `v0.6-recu` : Génération des reçus PDF
- `v0.7-dashboard` : Tableau de bord
- `v0.8-exe` : Packaging Windows
- `v0.8.1-fix` : Correction des erreurs de syntaxe
- `v0.8.2-fix2` : Correction des erreurs d'exécution
- `v0.8.3-fix3` : Correction du slot montant et noms réalistes

## 10 questions/réponses probables

### 1. Pourquoi avoir choisi Python et PySide6 ?

**Réponse** : Python est un langage accessible avec une bibliothèque standard riche. PySide6 est le binding officiel de Qt pour Python, offrant des widgets riches et stables. Python facilite le développement rapide et PySide6 permet de créer des interfaces professionnelles sans JavaScript.

### 2. Pourquoi SQLite et pas MySQL/PostgreSQL ?

**Réponse** : SQLite est inclus dans la bibliothèque standard Python, ne nécessite aucune installation supplémentaire, et stocke les données dans un fichier unique. C'est parfait pour une application desktop mono-utilisateur. MySQL/PostgreSQL nécessiteraient un serveur de base de données séparé, ce qui est inutile pour ce cas d'usage.

### 3. Pourquoi les montants sont-ils stockés en entiers et pas en flottants ?

**Réponse** : Le franc CFA n'a pas de sous-unités (cents). Les nombres flottants peuvent introduire des erreurs d'arrondi dans les calculs financiers. Les entiers garantissent des calculs exacts et précis pour les montants en FCFA.

### 4. Comment garantissez-vous l'intégrité des données ?

**Réponse** : Deux mécanismes principaux :
1. **Clés étrangères en RESTRICT** : Empêchent la suppression de données référencées (ex: on ne peut pas supprimer une classe si elle a des élèves)
2. **Transactions SQL** : Les opérations d'écriture sont regroupées en transactions pour garantir que tout réussisse ou tout échoue (ex: insertion d'un paiement avec solde_apres)

### 5. Pourquoi avoir séparé le solde_apres dans la table paiement ?

**Réponse** : Cela permet de conserver un historique immuable de l'évolution du solde. Le solde après chaque paiement est figé, ce qui permet de retracer l'historique financier et de détecter les erreurs. Le solde actuel peut être recalculé en prenant le dernier paiement.

### 6. Comment gérez-vous les erreurs dans l'application ?

**Réponse** : Trois niveaux de gestion :
1. **Validations** : Dans la couche services, avec des exceptions personnalisées (ValidationError, NotFoundError, BusinessRuleError)
2. **Décorateur @handle_slot_errors** : Capture toutes les exceptions dans les slots Qt et affiche des QMessageBox à l'utilisateur
3. **Exception hook global** : Capture les exceptions non gérées et les enregistre dans edupaie_errors.log

### 7. Pourquoi l'architecture en 3 couches ?

**Réponse** : Cette architecture sépare clairement les responsabilités :
- **UI** : Affichage et interaction utilisateur
- **Services** : Logique métier et validations
- **Data** : Accès aux données

Cela facilite la maintenance, les tests, et permet de modifier une couche sans impacter les autres.

### 8. Comment fonctionne le packaging avec PyInstaller ?

**Réponse** : PyInstaller analyse les imports Python, empaquette l'interpréteur Python, les dépendances (PySide6, fpdf2), et les ressources (schéma SQL, base modèle) dans un seul fichier .exe. L'application s'exécute sans Python installé sur la machine cible.

### 9. Quelles sont les limites de l'application ?

**Réponse** : 
- **Multi-utilisateur** : Non supporté (mono-utilisateur uniquement)
- **Sauvegarde** : Manuelle (pas de sauvegarde automatique)
- **Export** : Pas d'export Excel/CSV
- **Concurrence** : Pas de gestion de la concurrence

### 10. Quelles améliorations pourraient être apportées ?

**Réponse** :
- Sauvegarde automatique avec Dropbox/Google Drive
- Export Excel/CSV des données
- Gestion multi-utilisateur avec authentification
- Génération de rapports PDF (liste d'élèves, statistiques)
- Synchronisation avec un serveur central
- Application mobile
