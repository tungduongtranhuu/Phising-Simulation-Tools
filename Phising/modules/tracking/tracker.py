from datetime import datetime
from database.db import user_belongs_to_campaign, insert_event

# =========================
# Business Logic Layer
# =========================

def track_event(campaign_id, user_id, event_type, ip, user_agent):
    # Policy check
    if not user_belongs_to_campaign(campaign_id, user_id):
        raise Exception("User not part of this campaign")

    # Business timestamp logic
    event_timestamp = datetime.now().isoformat()

    insert_event(
        campaign_id,
        user_id,
        event_type,
        ip,
        user_agent,
        event_timestamp
    )
