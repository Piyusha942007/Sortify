from flask import Flask, redirect, url_for, request, render_template, session
import os
from dotenv import load_dotenv
load_dotenv()

from services.gmail_service import (
    apply_single_rule,
    apply_all_rules,
    get_recent_emails,
    archive_old_promotions,
    get_inbox_stats,
    delete_gmail_label,
    rename_gmail_label,
    get_gmail_service,
    create_gmail_draft,
    get_email_details,
    get_newsletters,
    send_unsubscribe_email
)
from services.gemini_service import suggest_rule_from_text, analyze_emails_for_suggestions, analyze_for_opportunities, generate_reply_draft
from services.db_service import (
    init_db,
    save_user,
    get_user_rules,
    add_rule as db_add_rule,
    delete_rule,
    update_rule,
    get_plugins,
    set_plugin_enabled,
    is_plugin_enabled,
    add_unsubscribed_sender,
    get_unsubscribed_senders,
    get_processed_emails_count,
    supabase
)
from plugins.phishing_detector import PhishingDetector
import json

init_db()

# KEEP InstalledAppFlow import for compatibility (not used after the fix)
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.oauth2.credentials import Credentials

from datetime import timedelta
import threading
import time

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# In-memory Plugin sync log feed
live_activity_logs = [
    "System initialized with SQLite fallback handler.",
    "Inbox scanning engines ready."
]

plugin_registry = [
    PhishingDetector()
]

def execute_plugins_on_sync(google_id):
    active_plugins = [p for p in plugin_registry if is_plugin_enabled(p.name)]
    if not active_plugins:
        return []
        
    print(f"DEBUG: Running {len(active_plugins)} active plugins for user {google_id}...")
    service = get_gmail_service(google_id)
    if not service:
        return []
        
    logs = []
    try:
        results = service.users().messages().list(userId="me", maxResults=5).execute()
        messages = results.get("messages", [])
        for msg in messages:
            details = get_email_details(service, msg["id"])
            if details:
                for plugin in active_plugins:
                    res = plugin.run(details, google_id)
                    if res:
                        log_str = f"[{plugin.name}] Email from '{details['sender'][:30]}' flagged: {res['tag']} — {res['message']}"
                        logs.append(log_str)
    except Exception as e:
        print(f"Error running plugins: {e}")
        
    return logs

# Background Worker to sync all users
def background_sync_worker():
    while True:
        try:
            print("DEBUG: Background Sync Worker starting...")
            from services.db_service import supabase
            users_list = []
            if supabase:
                try:
                    users = supabase.table("users").select("google_id").execute()
                    users_list = [u['google_id'] for u in users.data]
                except Exception as e:
                    print(f"Supabase fetch users failed: {e}")
            
            # SQLite fallback
            if not users_list:
                import sqlite3
                conn = sqlite3.connect("february.db")
                cursor = conn.cursor()
                cursor.execute("SELECT google_id FROM users")
                users_list = [row[0] for row in cursor.fetchall()]
                conn.close()

            for gid in users_list:
                print(f"DEBUG: Auto-sorting for user {gid}")
                apply_all_rules(gid)
                plugin_logs = execute_plugins_on_sync(gid)
                for log in plugin_logs:
                    live_activity_logs.insert(0, log)
            print("DEBUG: Background Sync completed. Sleeping for 10 minutes.")
        except Exception as e:
            print(f"DEBUG: Background Sync Error: {e}")
        time.sleep(600) # Sync every 10 minutes

# Start the worker thread
threading.Thread(target=background_sync_worker, daemon=True).start()

# allow plain HTTP for local dev
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = os.getenv("OAUTHLIB_INSECURE_TRANSPORT", "1")
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

def get_google_client_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    print(f"DEBUG: Loading Client ID: {client_id}")
    return {
        "web": {
            "client_id": client_id.strip() if client_id else None,
            "project_id": os.getenv("GOOGLE_PROJECT_ID", "").strip(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
            "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/oauth2callback").strip()]
        }
    }

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]
REDIRECT_URI = "http://127.0.0.1:5000/oauth2callback"

@app.route('/')
def walkthrough():
    return render_template('walkthrough.html', 
                           user_name=session.get('user_name'),
                           user_email=session.get('user_email'),
                           user_picture=session.get('user_picture'))

