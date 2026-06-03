import os
import sqlite3
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Initialize the Supabase client
supabase: Client = None
if url and key:
    try:
        supabase = create_client(url, key)
    except Exception as e:
        print(f"Supabase client initialization failed: {e}")

DB_FILE = "february.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            google_id TEXT PRIMARY KEY,
            email TEXT,
            name TEXT,
            picture TEXT,
            credentials TEXT
        )
    """)
    # Create rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            label TEXT,
            domain TEXT
        )
    """)
    # Create processed_emails table to avoid duplicate drafts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            google_id TEXT,
            rule_id INTEGER
        )
    """)
    # Check if reply_template column exists in rules
    cursor.execute("PRAGMA table_info(rules)")
    columns = [col[1] for col in cursor.fetchall()]
    if "reply_template" not in columns:
        cursor.execute("ALTER TABLE rules ADD COLUMN reply_template TEXT")
    conn.commit()
    conn.close()

def save_user(google_id, email, name, picture, credentials_json):
    if supabase:
        try:
            data = {
                "google_id": google_id,
                "email": email,
                "name": name,
                "picture": picture,
                "credentials": credentials_json
            }
            supabase.table("users").upsert(data).execute()
        except Exception as e:
            print(f"Supabase save_user failed, falling back to SQLite: {e}")
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (google_id, email, name, picture, credentials)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(google_id) DO UPDATE SET
            email=excluded.email,
            name=excluded.name,
            picture=excluded.picture,
            credentials=excluded.credentials
    """, (google_id, email, name, picture, credentials_json))
    conn.commit()
    conn.close()

def update_user_credentials(google_id, credentials_json):
    if supabase:
        try:
            supabase.table("users").update({"credentials": credentials_json}).eq("google_id", google_id).execute()
        except Exception as e:
            print(f"Supabase update_user_credentials failed, falling back to SQLite: {e}")
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET credentials = ? WHERE google_id = ?", (credentials_json, google_id))
    conn.commit()
    conn.close()

def get_user_credentials_json(google_id):
    if supabase:
        try:
            response = supabase.table("users").select("credentials").eq("google_id", google_id).execute()
            if response.data:
                return response.data[0]["credentials"]
        except Exception as e:
            print(f"Supabase get_user_credentials failed, falling back to SQLite: {e}")
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT credentials FROM users WHERE google_id = ?", (google_id,))
    row = cursor.fetchone()
    conn.close()
    return row["credentials"] if row else None

def get_user_rules(google_id):
    if supabase:
        try:
            response = supabase.table("rules").select("*").eq("user_id", google_id).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Supabase get_user_rules failed, falling back to SQLite: {e}")
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rules WHERE user_id = ?", (google_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_rule(user_id, label, domain, reply_template=None):
    rule_id = None
    if supabase:
        try:
            data = {
                "user_id": user_id,
                "label": label,
                "domain": domain
            }
            res = supabase.table("rules").insert(data).execute()
            if res.data:
                rule_id = res.data[0].get("id")
        except Exception as e:
            print(f"Supabase add_rule failed, falling back to SQLite: {e}")
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rules (user_id, label, domain, reply_template)
        VALUES (?, ?, ?, ?)
    """, (user_id, label, domain, reply_template))
    if not rule_id:
        rule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rule_id

def update_rule(rule_id, user_id, new_label, reply_template=None):
    if supabase:
        try:
            supabase.table("rules").update({"label": new_label}).eq("id", rule_id).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"Supabase update_rule failed, falling back to SQLite: {e}")
            
    conn = get_db_connection()
    cursor = conn.cursor()
    if reply_template is not None:
        cursor.execute("UPDATE rules SET label = ?, reply_template = ? WHERE id = ? AND user_id = ?", (new_label, reply_template, rule_id, user_id))
    else:
        cursor.execute("UPDATE rules SET label = ? WHERE id = ? AND user_id = ?", (new_label, rule_id, user_id))
    conn.commit()
    conn.close()

def delete_rule(rule_id, user_id):
    if supabase:
        try:
            supabase.table("rules").delete().eq("id", rule_id).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"Supabase delete_rule failed, falling back to SQLite: {e}")
            
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rules WHERE id = ? AND user_id = ?", (rule_id, user_id))
    conn.commit()
    conn.close()

def is_email_processed(message_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def mark_email_processed(message_id, google_id, rule_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO processed_emails (message_id, google_id, rule_id) VALUES (?, ?, ?)", (message_id, google_id, rule_id))
        conn.commit()
    except Exception as e:
        print(f"Error marking email processed: {e}")
    finally:
        conn.close()
