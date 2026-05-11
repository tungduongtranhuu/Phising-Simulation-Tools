"""
Script de test pour l'envoi d'emails de sensibilisation au phishing

⚠️  AVERTISSEMENT IMPORTANT :
    N'utilisez ce script QUE pour envoyer des emails à VOS PROPRES adresses !
    Toute utilisation à des fins malveillantes est illégale.

✅ USAGE LÉGITIME :
    - Tests sur vos propres emails (Gmail, Outlook, etc.)
    - Environnement de test (Mailtrap)
    - Formation en entreprise avec autorisation écrite

📚 Consultez GUIDE_EMAIL.md pour la documentation complète
"""

from modules.email.sender import send_phishing_email
from database.models import Users
import sys


# ==========================================
# CONFIGURATION - MODIFIEZ ICI
# ==========================================

# ÉTAPE 1 : Choisissez votre méthode d'envoi
USE_MAILTRAP = True  # True = Mailtrap (recommandé pour débuter), False = Gmail/SMTP réel

if USE_MAILTRAP:
    # MAILTRAP - Les emails ne sont PAS réellement envoyés
    # 1. Créez un compte sur https://mailtrap.io
    # 2. Créez une inbox de test
    # 3. Remplacez les valeurs ci-dessous par vos identifiants Mailtrap
    
    smtp_config = {
        'server': 'sandbox.smtp.mailtrap.io',
        'port': 2525,
        'email': '1b7860f0311bc5',      # ← Changez ici
        'password': 'da50aa5056f1ef',   # ← Changez ici
        'use_tls': True
    }
    
    # Avec Mailtrap, l'email peut être n'importe quoi (il n'est pas vraiment envoyé)
    test_user = Users(
        user_id=15,
        user_email='test@example.com'
    )
    
else:
    # GMAIL ou autre SMTP réel
    # Pour Gmail :
    # 1. Activez la validation en 2 étapes : https://myaccount.google.com/security
    # 2. Créez un mot de passe d'application : https://myaccount.google.com/apppasswords
    # 3. Utilisez ce mot de passe ci-dessous (format: xxxxxxxxxxxx sans espaces)
    
    smtp_config = {
        'server': 'smtp.gmail.com',
        'port': 587,
        'email': 'VOTRE_EMAIL@gmail.com',        # ← Changez ici
        'password': 'VOTRE_APP_PASSWORD',        # ← Changez ici (16 caractères sans espaces)
        'use_tls': True
    }
    
    # ⚠️  IMPORTANT : Utilisez UNIQUEMENT VOTRE propre email !
    test_user = Users(
        user_id=15,
        user_email='VOTRE_EMAIL@gmail.com'      # ← Changez ici
    )


# ÉTAPE 2 : Configuration de l'application
BASE_URL = "http://localhost:5000"  # Changez si votre app tourne sur un autre port


# ==========================================
# FONCTION DE TEST
# ==========================================

