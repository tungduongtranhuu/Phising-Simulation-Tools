# 📖 Guide des Nouvelles Fonctionnalités - Simulateur de Phishing

## 🎯 Vue d'ensemble

Ce document explique les nouvelles fonctionnalités ajoutées au simulateur de phishing pour améliorer la capture des données utilisateur et l'automatisation des emails de sensibilisation.

---

## ✨ Fonctionnalités Implémentées

### 1. 🔍 **Recherche dans les Tableaux**

Tous les tableaux disposent maintenant d'un champ de recherche en temps réel :

- **Dashboard** : Recherche dans les campagnes et événements
- **Liste des utilisateurs** : Recherche par email, ID, etc.
- **Détails de campagne** : Recherche dans les cibles et événements

**Utilisation** :
```
Tapez dans le champ "🔍 Rechercher..." et les résultats sont filtrés automatiquement
Le nombre de résultats trouvés s'affiche sous le champ de recherche
```

### 2. ⬆️⬇️ **Tri des Tableaux**

Cliquez sur les en-têtes de colonnes pour trier :

- **Tri numérique** : ID, nombre d'événements
- **Tri alphabétique** : Emails, noms de campagnes
- **Tri par date** : Dates de création, horodatages
- **Indicateurs visuels** : ↑ (ascendant) ou ↓ (descendant)

**Utilisation** :
```
Cliquez sur n'importe quel en-tête de colonne avec l'icône ⇅
Le tri s'applique instantanément
Un indicateur visuel montre la colonne et la direction du tri
```

### 3. 📥 **Export CSV**

Exportez vos données au format CSV pour analyse externe :

- **Bouton "📥 Exporter CSV"** sur chaque tableau
- **Nom de fichier automatique** : inclut le type de données et la date
- **Format compatible Excel** : avec BOM UTF-8
- **Nettoyage automatique** : retire les colonnes d'actions

**Exemples de fichiers générés** :
- `campagnes_2026-03-10.csv`
- `utilisateurs_2026-03-10.csv`
- `evenements_Campagne Test_2026-03-10.csv`

### 4. ✅ **Confirmations Améliorées**

Remplacement des `alert()` et `confirm()` natifs par des notifications modernes :

- **Notifications toast** : Messages élégants qui apparaissent en haut à droite
- **Types de messages** : Succès (vert), Erreur (rouge), Info (bleu)
- **Auto-disparition** : Les notifications disparaissent après 3 secondes
- **Animations fluides** : Transitions élégantes

**Fonctions utilisées** :
```javascript
confirmDelete(message, callback)  // Confirmation avec callback
showNotification(message, type)   // Notification toast
```

### 5. 📧 **Emails Automatiques de Sensibilisation**

**🚨 FONCTIONNALITÉ PRINCIPALE** : Capture automatique des clics et envoi d'emails

#### Comment ça marche ?

1. **Clic sur lien de phishing** → Capture automatique des données
2. **API track-click** → Enregistre l'événement dans la base de données
3. **Email automatique** → Envoie une alerte de sensibilisation à l'utilisateur

#### Données capturées lors d'un clic :

```json
{
  "campaign_id": "...",
  "user_id": "...",
  "event_type": "click",
  "timestamp": "2026-03-10T14:30:00",
  "user_agent": "Mozilla/5.0...",
  "screen_resolution": "1920x1080",
  "language": "fr-FR",
  "ip_address": "192.168.1.100"
}
```

#### Email de sensibilisation envoyé :

- **Sujet** : ⚠️ ALERTE : Vous avez cliqué sur un lien de phishing
- **Format** : HTML + texte brut (compatible tous clients)
- **Contenu** :
  - Alerte qu'il s'agissait d'un test
  - Risques potentiels d'un vrai phishing
  - Conseils de sécurité
  - Ressources pour se former

### 6. 📊 **Logging des Actions Utilisateur**

