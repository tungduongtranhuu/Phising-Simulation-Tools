# Guide d'Utilisation - Suppression de Campagnes et Utilisateurs

## 📋 Vue d'ensemble

Cette mise à jour ajoute des fonctionnalités complètes de suppression sécurisée pour les campagnes et les utilisateurs dans l'application de simulation de phishing.

## ✨ Nouvelles Fonctionnalités

### 1. Suppression de Campagnes

#### Via l'Interface Web

**Depuis le Tableau de Bord:**
- Chaque campagne dans la liste affiche maintenant un bouton 🗑️
- Cliquez sur le bouton pour supprimer une campagne
- Une confirmation en deux étapes est requise pour éviter les suppressions accidentelles

**Depuis la Page de Détails de Campagne:**
- Un bouton "🗑️ Supprimer cette campagne" apparaît en bas de la section "Informations générales"
- Cliquez sur le bouton
- Confirmez en tapant "SUPPRIMER" dans la boîte de dialogue

#### Via Script Python

Vous pouvez également utiliser le script autonome:

```bash
python delete/delete_campaign.py
```

**Options disponibles:**
1. Supprimer 1 campagne par ID
2. Supprimer plusieurs campagnes par IDs (ex: 36,37)
0. Quitter

### 2. Suppression d'Utilisateurs

#### Via l'Interface Web

**Depuis la Page des Utilisateurs:**
- Nouveau lien "👥 Utilisateurs" dans la barre de navigation
- Accédez à `/users` pour voir tous les utilisateurs
- Chaque utilisateur a un bouton "🗑️ Supprimer"
- Confirmation requise avant suppression

**Depuis la Page de Détails de Campagne:**
- Dans la table des cibles, chaque utilisateur a un bouton "🗑️ Supprimer" dans la colonne Actions
- Permet de supprimer un utilisateur directement depuis la campagne

#### Via Script Python

```bash
python delete/delete_user.py
```

**Options disponibles:**
1. Supprimer 1 utilisateur par ID
2. Supprimer 1 utilisateur par Email
3. Supprimer plusieurs utilisateurs par IDs (ex: 1,2,3)
0. Quitter

## 🔒 Sécurité des Suppressions

### Gestion des Contraintes de Clés Étrangères

Les suppressions respectent l'ordre suivant pour éviter les erreurs de contraintes:

**Pour une Campagne:**
1. ✅ Supprime tous les événements liés (`events`)
2. ✅ Supprime toutes les associations cible-campagne (`campaign_targets`)
3. ✅ Supprime la campagne elle-même (`campaigns`)
4. ℹ️ Les utilisateurs sont conservés (seuls les liens sont supprimés)

**Pour un Utilisateur:**
1. ✅ Supprime tous les événements liés (`events`)
2. ✅ Supprime toutes les associations utilisateur-campagne (`campaign_targets`)
3. ✅ Supprime l'utilisateur lui-même (`users`)
4. ℹ️ Les campagnes sont conservées

### Confirmations Multi-Niveaux

- **Première confirmation:** Affiche un résumé de ce qui sera supprimé
- **Deuxième confirmation:** Pour les campagnes, demande de taper "SUPPRIMER" explicitement
- **Feedback détaillé:** Affiche le nombre d'éléments supprimés après l'opération

## 🎨 Interface Utilisateur

### Nouveaux Boutons

- **`.btn-delete-campaign`** - Bouton rouge avec dégradé pour supprimer une campagne
- **`.btn-delete-user`** - Bouton rouge pour supprimer un utilisateur
- **`.btn-delete-small`** - Version compacte pour les tableaux

### Nouvelle Page

- **`/users`** - Liste de tous les utilisateurs avec statistiques:
  - Email de l'utilisateur
  - Nombre de campagnes associées
  - Nombre d'événements enregistrés
  - Bouton de suppression

## 🛠️ Structure Technique

### Nouveaux Fichiers

```
delete/
├── delete_campaign.py    # Script autonome + fonctions réutilisables
└── delete_user.py        # Script autonome + fonctions réutilisables

routes/
└── user_routes.py        # Nouvelles routes pour la gestion des utilisateurs

templates/
└── users_list.html       # Page listant tous les utilisateurs
```

### Nouvelles Routes API

```python
POST /campaign/<id>/delete  # Supprimer une campagne
POST /user/<id>/delete      # Supprimer un utilisateur
GET  /users                 # Lister tous les utilisateurs
```

