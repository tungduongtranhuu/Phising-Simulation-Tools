"""
Test des nouvelles fonctionnalités
Démo de la capture de clics et de l'envoi d'emails automatiques
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"
API_URL = f"{BASE_URL}/api"

def test_track_click():
    """
    Teste l'API de tracking de clic
    Simule un clic sur un lien de phishing
    """
    print("\n" + "="*60)
    print("🧪 TEST : Tracking de clic avec envoi d'email automatique")
    print("="*60)
    
    # Données du clic
    click_data = {
        "campaign_id": "1",  # Remplacez par un ID de campagne réel
        "user_id": "1",       # Remplacez par un ID utilisateur réel
        "event_type": "click",
        "timestamp": "2026-03-10T14:30:00",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "screen_resolution": "1920x1080",
        "language": "fr-FR"
    }
    
    try:
        print(f"\n📤 Envoi de la requête à {API_URL}/track-click")
        print(f"📦 Données : {json.dumps(click_data, indent=2)}")
        
        response = requests.post(
            f"{API_URL}/track-click",
            json=click_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCÈS !")
            print(f"   - Event ID: {result.get('event_id')}")
            print(f"   - Email envoyé: {result.get('email_sent')}")
            print(f"   - Utilisateur: {result.get('user_email')}")
            print(f"   - Campagne: {result.get('campaign_name')}")
            
            if result.get('email_error'):
                print(f"\n⚠️  Erreur email: {result.get('email_error')}")
        else:
            print(f"\n❌ ERREUR: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter au serveur")
        print("   → Assurez-vous que app.py est en cours d'exécution")
        print("   → Commande: python app.py")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")


def test_log_action():
    """
    Teste l'API de logging d'action
    """
    print("\n" + "="*60)
    print("🧪 TEST : Logging d'action utilisateur")
    print("="*60)
    
    # Données de l'action
    action_data = {
        "action": "export_csv",
        "timestamp": "2026-03-10T14:35:00",
        "page": "/dashboard",
        "table": "campaigns-table",
        "filename": "campagnes_2026-03-10.csv"
    }
    
    try:
        print(f"\n📤 Envoi de la requête à {API_URL}/log-action")
        print(f"📦 Données : {json.dumps(action_data, indent=2)}")
        
        response = requests.post(
            f"{API_URL}/log-action",
            json=action_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCÈS !")
            print(f"   - Log ID: {result.get('log_id')}")
        else:
            print(f"\n❌ ERREUR: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter au serveur")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")


def test_dashboard_access():
    """
    Teste l'accès au dashboard pour vérifier que le serveur fonctionne
    """
    print("\n" + "="*60)
    print("🧪 TEST : Accès au dashboard")
    print("="*60)
    
    try:
        print(f"\n📤 Requête GET vers {BASE_URL}/dashboard")
        response = requests.get(f"{BASE_URL}/dashboard")
        
        print(f"\n📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard accessible !")
        else:
            print(f"⚠️  Réponse inattendue: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter au serveur")
        print("   → Lancez le serveur avec: python app.py")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")


def display_usage_guide():
    """
    Affiche un guide d'utilisation des nouvelles fonctionnalités
    """
    guide = """
╔══════════════════════════════════════════════════════════════════╗
║        🎯 GUIDE D'UTILISATION DES NOUVELLES FONCTIONNALITÉS      ║
╚══════════════════════════════════════════════════════════════════╝

1️⃣  RECHERCHE DANS LES TABLEAUX
   ────────────────────────────────
   • Ouvrez n'importe quelle page (Dashboard, Users, Campagne)
   • Utilisez le champ "🔍 Rechercher..."
   • Les résultats se filtrent en temps réel
   • Le nombre de résultats s'affiche automatiquement

2️⃣  TRI DES COLONNES
   ──────────────────
   • Cliquez sur n'importe quel en-tête de colonne avec ⇅
   • Le tri s'applique instantanément (numérique ou alphabétique)
   • Un indicateur ↑ (ascendant) ou ↓ (descendant) apparaît
   • Cliquez à nouveau pour inverser le tri

3️⃣  EXPORT CSV
   ────────────
   • Cliquez sur le bouton "📥 Exporter CSV"
   • Le fichier se télécharge avec un nom automatique
   • Format : type_nom_date.csv (ex: campagnes_2026-03-10.csv)
   • Compatible Excel avec UTF-8 BOM

