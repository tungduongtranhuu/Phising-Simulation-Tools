"""
API Routes for Phishing Simulator
Handles tracking, logging, and automated email notifications
"""

from flask import Blueprint, request, jsonify
from database.db import get_connection
from modules.email.sender import send_awareness_email
from datetime import datetime
import logging

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@api_bp.route('/track-click', methods=['POST'])
def track_click():
    """
    Track user click on phishing link and send automated awareness email
    
    Expected JSON:
    {
        "campaign_id": "...",
        "user_id": "...",
        "event_type": "click",
        "timestamp": "...",
        "user_agent": "...",
        "screen_resolution": "...",
        "language": "..."
    }
    """
    try:
        data = request.get_json()
        
        campaign_id = data.get('campaign_id')
        user_id = data.get('user_id')
        event_type = data.get('event_type', 'click')
        user_agent = data.get('user_agent', '')
        screen_resolution = data.get('screen_resolution', '')
        language = data.get('language', '')
        
        # Get user IP
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        if not campaign_id or not user_id:
            return jsonify({
                'success': False,
                'message': 'campaign_id et user_id requis'
            }), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get user email
        cursor.execute('SELECT user_email FROM users WHERE user_id = ?', (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Utilisateur introuvable'
            }), 404
        
        user_email = user_row[0]
        
        # Get campaign info
        cursor.execute('SELECT campaign_name FROM campaigns WHERE campaign_id = ?', (campaign_id,))
        campaign_row = cursor.fetchone()
        
        if not campaign_row:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Campagne introuvable'
            }), 404
        
        campaign_name = campaign_row[0]
        
        # Record the tracking event
        cursor.execute('''
            INSERT INTO events (campaign_id, user_id, event_type, ip, user_agent, event_timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            campaign_id,
            user_id,
            event_type,
            ip_address,
            f"{user_agent} | {screen_resolution} | {language}",
            datetime.now().isoformat()
        ))
        
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        
        # Send automated awareness email
        email_sent = False
        email_error = None
        
        try:
            send_awareness_email(
                to_email=user_email,
                campaign_name=campaign_name,
                user_id=user_id
            )
            email_sent = True
            logger.info(f"Email de sensibilisation envoyé à {user_email}")
        except Exception as email_err:
            email_error = str(email_err)
            logger.error(f"Erreur envoi email à {user_email}: {email_err}")
        
        return jsonify({
            'success': True,
            'message': 'Clic tracé avec succès',
            'event_id': event_id,
            'email_sent': email_sent,
            'email_error': email_error,
            'user_email': user_email,
            'campaign_name': campaign_name
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur track-click: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        }), 500


@api_bp.route('/log-action', methods=['POST'])
def log_action():
    """
    Log user actions for analytics
    
    Expected JSON:
    {
        "action": "export_csv",
        "timestamp": "...",
        "page": "/dashboard",
        "table": "campaigns-table",
        "filename": "export.csv"
    }
    """
    try:
        data = request.get_json()
        
        # For now, just log to console
        # In production, you could store in database or analytics service
        logger.info(f"User Action: {data}")
        
        # Optionally store in database
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create action_logs table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                page TEXT,
                details TEXT,
                ip_address TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Insert log
        cursor.execute('''
            INSERT INTO action_logs (action_type, page, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data.get('action', 'unknown'),
            data.get('page', ''),
            str(data),
            request.headers.get('X-Forwarded-For', request.remote_addr),
            data.get('timestamp', datetime.now().isoformat())
        ))
        
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'log_id': log_id
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur log-action: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