@app.route('/dashboard')
def dashboard():
    if 'google_id' not in session:
        return redirect(url_for('walkthrough'))
        
    google_id = session['google_id']
    creds = True
    
    rules = get_user_rules(google_id)
    stats = get_inbox_stats(google_id)
    
    suggestions = []
    opportunities = []
    newsletters = []
    plugins_list = []
    unsubscribed_list = []
    
    if creds:
        try:
            email_samples = get_recent_emails(20, google_id)
            samples_str = "\n".join(email_samples)
            suggestions = analyze_emails_for_suggestions(samples_str)
            opportunities = analyze_for_opportunities(samples_str)
            
            newsletters = get_newsletters(google_id)
            plugins_list = get_plugins()
            unsubscribed_list = get_unsubscribed_senders()
            
            replies_count = get_processed_emails_count(google_id)
            sorted_count = stats.get("total_sorted", 0)
            time_saved = (sorted_count * 2) + (replies_count * 5)
            stats["time_saved"] = time_saved
            stats["replies_drafted"] = replies_count
        except Exception as e:
            print(f"Dashboard Panel Error: {e}")

    return render_template("index.html", 
                           rules=rules, 
                           stats=stats,
                           suggestions=suggestions,
                           opportunities=opportunities,
                           newsletters=newsletters,
                           plugins=plugins_list,
                           live_logs=live_activity_logs[:15],
                           unsubscribed=unsubscribed_list,
                           user_name=session.get('user_name'),
                           user_email=session.get('user_email'),
                           user_picture=session.get('user_picture'),
                           creds=creds)

@app.route("/cleanup", methods=["POST"])
def cleanup():
    if 'google_id' not in session:
        return redirect(url_for('authorize'))
    result = archive_old_promotions(session['google_id'])
    return redirect(url_for("dashboard", msg=result))

@app.route("/ai_rule", methods=["POST"])
def ai_rule():
    if 'google_id' not in session:
        return redirect(url_for('authorize'))
    google_id = session['google_id']
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        return redirect(url_for("dashboard", msg="Please enter a prompt."))
        
    rules = suggest_rule_from_text(prompt)
    if not rules:
        return redirect(url_for("dashboard", msg="AI couldn't generate rules for that prompt."))
        
    applied_count = 0
    for r in rules:
        rule_id = db_add_rule(google_id, r['label'], r['domain'])
        apply_single_rule({
            "id": rule_id,
            "label": r['label'],
            "domain": r['domain'],
            "reply_template": None
        }, google_id)
        applied_count += 1
        
    return redirect(url_for("dashboard", msg=f"AI added and applied {applied_count} new rules!"))

@app.route("/draft_reply", methods=["POST"])
def draft_reply():
    if 'google_id' not in session:
        return {"status": "error", "message": "Not authorized"}, 401
    
    google_id = session['google_id']
    sender = request.form.get("sender")
    subject = request.form.get("subject")
    summary = request.form.get("summary")
    
    email_context = f"Sender: {sender}\nSubject: {subject}\nTopic: {summary}"
    reply_body = generate_reply_draft(email_context)
    draft = create_gmail_draft(google_id, sender, subject, reply_body)
    
    if draft:
        return {"status": "success", "message": "Draft created in your Gmail!"}
    else:
        return {"status": "error", "message": "Failed to create draft."}

@app.route("/sync", methods=["POST"])
def sync():
    if 'google_id' not in session:
        return {"status": "error", "message": "Not authorized"}
    google_id = session['google_id']
    result = apply_all_rules(google_id)
    
    # Run active plugins and log outcomes
    plugin_logs = execute_plugins_on_sync(google_id)
    for log in plugin_logs:
        live_activity_logs.insert(0, log)
        
    return {"status": "success", "result": result}

@app.route("/add_rule", methods=["POST"])
def add_rule():
    if 'google_id' not in session:
        return redirect(url_for('authorize'))
        
    label = request.form.get("label", "").strip()
    domain = request.form.get("domain", "").strip()
    reply_template = request.form.get("reply_template", "").strip() or None
    
    if not label or not domain:
        return redirect(url_for("dashboard", msg="Please fill all fields."))

    google_id = session['google_id']
    rule_id = db_add_rule(google_id, label, domain, reply_template)

    result = apply_single_rule({
        "id": rule_id,
        "label": label,
        "domain": domain,
        "reply_template": reply_template
    }, google_id=google_id)
    return {"status": "success", "message": result, "label": label, "domain": domain}

