"""
Module d'envoi d'emails pour les campagnes de sensibilisation au phishing

⚠️ AVERTISSEMENT LÉGAL :
- N'utilisez cette fonctionnalité QUE sur vos propres adresses email
- Ou avec le consentement écrit explicite des destinataires
- Dans le cadre d'une formation autorisée au sein de votre organisation
- Toute utilisation malveillante est illégale et punissable par la loi

✅ USAGE RECOMMANDÉ :
- Tests sur vos propres emails (Gmail, Outlook, etc.)
- Environnement de test (Mailtrap, Ethereal Email)
- Formation en entreprise avec autorisation RH/DSI
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from modules.email.templates import build_tracking_link, build_email_content, build_html_email
from database.db import insert_event
from datetime import datetime
import ssl
import time


def send_phishing_email(
    smtp_server,
    smtp_port,
    sender_email,
    sender_password,
    campaign_id,
    user,
    base_url="http://127.0.0.1:5000",
    use_tls=True,
    use_html=True
):
    """
    Envoie un email de test pour une campagne de sensibilisation
    
    Args:
        smtp_server (str): Serveur SMTP (ex: smtp.gmail.com)
        smtp_port (int): Port SMTP (587 pour TLS, 465 pour SSL)
        sender_email (str): Email expéditeur
        sender_password (str): Mot de passe ou token d'application
        campaign_id (int): ID de la campagne
        user (User): Objet utilisateur destinataire
        base_url (str): URL de base pour le tracking
        use_tls (bool): Utiliser TLS (recommandé)
        use_html (bool): Envoyer en HTML plutôt que texte brut
    
    Returns:
        bool: True si l'envoi a réussi, False sinon
    
    Raises:
        Exception: En cas d'erreur d'envoi
    """
    try:
        # Construire le lien de tracking
        tracking_link = build_tracking_link(base_url, campaign_id, user.user_id)

        # Créer le message
        if use_html:
            msg = MIMEMultipart('alternative')
            subject, text_body, html_body = build_html_email(user.user_email, tracking_link)
            
            # Ajouter les deux versions (texte et HTML)
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
        else:
            subject, body = build_email_content(user.user_email, tracking_link)
            msg = MIMEText(body, 'plain')
        
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = user.user_email

        # Connexion et envoi sécurisé
        context = ssl.create_default_context()
        
        if use_tls and smtp_port in [587, 2525, 25]:
            # STARTTLS (pour Gmail, Outlook, Mailtrap)
            # Port 587: Standard SMTP with STARTTLS
            # Port 2525: Mailtrap et alternative SMTP
            # Port 25: SMTP standard (rare)
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.set_debuglevel(0)  # Mettre à 1 pour debug
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                print(f"✅ Email envoyé à {user.user_email}")
        elif smtp_port == 465:
            # SSL/TLS direct
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=30) as server:
                server.set_debuglevel(0)
                server.login(sender_email, sender_password)
                server.send_message(msg)
                print(f"✅ Email envoyé à {user.user_email}")
        else:
            # Sans TLS (uniquement pour tests locaux)
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.set_debuglevel(0)
                if sender_password:  # Si un mot de passe est fourni
                    server.login(sender_email, sender_password)
                server.send_message(msg)
                print(f"✅ Email envoyé à {user.user_email}")

        # Enregistrer l'événement d'envoi
        insert_event(
            campaign_id,
            user.user_id,
            "sent",
            "0.0.0.0",
            "SMTP",
            datetime.now().isoformat()
        )
        
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Erreur d'authentification SMTP: {e}")
        print("→ Vérifiez votre email et mot de passe")
        print("→ Si vous utilisez Gmail, activez un 'App Password'")
        raise
    
    except smtplib.SMTPException as e:
        print(f"❌ Erreur SMTP: {e}")
        raise
    
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
        raise


def send_campaign_emails(
    smtp_config,
    campaign_id,
    users,
    base_url="http://127.0.0.1:5000"
):
    """
    Envoie des emails à tous les utilisateurs d'une campagne
    
    Args:
        smtp_config (dict): Configuration SMTP
            {
                'server': 'smtp.gmail.com',
                'port': 587,
                'email': 'your-email@gmail.com',
                'password': 'your-app-password',
                'use_tls': True
            }
        campaign_id (int): ID de la campagne
        users (list): Liste d'objets User
        base_url (str): URL de base pour le tracking
    
    Returns:
        dict: Résultats de l'envoi
            {
                'success': 5,
                'failed': 0,
                'errors': []
            }
    """
    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    print(f"\n📧 Envoi d'emails pour la campagne {campaign_id}...")
    print(f"👥 Nombre de destinataires: {len(users)}\n")
    
    for index, user in enumerate(users, 1):
        try:
            print(f"[{index}/{len(users)}] Envoi à {user.user_email}...")
            
            send_phishing_email(
                smtp_server=smtp_config['server'],
                smtp_port=smtp_config['port'],
                sender_email=smtp_config['email'],
                sender_password=smtp_config['password'],
                campaign_id=campaign_id,
                user=user,
                base_url=base_url,
                use_tls=smtp_config.get('use_tls', True)
            )
            results['success'] += 1
            
            # Petit délai entre chaque email pour éviter le rate limiting
            if index < len(users):  # Pas de délai après le dernier email
                time.sleep(0.5)  # 500ms de pause
                
        except Exception as e:
            results['failed'] += 1
            error_msg = str(e)
            results['errors'].append({
                'user': user.user_email,
                'error': error_msg
            })
            print(f"❌ Échec pour {user.user_email}: {error_msg}")
            
            # Continuer avec les autres users même si un échoue
            continue
    
    print(f"\n📊 Résultats:")
    print(f"   ✅ Réussis: {results['success']}")
    print(f"   ❌ Échoués: {results['failed']}")
    
    return results


def send_awareness_email(to_email, campaign_name, user_id):
    """
    Envoie un email de sensibilisation automatique après qu'un utilisateur 
    a cliqué sur un lien de phishing
    
    Args:
        to_email (str): Email du destinataire
        campaign_name (str): Nom de la campagne
        user_id (str): ID de l'utilisateur
    
    Returns:
        bool: True si l'envoi a réussi
    """
    try:
        # Configuration SMTP depuis config ou environnement
        from config import DevelopmentConfig
        
        smtp_server = DevelopmentConfig.SMTP_SERVER
        smtp_port = DevelopmentConfig.SMTP_PORT
        sender_email = DevelopmentConfig.SMTP_USERNAME
        sender_password = DevelopmentConfig.SMTP_PASSWORD
        use_tls = DevelopmentConfig.SMTP_USE_TLS
        
        # Créer le message d'alerte
        msg = MIMEMultipart('alternative')
        msg["Subject"] = f"⚠️ ALERTE : Vous avez cliqué sur un lien de phishing"
        msg["From"] = sender_email
        msg["To"] = to_email
        
        # Corps du message
        text_body = f"""
