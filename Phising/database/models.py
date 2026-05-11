class Campaigns:
    def __init__(self,campaign_id, campaign_name,campaign_created_at,campaign_status):
        self.campaign_id = campaign_id
        self.campaign_name = campaign_name
        self.campaign_created_at = campaign_created_at
        self.campaign_status = campaign_status


class Users:
    def __init__(self,user_id,user_email):
        self.user_id = user_id
        self.user_email= user_email


class CampaignTargets: 
    def __init__(self,id,campaign_id,user_id): 
        self.id = id 
        self.campaign_id = campaign_id 
        self.user_id = user_id


class Events:
    def __init__(self,id,campaign_id,user_id,type,ip,user_agent,timestamp):
        self.id = id
        self.campaign_id = campaign_id
        self.user_id = user_id
        self.type = type 
        self.ip = ip
        self.user_agent = user_agent
        self.timestamp = timestamp