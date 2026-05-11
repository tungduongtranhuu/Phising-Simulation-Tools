from flask import Blueprint, request, redirect, render_template, flash, jsonify
from modules.campaign.manager import create_campaign, get_campaign
from modules.campaign.targets import add_single_user_to_campaign, list_targets
from database.db import get_events_by_campaign, get_connection
from modules.email.sender import send_campaign_emails
from config import Config
import sys
import os

# Ajouter le dossier delete au path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'delete'))

campaign_bp = Blueprint("campaign", __name__)

@campaign_bp.route("/campaign/create", methods=["GET", "POST"])
def create_campaign_route():
    if request.method == "POST":
        name = request.form["name"]
        create_campaign(name)
        return redirect("/dashboard")
    return render_template("create_campaign.html")

@campaign_bp.route("/campaign/<int:campaign_id>")
def campaign_detail(campaign_id):
    campaign = get_campaign(campaign_id)
    if not campaign:
        return "Campaign not found", 404
    
    users = list_targets(campaign_id)
    events = get_events_by_campaign(campaign_id)
    
    return render_template("campaign_detail.html", 
                         campaign=campaign, 
                         users=users,
                         events=events)

@campaign_bp.route("/campaign/<int:campaign_id>/add_user", methods=["POST"])
def add_user_to_campaign_route(campaign_id):
    email = request.form["email"]
    try:
        add_single_user_to_campaign(campaign_id, email)
    except Exception as e:
        # Handle duplicates or other errors silently or with flash message
        pass
    return redirect(f"/campaign/{campaign_id}")


@campaign_bp.route("/campaign/<int:campaign_id>/send_emails", methods=["POST"])
def send_emails_to_campaign_users(campaign_id):
    """
    Gửi email đến tất cả users trong campaign qua Mailtrap
    Send emails to all users in campaign via Mailtrap
    """
    try:
        # Lấy campaign info
        campaign = get_campaign(campaign_id)
        if not campaign:
            return "Campaign not found", 404
        
        # Lấy danh sách users trong campaign
        users = list_targets(campaign_id)
        
        if not users:
            print(f"⚠️  Campaign {campaign_id} không có user nào")
            return redirect(f"/campaign/{campaign_id}")
        
        # Cấu hình SMTP từ .env
        config = Config()
        smtp_config = {
            'server': config.MAIL_SERVER,
            'port': config.MAIL_PORT,
            'email': config.MAIL_USERNAME,
            'password': config.MAIL_PASSWORD,
            'use_tls': config.MAIL_USE_TLS
        }
        
        # Gửi email đến tất cả users
        print(f"\n{'='*70}")
        print(f"📧 Gửi email cho Campaign: {campaign.campaign_name}")
        print(f"👥 Số lượng users: {len(users)}")
        print(f"🔧 Server: {smtp_config['server']}")
        print(f"{'='*70}\n")
        
        results = send_campaign_emails(
            smtp_config=smtp_config,
            campaign_id=campaign_id,
            users=users,
            base_url=config.APP_URL
        )
        
        print(f"\n{'='*70}")
        print(f"✅ Kết quả gửi email:")
        print(f"   Thành công: {results['success']}/{len(users)}")
        print(f"   Thất bại: {results['failed']}/{len(users)}")
        if results['errors']:
            print(f"   Lỗi: {results['errors']}")
        print(f"🔍 Kiểm tra email tại: https://mailtrap.io")
        print(f"{'='*70}\n")
        
        return redirect(f"/campaign/{campaign_id}")
        
    except Exception as e:
        print(f"❌ Lỗi khi gửi email: {e}")
        import traceback
        traceback.print_exc()
        return f"Error sending emails: {str(e)}", 500


@campaign_bp.route("/campaign/<int:campaign_id>/delete", methods=["POST"])
def delete_campaign_route(campaign_id):
    """
    Supprimer une campagne et toutes les données associées de manière sécurisée
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Vérifier si la campagne existe
        cursor.execute("SELECT campaign_id, campaign_name FROM campaigns WHERE campaign_id = ?", (campaign_id,))
        campaign = cursor.fetchone()
        
        if not campaign:
            conn.close()
            return jsonify({"success": False, "message": "Campagne introuvable"}), 404
        
        campaign_name = campaign[1]
        
        # Compter les enregistrements associés
        cursor.execute("SELECT COUNT(*) FROM events WHERE campaign_id = ?", (campaign_id,))
        events_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM campaign_targets WHERE campaign_id = ?", (campaign_id,))
        targets_count = cursor.fetchone()[0]
        
        print(f"\n🗑️  Suppression de la campagne ID: {campaign_id}")
        print(f"   Nom: {campaign_name}")
        print(f"   Événements: {events_count}")
        print(f"   Cibles: {targets_count}")
        
        # Supprimer dans l'ordre (sécurisé pour les clés étrangères)
        # 1. Supprimer les événements d'abord
        cursor.execute("DELETE FROM events WHERE campaign_id = ?", (campaign_id,))
        print(f"   ✅ {events_count} événements supprimés")
        
        # 2. Supprimer campaign_targets
        cursor.execute("DELETE FROM campaign_targets WHERE campaign_id = ?", (campaign_id,))
        print(f"   ✅ {targets_count} cibles de campagne supprimées")
        
        # 3. Enfin supprimer la campagne
        cursor.execute("DELETE FROM campaigns WHERE campaign_id = ?", (campaign_id,))
        print(f"   ✅ Campagne '{campaign_name}' supprimée")
        
        conn.commit()
        conn.close()
        
        print("✨ Terminé! La campagne a été supprimée en toute sécurité.\n")
        
        return jsonify({
            "success": True, 
            "message": f"Campagne '{campaign_name}' supprimée avec succès",
            "deleted": {
                "events": events_count,
                "targets": targets_count
            }
        })
        
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"success": False, "message": f"Erreur: {str(e)}"}), 500
