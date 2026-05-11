from datetime import datetime
from database.db import create_campaign as db_create_campaign
from database.db import get_all_campaign as db_get_all_campaign
from database.db import get_campaign_by_id as db_get_campaign_by_id

def create_campaign(name):
    if not name or name.strip() == "":
        raise ValueError("Campaign name cannot be empty")
    return db_create_campaign(name)

def list_campaigns():
    return db_get_all_campaign()

def get_campaign(campaign_id):
    return db_get_campaign_by_id(campaign_id)