### Format de Réponse JSON

```json
{
    "success": true,
    "message": "Campagne 'Test' supprimée avec succès",
    "deleted": {
        "events": 15,
        "targets": 5
    }
}
```

## 📝 Exemples d'Utilisation

### Exemple 1: Supprimer une campagne depuis le tableau de bord

1. Allez sur `/dashboard`
2. Trouvez la campagne à supprimer
3. Cliquez sur le bouton 🗑️
4. Lisez le résumé de ce qui sera supprimé
5. Cliquez OK
6. Tapez "SUPPRIMER" dans la boîte de dialogue
7. Validez

### Exemple 2: Supprimer plusieurs campagnes via script

```bash
python delete/delete_campaign.py
```

```
📋 LISTE DES CAMPAGNES (2 campagnes):
===================================================================================
ID    Nom                            Statut       Utilisateurs  Événements
===================================================================================
36    hqhq                           active       3             12
37    daylaphishing                  active       2             8
===================================================================================

📝 OPTIONS:
  1 - Supprimer 1 campagne par ID
  2 - Supprimer plusieurs campagnes par IDs
  0 - Quitter

Choisir (0-2): 2

Entrer les IDs des campagnes séparés par des virgules (ex: 36,37): 36,37

⚠️  Suppression de 2 campagnes: [36, 37]
Tapez 'OUI' pour confirmer la suppression de TOUTES: OUI

🗑️  Suppression de 2 campagnes...

--- Suppression de la campagne ID: 36 ---
...
```

### Exemple 3: Voir tous les utilisateurs

1. Cliquez sur "👥 Utilisateurs" dans la navigation
2. Vous verrez une table avec tous les utilisateurs
3. Chaque ligne affiche:
   - ID utilisateur
   - Email
   - Nombre de campagnes associées
   - Nombre d'événements
   - Bouton de suppression

## ⚠️ Avertissements Importants

### Suppressions Irréversibles

- **Aucune corbeille:** Les suppressions sont définitives
- **Pas de restauration:** Les données supprimées ne peuvent pas être récupérées
- **Vérifiez avant:** Assurez-vous de vouloir vraiment supprimer

### Base de Données

- Les suppressions respectent les contraintes de clés étrangères
- Aucun risque de corruption de la base de données
- Les suppressions sont effectuées dans une transaction (rollback en cas d'erreur)

### Performance

- Supprimer une campagne avec beaucoup de données peut prendre quelques secondes
- Le script affiche lesProgressBar pour les opérations longues
- L'interface web affiche un résumé après la suppression

## 🐛 Dépannage

### Erreur: "Campagne introuvable"
- Vérifiez que l'ID de la campagne existe
- Rechargez la page pour voir les campagnes actuelles

### Erreur: "Utilisateur introuvable"
- Vérifiez que l'ID de l'utilisateur est correct
- L'utilisateur a peut-être déjà été supprimé

### La page ne se recharge pas après suppression
- Utilisez F5 pour recharger manuellement
- Vérifiez la console JavaScript pour les erreurs

### Erreur Foreign Key constraint
- **Ce problème est résolu** par les nouveaux scripts
- Si vous voyez encore cette erreur, utilisez les scripts `delete_campaign.py` ou `delete_user.py`

## 📚 Fichiers de Configuration

### Imports Ajustés

Les fichiers dans `delete/` ajoutent automatiquement le dossier parent au path Python:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

Cela permet d'importer `database.db` depuis n'importe où.

### Styles CSS

Tous les styles pour les boutons de suppression sont dans `static/css/style.css`:
- Boutons rouges avec dégradé
- Effets de survol
- Versions compactes pour les tableaux

## 🎓 Bonnes Pratiques

1. **Vérifiez toujours** les données avant de supprimer
2. **Utilisez les scripts** pour les suppressions en masse
3. **Lisez les messages** de confirmation attentivement
4. **Sauvegardez** votre base de données avant des suppressions importantes
5. **Testez d'abord** sur des données de test

## 📞 Support

Pour toute question sur les fonctionnalités de suppression:
1. Consultez les fichiers `FOREIGN_KEY_CONSTRAINTS.md` et `FIX_PERMISSION_ERROR.md`
2. Vérifiez les logs dans la console
3. Utilisez les scripts autonomes pour plus de contrôle

---

**Version:** 1.0.0  
**Dernière mise à jour:** 1 mars 2026  
**Langue:** Français 🇫🇷
