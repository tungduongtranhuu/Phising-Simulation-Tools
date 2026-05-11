from flask import Blueprint, request, redirect
from modules.tracking.tracker import track_event

tracking_bp = Blueprint("tracking", __name__)

@tracking_bp.route("/track")  #/track?cid=CAMPAIGN_ID&uid=USER_ID phải gửi đúng theo như cặp giá trị trong database campaign_targets 
def tracking_route():
    try:
        # Vérifier que les paramètres existent
        cid = request.args.get("cid")
        uid = request.args.get("uid")
        
        if not cid or not uid:
            # Paramètres manquants, rediriger vers landing
            return redirect("/landing")
        
        campaign_id = int(cid)
        user_id = int(uid)

        ip = request.remote_addr
        user_agent = request.headers.get("User-Agent", "Unknown")

        track_event(campaign_id, user_id, "clicked", ip, user_agent)

        return redirect("/landing")

    except Exception as e:
        # En cas d'erreur, rediriger quand même vers landing
        print(f"Erreur tracking: {e}")
        return redirect("/landing")

