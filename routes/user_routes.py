"""
Routes pour la gestion des utilisateurs
"""

from flask import Blueprint, request, redirect, render_template, jsonify
from database.db import get_connection
import sys
import os

# Ajouter le dossier delete au path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'delete'))

user_bp = Blueprint("user", __name__)


@user_bp.route("/user/<int:user_id>/delete", methods=["POST"])
def delete_user_route(user_id):
    """
    Supprimer un utilisateur et toutes les données associées de manière sécurisée
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Rechercher l'utilisateur
        cursor.execute("SELECT user_id, user_email FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({"success": False, "message": "Utilisateur introuvable"}), 404
        
        user_email = user[1]
        
        # Compter les enregistrements associés
        cursor.execute("SELECT COUNT(*) FROM events WHERE user_id = ?", (user_id,))
        events_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM campaign_targets WHERE user_id = ?", (user_id,))
        targets_count = cursor.fetchone()[0]
        
        print(f"\n🗑️  Suppression de l'utilisateur ID: {user_id}")
        print(f"   Email: {user_email}")
        print(f"   Événements: {events_count}")
        print(f"   Cibles: {targets_count}")
        
        # Supprimer dans l'ordre (sécurisé pour les clés étrangères)
        # 1. Supprimer les événements d'abord
        cursor.execute("DELETE FROM events WHERE user_id = ?", (user_id,))
        print(f"   ✅ {events_count} événements supprimés")
        
        # 2. Supprimer campaign_targets
        cursor.execute("DELETE FROM campaign_targets WHERE user_id = ?", (user_id,))
        print(f"   ✅ {targets_count} cibles de campagne supprimées")
        
        # 3. Enfin supprimer l'utilisateur
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        print(f"   ✅ Utilisateur '{user_email}' supprimé")
        
        conn.commit()
        conn.close()
        
        print("✨ Terminé! L'utilisateur a été supprimé en toute sécurité.\n")
        
        return jsonify({
            "success": True, 
            "message": f"Utilisateur '{user_email}' supprimé avec succès",
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


@user_bp.route("/users")
def list_users():
    """
    Afficher la liste de tous les utilisateurs
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                u.user_id,
                u.user_email,
                COUNT(DISTINCT ct.campaign_id) as campaigns_count,
                COUNT(DISTINCT e.id) as events_count
            FROM users u
            LEFT JOIN campaign_targets ct ON u.user_id = ct.user_id
            LEFT JOIN events e ON u.user_id = e.user_id
            GROUP BY u.user_id, u.user_email
            ORDER BY u.user_id
        """)
        
        users = cursor.fetchall()
        conn.close()
        
        # Convertir en liste de dictionnaires
        users_list = []
        for user in users:
            users_list.append({
                'user_id': user[0],
                'user_email': user[1],
                'campaigns_count': user[2],
                'events_count': user[3]
            })
        
        return render_template("users_list.html", users=users_list)
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des utilisateurs: {e}")
        return f"Erreur: {str(e)}", 500