@app.route("/delete_rule/<int:rule_id>", methods=["POST"])
def delete_rule_route(rule_id):
    if 'google_id' not in session:
        return {"status": "error", "message": "Not authorized"}, 401
    
    google_id = session['google_id']
    rules = get_user_rules(google_id)
    label_to_delete = next((r['label'] for r in rules if r['id'] == rule_id), None)
    
    if label_to_delete:
        delete_gmail_label(google_id, label_to_delete)
        
    delete_rule(rule_id, google_id)
    return {"status": "success", "message": "Rule and Gmail label removed."}

@app.route("/edit_rule/<int:rule_id>", methods=["POST"])
def edit_rule_route(rule_id):
    if 'google_id' not in session:
        return {"status": "error", "message": "Not authorized"}, 401
    
    google_id = session['google_id']
    new_label = request.form.get("label", "").strip()
    new_reply_template = request.form.get("reply_template", "").strip() or None
    
    if not new_label:
        return {"status": "error", "message": "Label cannot be empty."}, 400
        
    rules = get_user_rules(google_id)
    old_label = next((r['label'] for r in rules if r['id'] == rule_id), None)
    
    if old_label and old_label.lower() != new_label.lower():
        rename_gmail_label(google_id, old_label, new_label)
        
    update_rule(rule_id, google_id, new_label, new_reply_template)
    return {"status": "success", "message": f"Rule updated successfully. Gmail label renamed to '{new_label}'"}

# ---- Hackathon Unsubscribe Agent Route ----
@app.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    if 'google_id' not in session:
        return {"status": "error", "message": "Not authorized"}, 401
        
    google_id = session['google_id']
    sender = request.form.get("sender")
    mailto_link = request.form.get("mailto_link")
    http_link = request.form.get("http_link")
    
    if not sender:
        return {"status": "error", "message": "Sender info missing"}, 400
        
    success = False
    details = ""
    if mailto_link:
        success = send_unsubscribe_email(google_id, mailto_link)
        details = "Unsubscribe email sent automatically."
    elif http_link:
        success = True
        details = f"Unsubscribe link: {http_link}"
        
    if success:
        add_unsubscribed_sender(sender)
        live_activity_logs.insert(0, f"[Unsubscribe Agent] Auto-unsubscribed from '{sender}'")
        return {"status": "success", "message": f"Successfully processed unsubscribe for {sender}. {details}"}
    else:
        return {"status": "error", "message": "Could not complete unsubscribe automatically."}

# ---- Hackathon Plugin Management Route ----
@app.route("/toggle_plugin", methods=["POST"])
def toggle_plugin():
    if 'google_id' not in session:
        return {"status": "error", "message": "Not authorized"}, 401
        
    plugin_name = request.form.get("plugin_name")
    enabled = request.form.get("enabled") == "1"
    
    if not plugin_name:
        return {"status": "error", "message": "Plugin name missing"}, 400
        
    set_plugin_enabled(plugin_name, enabled)
    status_str = "enabled" if enabled else "disabled"
    live_activity_logs.insert(0, f"[Plugin Manager] Plugin '{plugin_name}' has been {status_str}.")
    return {"status": "success", "message": f"Plugin '{plugin_name}' is now {status_str}."}

# ---- OAuth routes ----
@app.route("/authorize")
def authorize():
    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    session["state"] = state
    session["code_verifier"] = flow.code_verifier
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    state = session.get("state")
    if not state:
        return redirect(url_for("authorize"))

    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
    )
    flow.code_verifier = session.get("code_verifier")

    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        alt_url = request.url.replace("localhost", "127.0.0.1")
        if alt_url != request.url:
            flow.fetch_token(authorization_response=alt_url)
        else:
            raise e

    creds = flow.credentials
    from googleapiclient.discovery import build
    service = build('oauth2', 'v2', credentials=creds)
    user_info = service.userinfo().get().execute()
    
    google_id = user_info.get('id')
    email = user_info.get('email')
    name = user_info.get('name')
    picture = user_info.get('picture')
    
    session.permanent = True
    session['google_id'] = google_id
    session['user_email'] = email
    session['user_name'] = name
    session['user_picture'] = picture
    
    save_user(google_id, email, name, picture, creds.to_json())
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    try:
        os.remove("token.json")
    except FileNotFoundError:
        pass
    try:
        os.remove("token.pickle")
    except FileNotFoundError:
        pass
    session.clear()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
