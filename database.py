import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Initialize the Supabase client
supabase: Client = None
if url and key:
    supabase = create_client(url, key)

def init_db():
    pass

def save_user(google_id, email, name, picture, credentials_json):
    if not supabase: return
    data = {
        "google_id": google_id,
        "email": email,
        "name": name,
        "picture": picture,
        "credentials": credentials_json
    }
    supabase.table("users").upsert(data).execute()

def update_user_credentials(google_id, credentials_json):
    if not supabase: return
    supabase.table("users").update({"credentials": credentials_json}).eq("google_id", google_id).execute()

def get_user_credentials_json(google_id):
    if not supabase: return None
    response = supabase.table("users").select("credentials").eq("google_id", google_id).execute()
    if response.data:
        return response.data[0]["credentials"]
    return None

def get_user_rules(google_id):
    if not supabase: return []
    response = supabase.table("rules").select("*").eq("user_id", google_id).execute()
    return response.data if response.data else []

def add_rule(user_id, label, domain):
    if not supabase: return
    data = {
        "user_id": user_id,
        "label": label,
        "domain": domain
    }
    supabase.table("rules").insert(data).execute()

def update_rule(rule_id, user_id, new_label):
    if not supabase: return
    supabase.table("rules").update({"label": new_label}).eq("id", rule_id).eq("user_id", user_id).execute()

def delete_rule(rule_id, user_id):
    if not supabase: return
    supabase.table("rules").delete().eq("id", rule_id).eq("user_id", user_id).execute()
