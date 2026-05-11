from flask import Blueprint, render_template
from modules.campaign.manager import list_campaigns
from database.db import get_connection

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    campaigns = list_campaigns()
    
    # Get statistics
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Total events
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    
    # Recent events (last 10)
    cursor.execute("""
        SELECT e.*, c.campaign_name, u.user_email
        FROM events e
        JOIN campaigns c ON e.campaign_id = c.campaign_id
        JOIN users u ON e.user_id = u.user_id
        ORDER BY e.event_timestamp DESC
        LIMIT 10
    """)
    recent_events = cursor.fetchall()
    
    conn.close()
    
    stats = {
        'total_campaigns': len(campaigns),
        'total_users': total_users,
        'total_events': total_events,
        'active_campaigns': len([c for c in campaigns if c.campaign_status == 'active'])
    }
    
    return render_template("dashboard.html", 
                         campaigns=campaigns, 
                         stats=stats,
                         recent_events=recent_events)
