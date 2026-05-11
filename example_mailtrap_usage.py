"""
Exemple d'utilisation de l'envoi d'emails avec Mailtrap dans l'application Flask
Ce script montre comment intégrer Mailtrap dans vos routes/campaigns
"""

from modules.email.sender import send_campaign_emails, send_phishing_email
from database.models import Users
from database.db import get_campaign_users
from config import Config
import os

# ==========================================
# MÉTHODE 1: Utiliser la configuration depuis .env
# ==========================================

def send_emails_with_env_config(campaign_id):
    """
    Utilise la configuration depuis les variables d'environnement (.env file)
    
    Usage:
        1. Créez un fichier .env à la racine
        2. Ajoutez vos identifiants Mailtrap
        3. Appelez cette fonction
    """
    config = Config()
    
    smtp_config = {
        'server': config.MAIL_SERVER,
        'port': config.MAIL_PORT,
        'email': config.MAIL_USERNAME,
        'password': config.MAIL_PASSWORD,
        'use_tls': config.MAIL_USE_TLS
    }
    
    # Récupérer les utilisateurs de la campagne
    users = get_campaign_users(campaign_id)
    
    # Envoyer les emails
    results = send_campaign_emails(
        smtp_config=smtp_config,
        campaign_id=campaign_id,
        users=users,
        base_url=config.APP_URL
    )
    
    return results


# ==========================================
# MÉTHODE 2: Configuration directe (pour tests rapides)
# ==========================================

def send_emails_with_direct_config(campaign_id):
    """
    Configuration directe sans fichier .env
    Pratique pour tester rapidement
    """
    smtp_config = {
        'server': 'sandbox.smtp.mailtrap.io',
        'port': 2525,
        'email': os.getenv('MAILTRAP_USERNAME', 'YOUR_USERNAME'),
        'password': os.getenv('MAILTRAP_PASSWORD', 'YOUR_PASSWORD'),
        'use_tls': True
    }
    
    users = get_campaign_users(campaign_id)
    
    results = send_campaign_emails(
        smtp_config=smtp_config,
        campaign_id=campaign_id,
        users=users,
        base_url='http://localhost:5000'
    )
    
    return results


# ==========================================
# MÉTHODE 3: Envoyer à un seul utilisateur
# ==========================================

def send_single_test_email():
    """
    Envoie un email de test à un seul utilisateur
    Idéal pour tester avant d'envoyer une campagne complète
    """
    config = Config()
    
    # Créer un utilisateur de test
    test_user = Users(
        user_id=999,
        user_email='test@example.com'  # Avec Mailtrap, n'importe quel email fonctionne
    )
    
    try:
        send_phishing_email(
            smtp_server=config.MAIL_SERVER,
            smtp_port=config.MAIL_PORT,
            sender_email=config.MAIL_USERNAME,
            sender_password=config.MAIL_PASSWORD,
            campaign_id=1,
            user=test_user,
            base_url=config.APP_URL,
            use_tls=config.MAIL_USE_TLS
        )
        
        print(f"✅ Email de test envoyé à {test_user.user_email}")
        print("🔍 Vérifiez votre inbox Mailtrap sur https://mailtrap.io")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


# ==========================================
# INTÉGRATION DANS UNE ROUTE FLASK
# ==========================================

def example_flask_route():
    """
    Exemple d'intégration dans une route Flask
    
    Dans routes/campaign_routes.py, vous pourriez avoir:
    """
    from flask import jsonify, request
    
    # @app.route('/api/campaigns/<int:campaign_id>/send', methods=['POST'])
    # def send_campaign_emails_route(campaign_id):
    #     try:
    #         # Utiliser la méthode 1
    #         results = send_emails_with_env_config(campaign_id)
    #         
    #         return jsonify({
    #             'success': True,
    #             'sent': results['success'],
    #             'failed': results['failed'],
    #             'errors': results['errors']
    #         })
    #     
    #     except Exception as e:
    #         return jsonify({
    #             'success': False,
    #             'error': str(e)
    #         }), 500
    
    pass


# ==========================================
# TESTS RAPIDES
# ==========================================

if __name__ == "__main__":
    print("=" * 70)
    print("EXEMPLES D'UTILISATION - ENVOI D'EMAILS AVEC MAILTRAP")
    print("=" * 70)
    
    print("\n1️⃣  Test d'envoi d'un seul email:")
    print("   → send_single_test_email()")
    
    print("\n2️⃣  Envoi d'une campagne complète avec config .env:")
    print("   → results = send_emails_with_env_config(campaign_id=1)")
    
    print("\n3️⃣  Envoi avec configuration directe:")
    print("   → results = send_emails_with_direct_config(campaign_id=1)")
    
    print("\n" + "=" * 70)
    print("💡 Pour tester, décommentez la ligne ci-dessous:")
    print("=" * 70)
    
    # Décommentez pour tester:
    # send_single_test_email()
    
    print("\n⚠️  N'oubliez pas de configurer Mailtrap d'abord!")
    print("   1. Créez un compte sur https://mailtrap.io")
    print("   2. Configurez le fichier .env avec vos identifiants")
    print("   3. Ou définissez les variables d'environnement MAILTRAP_USERNAME et MAILTRAP_PASSWORD")
    print("\n📖 Voir GUIDE_MAILTRAP.md ou HUONG_DAN_MAILTRAP.md pour plus de détails")