4️⃣  CAPTURE DE CLIC ET EMAIL AUTOMATIQUE
   ───────────────────────────────────────
   ✨ FONCTIONNALITÉ PRINCIPALE ✨
   
   Scénario complet :
   
   a) Créez une campagne et ajoutez des utilisateurs
   
   b) Copiez le lien de tracking (bouton 📋 Copier)
      Format : http://127.0.0.1:5000/track?cid=1&uid=1
   
   c) Ouvrez le lien dans un navigateur
   
   d) 🎯 QUE SE PASSE-T-IL ?
      • L'événement "click" est enregistré dans la base de données
      • Les données du clic sont capturées (IP, user-agent, résolution)
      • Un email de sensibilisation est AUTOMATIQUEMENT envoyé
      • L'utilisateur reçoit une alerte expliquant les risques
   
   e) Vérifiez les résultats :
      • Dashboard → Section "Événements récents"
      • Détails de campagne → Onglet "Événements"
      • Consultez Mailtrap pour voir l'email reçu

5️⃣  NOTIFICATIONS AMÉLIORÉES
   ─────────────────────────
   • Plus de popups alert() basiques
   • Notifications toast modernes en haut à droite
   • Couleurs selon le type : vert (succès), rouge (erreur), bleu (info)
   • Auto-disparition après 3 secondes
   • Animations fluides

6️⃣  LOGGING DES ACTIONS
   ──────────────────────
   Toutes les actions importantes sont loggées :
   • Exports CSV
   • Suppressions d'utilisateurs/campagnes
   • Clics sur liens de phishing
   • Accessible via la table action_logs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 CONFIGURATION SMTP REQUISE

Pour que les emails automatiques fonctionnent :

Option 1 : MAILTRAP (recommandé pour tests)
   • Créez un compte sur mailtrap.io
   • Copiez les identifiants SMTP de votre inbox
   • Modifiez config.py :
     SMTP_SERVER = "sandbox.smtp.mailtrap.io"
     SMTP_PORT = 2525
     SMTP_USERNAME = "votre-username"
     SMTP_PASSWORD = "votre-password"

Option 2 : GMAIL
   • Activez la validation en 2 étapes
   • Créez un "App Password"
   • Modifiez config.py :
     SMTP_SERVER = "smtp.gmail.com"
     SMTP_PORT = 587
     SMTP_USERNAME = "votre-email@gmail.com"
     SMTP_PASSWORD = "votre-app-password"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎓 SCÉNARIO DE TEST COMPLET

1. Lancez le serveur :
   > python app.py

2. Ouvrez http://127.0.0.1:5000/dashboard

3. Créez une nouvelle campagne :
   Dashboard → "➕ Créer une nouvelle campagne"

4. Ajoutez une cible (votre email de test) :
   Détails campagne → "➕ Ajouter une cible"

5. Copiez le lien de tracking (📋 Copier)

6. (Optionnel) Envoyez l'email de phishing :
   Détails campagne → "📤 Envoyer les emails"

7. Cliquez sur le lien de tracking

8. 🎉 RÉSULTAT :
   • Page "landing.html" s'affiche (alerte de sensibilisation)
   • Événement enregistré dans la base de données
   • Email automatique envoyé à votre adresse
   • Vérifiez Mailtrap pour voir l'email

9. Testez les autres fonctionnalités :
   • Recherchez dans les tableaux
   • Triez les colonnes
   • Exportez en CSV

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 VÉRIFICATION DES DONNÉES

Via Python :
   from database.db import get_db_connection
   conn = get_db_connection()
   cursor = conn.cursor()
   
   # Voir tous les événements
   cursor.execute("SELECT * FROM events ORDER BY timestamp DESC")
   print(cursor.fetchall())
   
   # Voir tous les logs d'action
   cursor.execute("SELECT * FROM action_logs ORDER BY timestamp DESC")
   print(cursor.fetchall())

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 RÉSULTAT FINAL

✅ 4 fonctions JavaScript pleinement utilisées (100% vs 43% avant)
✅ Capture automatique des clics avec données enrichies
✅ Envoi automatique d'emails de sensibilisation
✅ Interface utilisateur moderne avec recherche, tri et export
✅ Logging complet de toutes les actions
✅ Notifications élégantes au lieu de popups basiques

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(guide)


if __name__ == "__main__":
    # Afficher le guide d'utilisation
    display_usage_guide()
    
    # Menu de test
    print("\n╔══════════════════════════════════════╗")
    print("║      🧪 MENU DE TEST                 ║")
    print("╚══════════════════════════════════════╝\n")
    print("1. Tester l'accès au dashboard")
    print("2. Tester le tracking de clic (avec email)")
    print("3. Tester le logging d'action")
    print("4. Tout tester")
    print("0. Quitter\n")
    
    choice = input("Votre choix : ")
    
    if choice == "1":
        test_dashboard_access()
    elif choice == "2":
        test_track_click()
    elif choice == "3":
        test_log_action()
    elif choice == "4":
        test_dashboard_access()
        test_track_click()
        test_log_action()
    elif choice == "0":
        print("\n👋 Au revoir !")
    else:
        print("\n❌ Choix invalide")
    
    print("\n" + "="*60)
    print("📖 Pour plus d'informations, consultez NOUVELLES_FONCTIONNALITES.md")
    print("="*60 + "\n")