🚨 ATTENTION - SIMULATION DE PHISHING 🚨

Bonjour,

Vous venez de cliquer sur un lien dans le cadre de la campagne de sensibilisation : "{campaign_name}"

✋ CECI ÉTAIT UN TEST DE SÉCURITÉ

Dans un scénario réel, vous auriez pu :
• Compromettre vos identifiants personnels
• Exposer des données sensibles de l'entreprise
• Installer un logiciel malveillant
• Devenir victime d'une fraude financière

🛡️ CONSEILS DE SÉCURITÉ :

1. Vérifiez toujours l'expéditeur avant de cliquer
2. Ne cliquez jamais sur des liens suspects
3. Vérifiez l'URL avant de saisir des informations
4. En cas de doute, contactez votre service informatique
5. Signalez tout email suspect

📚 RESSOURCES :
- Guide de sécurité informatique
- Formation sur la cybersécurité
- Contact du service IT

Cette simulation vise à vous sensibiliser aux dangers du phishing.
Restez vigilant !

---
Campagne : {campaign_name}
ID Utilisateur : {user_id}
        """
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .alert-box {{ background: #fee; border-left: 4px solid #e44; padding: 20px; margin: 20px 0; }}
        .success-box {{ background: #efe; border-left: 4px solid #4a4; padding: 20px; margin: 20px 0; }}
        .tips {{ background: #f9f9f9; padding: 15px; border-radius: 5px; }}
        .tips ul {{ margin: 10px 0; }}
        h1 {{ color: #e44; }}
        h2 {{ color: #333; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚨 ATTENTION - SIMULATION DE PHISHING</h1>
        
        <div class="alert-box">
            <strong>⚠️ Vous venez de cliquer sur un lien de phishing !</strong>
            <p>Cette alerte fait partie de la campagne de sensibilisation : <strong>"{campaign_name}"</strong></p>
        </div>
        
        <div class="success-box">
            <strong>✋ CECI ÉTAIT UN TEST DE SÉCURITÉ</strong>
            <p>Heureusement, il s'agissait d'une simulation. Dans un scénario réel, vous auriez pu compromettre vos données.</p>
        </div>
        
        <h2>⚠️ Risques potentiels dans un vrai phishing :</h2>
        <ul>
            <li>Vol de vos identifiants personnels</li>
            <li>Exposition de données sensibles de l'entreprise</li>
            <li>Installation de logiciels malveillants</li>
            <li>Fraude financière</li>
        </ul>
        
        <div class="tips">
            <h2>🛡️ Conseils de sécurité pour l'avenir :</h2>
            <ul>
                <li><strong>Vérifiez l'expéditeur</strong> avant de cliquer sur un lien</li>
                <li><strong>Survolez les liens</strong> pour voir l'URL réelle</li>
                <li><strong>Vérifiez l'URL</strong> avant de saisir des informations</li>
                <li><strong>Méfiez-vous des urgences</strong> : les phisheurs créent un sentiment d'urgence</li>
                <li><strong>En cas de doute</strong>, contactez votre service informatique</li>
            </ul>
        </div>
        
        <h2>📚 Ressources supplémentaires :</h2>
        <ul>
            <li>Guide de sécurité informatique interne</li>
            <li>Formation en ligne sur la cybersécurité</li>
            <li>Contact du service IT pour questions</li>
        </ul>
        
        <div class="footer">
            <p><strong>Cette simulation vise à vous sensibiliser aux dangers du phishing.</strong></p>
            <p>Restez vigilant et continuez à vous former !</p>
            <p style="font-size: 0.8em; color: #999;">
                Campagne : {campaign_name}<br>
                ID Utilisateur : {user_id}
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        # Ajouter les deux versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Envoyer l'email
        context = ssl.create_default_context()
        
        if use_tls and smtp_port in [587, 2525, 25]:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                server.send_message(msg)
        elif smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                if sender_password:
                    server.login(sender_email, sender_password)
                server.send_message(msg)
        
        print(f"✅ Email de sensibilisation envoyé à {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email de sensibilisation: {e}")
        raise