Toutes les actions importantes sont loggées pour analyse :

- **Exports CSV** : Qui a exporté quelles données et quand
- **Suppressions** : Traçabilité des suppressions
- **Clics sur liens** : Analyse comportementale
- **Stockage** : Table `action_logs` dans la base de données

---

## 🛠️ Routes API Ajoutées

### POST `/api/track-click`

Capture un clic sur lien de phishing et envoie l'email de sensibilisation.

**Payload JSON** :
```json
{
  "campaign_id": "camp123",
  "user_id": "user456",
  "event_type": "click",
  "user_agent": "Mozilla/5.0...",
  "screen_resolution": "1920x1080",
  "language": "fr-FR"
}
```

**Réponse** :
```json
{
  "success": true,
  "event_id": 789,
  "email_sent": true,
  "user_email": "user@example.com",
  "campaign_name": "Test Q1 2026"
}
```

### POST `/api/log-action`

Enregistre une action utilisateur pour analytics.

**Payload JSON** :
```json
{
  "action": "export_csv",
  "page": "/dashboard",
  "table": "campaigns-table",
  "filename": "export.csv"
}
```

---

## 📁 Fichiers Modifiés

### Frontend

| Fichier | Modifications |
|---------|---------------|
| `static/js/main.js` | ✅ Fonctions améliorées : confirmDelete, sortTable, filterTable, exportTableToCSV<br>✅ Nouvelles fonctions : trackClickAndNotify, logUserAction |
| `static/css/style.css` | ✅ Styles pour contrôles de tableaux<br>✅ Styles pour tri et recherche<br>✅ Animations et transitions |
| `templates/dashboard.html` | ✅ Champs de recherche<br>✅ Boutons d'export<br>✅ En-têtes triables |
| `templates/users_list.html` | ✅ Champs de recherche<br>✅ Boutons d'export<br>✅ En-têtes triables |
| `templates/campaign_detail.html` | ✅ Champs de recherche<br>✅ Boutons d'export<br>✅ En-têtes triables<br>✅ Notifications améliorées |

### Backend

| Fichier | Modifications |
|---------|---------------|
| `routes/api_routes.py` | 🆕 Nouveau fichier avec routes API |
| `modules/email/sender.py` | ✅ Fonction send_awareness_email() |
| `app.py` | ✅ Enregistrement du blueprint api_bp |

---

## 🚀 Comment Utiliser

### 1. Tester la capture de clic et l'email automatique

1. Créez une campagne et ajoutez des cibles
2. Copiez le lien de tracking d'un utilisateur
3. Ouvrez le lien dans un navigateur
4. **→ L'événement est enregistré automatiquement**
5. **→ Un email de sensibilisation est envoyé à l'utilisateur**

### 2. Rechercher dans les tableaux

1. Accédez à n'importe quelle page avec un tableau
2. Utilisez le champ "🔍 Rechercher..."
3. Les résultats se filtrent en temps réel

### 3. Trier les données

1. Cliquez sur n'importe quel en-tête de colonne avec ⇅
2. Les données sont triées instantanément
3. L'indicateur ↑ ou ↓ montre le sens du tri

### 4. Exporter en CSV

1. Cliquez sur "📥 Exporter CSV"
2. Le fichier se télécharge automatiquement
3. Ouvrez-le dans Excel ou un autre tableur

---

## ⚙️ Configuration Requise

### Variables d'environnement (config.py)

```python
SMTP_SERVER = "sandbox.smtp.mailtrap.io"  # ou smtp.gmail.com
SMTP_PORT = 2525                           # ou 587 pour Gmail
SMTP_USERNAME = "votre-username"
SMTP_PASSWORD = "votre-password"
SMTP_USE_TLS = True
```

### Pour Gmail :
1. Activez la validation en 2 étapes
2. Créez un "App Password" dans les paramètres Google
3. Utilisez ce mot de passe dans la configuration

