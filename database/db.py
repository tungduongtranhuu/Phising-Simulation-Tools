import sqlite3
import os
from datetime import datetime
from database.models import Campaigns, Users, CampaignTargets, Events

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "phishing.db")

def get_connection(): 
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)  # Timeout de 30 secondes
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
    conn.row_factory = sqlite3.Row  # Enable named column access
    return conn
###Init DB and create tables
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    #Compaign table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            campaign_created_at DATETIME,
            campaign_status TEXT NOT NULL
        )
    ''')

    #Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL UNIQUE
        )
    ''')

    # Campaign Targets table (Many-to-Many)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            UNIQUE(campaign_id, user_id),
            FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')   
    #Events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            ip TEXT NOT NULL,
            user_agent TEXT NOT NULL,
            event_timestamp DATETIME NOT NULL,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close()

###Campaign operations
def create_campaign(name):
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO campaigns (campaign_name, campaign_created_at, campaign_status)
        VALUES (?, ?, ?)
    ''', (name, created_at, "active"))
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def get_all_campaign():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM campaigns')
    rows = cursor.fetchall()

    conn.close()
    return [Campaigns(*row) for row in rows]

def get_campaign_by_id(campaign_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM campaigns WHERE campaign_id = ?', (campaign_id,))
    row = cursor.fetchone()

    conn.close()
    
    if row:
        return Campaigns(*row)
    return None


###User operations
def create_user(email): 
    conn = get_connection()
    cursor = conn.cursor()
    if get_user_by_email(email):
        conn.close()
        raise Exception("User already exists")
    cursor.execute(''' 
                   INSERT INTO users (user_email) 
                   VALUES (?) 
                   ''', (email,))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id  

def get_user_by_email(email):
    conn = get_connection() 
    cursor = conn.cursor() 
    cursor.execute(''' 
                   SELECT * FROM users 
                   WHERE user_email = ? ''', (email,)) 
    row = cursor.fetchone() 
    conn.close() 

    if row: 
        return Users(*row) 
    return None 

def get_user_by_id(user_id):
    conn = get_connection() 
    cursor = conn.cursor() 
    cursor.execute(''' 
                   SELECT * FROM users 
                   WHERE user_id = ? ''', (user_id,)) 
    row = cursor.fetchone() 
    conn.close() 

    if row: 
        return Users(*row) 
    return None 

###Campaign Targets operations
def add_user_to_campaign(campaign_id, user_id): 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(''' 
                   INSERT INTO campaign_targets (campaign_id, user_id) 
                   VALUES (?, ?) ''',
                (campaign_id, user_id))
    conn.commit()
    conn.close()


def get_users_by_campaign(campaign_id): 
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
                   SELECT u.user_id, u.user_email 
                   FROM users u 
                   JOIN campaign_targets ct ON u.user_id = ct.user_id 
                   WHERE ct.campaign_id = ?
                   ''', 
                   (campaign_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return [Users(*row) for row in rows]


###Event operations  
# =========================
# Tracking - SQL layer only
# =========================

def user_belongs_to_campaign(campaign_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 1 FROM campaign_targets
        WHERE campaign_id = ? AND user_id = ?
    ''', (campaign_id, user_id))

    result = cursor.fetchone()
    conn.close()

    return result is not None


def insert_event(campaign_id, user_id, event_type, ip, user_agent, event_timestamp):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO events
        (campaign_id, user_id, event_type, ip, user_agent, event_timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (campaign_id, user_id, event_type, ip, user_agent, event_timestamp))

    conn.commit()
    conn.close()


def get_events_by_campaign(campaign_id): 
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM events
        WHERE campaign_id = ?
    ''', (campaign_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        Events(
            row["id"],
            row["campaign_id"],
            row["user_id"],
            row["event_type"],
            row["ip"],
            row["user_agent"],
            row["event_timestamp"]
        )
        for row in rows
    ]