def test_email_sending():
    """Teste l'envoi d'un email de sensibilisation"""
    
    print("=" * 70)
    print("📧 TEST D'ENVOI D'EMAIL - SIMULATEUR DE PHISHING")
    print("=" * 70)
    print()
    
    # Affichage de la configuration
    print("📋 Configuration :")
    print(f"   Serveur SMTP : {smtp_config['server']}")
    print(f"   Port         : {smtp_config['port']}")
    print(f"   Expéditeur   : {smtp_config['email']}")
    print(f"   Destinataire : {test_user.user_email}")
    print(f"   TLS activé   : {smtp_config['use_tls']}")
    print()
    
    # Vérification des identifiants
    if smtp_config['email'].startswith('VOTRE_'):
        print("❌ ERREUR : Vous devez modifier la configuration !")
        print()
        print("➡️  Étapes à suivre :")
        print("   1. Ouvrez le fichier test_email_simple.py")
        print("   2. Modifiez la section CONFIGURATION")
        print("   3. Remplacez les valeurs par vos identifiants")
        print()
        if USE_MAILTRAP:
            print("   Pour Mailtrap : https://mailtrap.io")
        else:
            print("   Pour Gmail : https://myaccount.google.com/apppasswords")
        print()
        return False
    
    # Confirmation de sécurité
    if not USE_MAILTRAP:
        print("⚠️  AVERTISSEMENT DE SÉCURITÉ")
        print()
        print("   Vous êtes sur le point d'envoyer un VRAI email.")
        print(f"   Destinataire : {test_user.user_email}")
        print()
        print("   Confirmez que :")
        print("   ✓ C'est VOTRE adresse email")
        print("   ✓ Vous avez l'autorisation de l'utiliser")
        print("   ✓ Vous comprenez qu'il s'agit d'un test éducatif")
        print()
        
        confirmation = input("   Tapez 'OUI' en majuscules pour continuer : ")
        
        if confirmation != 'OUI':
            print()
            print("❌ Test annulé par l'utilisateur.")
            print()
            return False
    
    print()
    print("📤 Envoi de l'email en cours...")
    print() 
    
    try:
        # Envoi de l'email
        result = send_phishing_email(
            smtp_server=smtp_config['server'],
            smtp_port=smtp_config['port'],
            sender_email=smtp_config['email'],
            sender_password=smtp_config['password'],
            campaign_id=36,
            user=test_user,
            base_url=BASE_URL,
            use_tls=smtp_config['use_tls'],
            use_html=True  # Envoie en format HTML
        )
        
        print()
        print("=" * 70)
        print("✅ SUCCÈS - L'email a été envoyé !")
        print("=" * 70)
        print()
        
        # Instructions de vérification
        if USE_MAILTRAP:
            print("📥 Vérification :")
            print("   1. Connectez-vous sur https://mailtrap.io")
            print("   2. Allez dans votre inbox de test")
            print("   3. Vous devriez voir l'email envoyé")
            print("   4. Cliquez dessus pour voir le rendu HTML")
        else:
            print("📥 Vérification :")
            print(f"   1. Vérifiez votre boîte de réception : {test_user.user_email}")
            print("   2. L'email peut arriver dans quelques secondes")
            print("   3. Vérifiez aussi vos spams/courrier indésirable")
            print()
            print("🔗 Test du lien de tracking :")
            print(f"   {BASE_URL}/track?cid=36&uid={test_user.user_id}")
            print()
            print("   ⚠️  Si vous cliquez sur le lien dans l'email,")
            print("      l'événement sera enregistré dans la base de données")
        
        print()
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERREUR lors de l'envoi")
        print("=" * 70)
        print()
        print(f"Détails : {e}")
        print()
        print("🔧 Solutions possibles :")
        print()
        
        if "Authentication" in str(e):
            print("   1. Vérifiez votre email et mot de passe")
            if not USE_MAILTRAP:
                print("   2. Pour Gmail, vérifiez que :")
                print("      - La validation en 2 étapes est activée")
                print("      - Vous utilisez un 'App Password' (pas votre mot de passe normal)")
                print("      - Le mot de passe est sans espaces (16 caractères)")
                print("      - Générez-en un nouveau si nécessaire :")
                print("        → https://myaccount.google.com/apppasswords")
        
        elif "Connection" in str(e):
            print("   1. Vérifiez votre connexion internet")
            print("   2. Vérifiez le serveur SMTP et le port")
            print(f"      Serveur : {smtp_config['server']}")
            print(f"      Port    : {smtp_config['port']}")
        
        else:
            print("   1. Consultez le message d'erreur ci-dessus")
            print("   2. Vérifiez votre configuration SMTP")
            print("   3. Consultez GUIDE_EMAIL.md pour plus d'aide")
        
        print()
        return False


# ==========================================
# POINT D'ENTRÉE
# ==========================================

if __name__ == "__main__":
    print()
    
    try:
        success = test_email_sending()
        
        if success:
            print("=" * 70)
            print("🎉 TEST RÉUSSI !")
            print("=" * 70)
            print()
            print("📚 Prochaines étapes :")
            print("   - Consultez GUIDE_EMAIL.md pour plus d'options")
            print("   - Testez différents templates d'emails")
            print("   - Intégrez l'envoi d'emails dans vos campagnes")
            print()
            sys.exit(0)
        else:
            print("=" * 70)
            print("⚠️  TEST NON EFFECTUÉ")
            print("=" * 70)
            print()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print()
        print()
        print("❌ Test interrompu par l'utilisateur (Ctrl+C)")
        print()
        sys.exit(1)
    
    except Exception as e:
        print()
        print("❌ ERREUR INATTENDUE :")
        print(f"   {e}")
        print()
        print("   Consultez GUIDE_EMAIL.md pour obtenir de l'aide")
        print()
        sys.exit(1)