### Pour Mailtrap (recommandé pour tests) :
1. Créez un compte sur mailtrap.io
2. Utilisez les identifiants fournis dans l'inbox
3. Tous les emails sont interceptés (aucun envoi réel)

---

## 🔒 Sécurité et Confidentialité

### Données Collectées

- **Events** : timestamp, type, IP, user-agent
- **Actions logs** : type d'action, page, détails
- **Pas de données sensibles** stockées

### Conformité

- ✅ Utilisez uniquement pour formations autorisées
- ✅ Obtenez le consentement des participants
- ✅ Informez les utilisateurs qu'il s'agit d'une simulation
- ✅ Ne stockez pas de données personnelles sensibles

---

## 🐛 Débogage

### Vérifier que les emails sont envoyés

1. Consultez les logs du serveur Flask
2. Recherchez : `✅ Email de sensibilisation envoyé à ...`
3. Si erreur : vérifiez configuration SMTP

### Vérifier les événements de clic

```sql
SELECT * FROM events WHERE event_type = 'click' ORDER BY timestamp DESC;
```

### Vérifier les logs d'action

```sql
SELECT * FROM action_logs ORDER BY timestamp DESC;
```

---

## 📈 Métriques et Analytics

### Données disponibles

- **Taux de clic** : % d'utilisateurs ayant cliqué
- **Temps de réponse** : Délai entre envoi et clic
- **Appareils utilisés** : Analyse des user-agents
- **Géolocalisation** : Analyse des IPs (si implémenté)
- **Exports** : Qui exporte quelles données

### Requêtes SQL utiles

```sql
-- Taux de clic par campagne
SELECT 
    c.campaign_name,
    COUNT(DISTINCT ct.user_id) as total_users,
    COUNT(DISTINCT e.user_id) as clicked_users,
    ROUND(COUNT(DISTINCT e.user_id) * 100.0 / COUNT(DISTINCT ct.user_id), 2) as click_rate
FROM campaigns c
LEFT JOIN campaign_targets ct ON c.campaign_id = ct.campaign_id
LEFT JOIN events e ON c.campaign_id = e.campaign_id AND e.event_type = 'click'
GROUP BY c.campaign_id;
```

---

## 🎓 Bonnes Pratiques

1. **Informez toujours** les participants qu'il s'agit d'une simulation
2. **Obtenez l'autorisation** de la direction avant de lancer une campagne
3. **Analysez les résultats** pour adapter la formation
4. **Exportez régulièrement** les données pour reporting
5. **Nettoyez les vieilles campagnes** pour garder une base de données propre

---

## 📞 Support

Pour toute question ou problème :

1. Consultez les logs du serveur Flask
2. Vérifiez la configuration SMTP
3. Testez d'abord avec Mailtrap avant Gmail
4. Vérifiez les erreurs dans la console du navigateur (F12)

---

## 🔄 Mises à Jour Futures

Fonctionnalités prévues :

- [ ] Dashboard analytics avancé avec graphiques
- [ ] Rapports PDF automatiques
- [ ] Templates d'emails personnalisables
- [ ] Intégration avec Active Directory
- [ ] API REST complète pour intégrations
- [ ] Webhooks pour notifications externes

---

**Version** : 2.0  
**Date** : 10 mars 2026  
**Auteur** : Tung Duong

---

## 🎉 Résumé des Améliorations

✅ **4 fonctions JavaScript** maintenant pleinement utilisées  
✅ **Capture automatique** des clics sur liens de phishing  
✅ **Emails de sensibilisation** envoyés automatiquement  
✅ **Recherche, tri, export** sur tous les tableaux  
✅ **Notifications modernes** au lieu de popups basiques  
✅ **Logging complet** de toutes les actions  
✅ **UI/UX améliorée** avec animations et styles modernes  

**Taux d'utilisation des fonctions main.js : 100%** 🎯
