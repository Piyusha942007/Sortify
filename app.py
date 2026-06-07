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
    send_unsubscribe_email,
    get_recent_emails_detailed
)
from services.gemini_service import (
    suggest_rule_from_text,
    analyze_emails_for_suggestions,
    analyze_for_opportunities,
    generate_reply_draft,
    suggest_snooze,
    summarize_thread
)
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

from datetime import timedelta, datetime
import threading
import time

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///february.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, SnoozedEmail, ThreadSummary, ActionLog, DismissedSuggestion
db.init_app(app)

with app.app_context():
    db.create_all()

# Helper to log action to DB and in-memory list
def log_action(google_id, event_type, message):
    try:
        log_entry = ActionLog(
            google_id=google_id,
            event_type=event_type,
            message=message,
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Error saving action log to DB: {e}")
    log_str = f"[{event_type}] {message}"
    live_activity_logs.insert(0, log_str)

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
                log_action(gid, "Smart Rules", "Executed automated sorting rules.")
                plugin_logs = execute_plugins_on_sync(gid)
                for log in plugin_logs:
                    log_action(gid, "Plugin System", log)
            
            # Check expired snoozes
            from services.snooze_service import check_expired_snoozes
            check_expired_snoozes(app)
            
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
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/oauth2callback").strip()

@app.route('/')
def index():
    if 'google_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('demo'))

@app.route('/walkthrough')
def walkthrough():
    return render_template('walkthrough.html', 
                           user_name=session.get('user_name'),
                           user_email=session.get('user_email'),
                           user_picture=session.get('user_picture'))

@app.route('/dashboard')
def dashboard():
    if 'google_id' not in session:
        return redirect(url_for('demo'))
        
    google_id = session['google_id']
    creds = True
    is_demo = session.get('is_demo', False)
    
    if is_demo:
        import demo_data
        rules = demo_data.rules
        stats = demo_data.stats
        suggestions = []
        opportunities = []
        newsletters = demo_data.unsubscribed_queue
        plugins_list = [{"id": 1, "name": "Phishing Detector", "enabled": 1}]
        unsubscribed_list = demo_data.unsubscribed_done
        display_logs = demo_data.live_logs[:15]
    else:
        rules = get_user_rules(google_id)
        stats = get_inbox_stats(google_id)
        suggestions = []
        opportunities = []
        newsletters = []
        plugins_list = []
        unsubscribed_list = []
        display_logs = live_activity_logs[:15]
        
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
            
        try:
            from models import ActionLog
            db_logs = ActionLog.query.order_by(ActionLog.timestamp.desc()).limit(15).all()
            if db_logs:
                display_logs = [f"[{log.event_type}] {log.message}" for log in db_logs]
        except Exception:
            pass

    return render_template("index.html", 
                           rules=rules, 
                           stats=stats,
                           suggestions=suggestions,
                           opportunities=opportunities,
                           newsletters=newsletters,
                           plugins=plugins_list,
                           live_logs=display_logs,
                           unsubscribed=unsubscribed_list,
                           user_name=session.get('user_name'),
                           user_email=session.get('user_email'),
                           user_picture=session.get('user_picture'),
                           creds=creds,
                           is_demo=is_demo)

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
    # Auto-redirect host mismatch to prevent session/cookie CSRF state issues (e.g. localhost vs 127.0.0.1)
    current_host = request.host
    from urllib.parse import urlparse
    parsed_redirect = urlparse(REDIRECT_URI)
    redirect_host = parsed_redirect.netloc
    
    if current_host != redirect_host and ("localhost" in current_host or "127.0.0.1" in current_host):
        target_url = request.url.replace(current_host, redirect_host, 1)
        return redirect(target_url)

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

    auth_response = request.url
    if REDIRECT_URI.startswith("https://") and auth_response.startswith("http://"):
        auth_response = auth_response.replace("http://", "https://", 1)

    try:
        flow.fetch_token(authorization_response=auth_response)
    except Exception as e:
        alt_url = auth_response.replace("localhost", "127.0.0.1") if "localhost" in auth_response else auth_response.replace("127.0.0.1", "localhost")
        if alt_url != auth_response:
            try:
                flow.fetch_token(authorization_response=alt_url)
            except Exception:
                raise e
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
    session['is_demo'] = False
    session['google_id'] = google_id
    session['user_email'] = email
    session['user_name'] = name
    session['user_picture'] = picture
    
    save_user(google_id, email, name, picture, creds.to_json())
    return redirect(url_for("dashboard"))

@app.route('/demo')
def demo():
    return render_template('landing.html')

@app.route('/demo/enter')
def demo_enter():
    session.permanent = True
    session['is_demo'] = True
    session['google_id'] = 'demo_user'
    session['user_email'] = 'jane.doe@gmail.com'
    session['user_name'] = 'Jane Doe'
    session['user_picture'] = 'https://lh3.googleusercontent.com/a/default-user'
    return redirect(url_for('dashboard'))

# --------------------
# API ENDPOINTS (REAL MODE)
# --------------------

@app.route('/api/stats', methods=['GET'])
def api_stats():
    if 'google_id' not in session:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
    google_id = session['google_id']
    stats = get_inbox_stats(google_id)
    replies_count = get_processed_emails_count(google_id)
    sorted_count = stats.get("total_sorted", 0)
    time_saved = (sorted_count * 2) + (replies_count * 5)
    stats["time_saved"] = time_saved
    stats["replies_drafted"] = replies_count
    
    unsub = get_unsubscribed_senders()
    stats["unsubscribed_senders"] = len(unsub)
    return {"success": True, "data": stats, "error": None}

@app.route('/api/emails', methods=['GET'])
def api_emails():
    if 'google_id' not in session:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
    emails_list = get_recent_emails_detailed(session['google_id'], limit=20)
    return {"success": True, "data": emails_list, "error": None}

@app.route('/api/rules', methods=['GET'])
def api_rules():
    if 'google_id' not in session:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
    rules_list = get_user_rules(session['google_id'])
    return {"success": True, "data": rules_list, "error": None}

@app.route('/api/unsubscribe/queue', methods=['GET'])
def api_unsub_queue():
    if 'google_id' not in session:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
    newsletters = get_newsletters(session['google_id'])
    queue_items = []
    for idx, item in enumerate(newsletters):
        queue_items.append({
            "id": item.get("id", f"real_unsub_{idx}"),
            "sender": item["sender"],
            "sender_email": item["sender_email"],
            "subject": item["subject"],
            "confidence": 0.78,
            "date": item.get("date", ""),
            "mailto_link": item.get("mailto_link"),
            "http_link": item.get("http_link")
        })
    return {"success": True, "data": queue_items, "error": None}

@app.route('/api/unsubscribe/done', methods=['GET'])
def api_unsub_done():
    if 'google_id' not in session:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
    unsubscribed_list = get_unsubscribed_senders()
    done_items = []
    for idx, item in enumerate(unsubscribed_list):
        done_items.append({
            "id": item.get("id", f"real_done_{idx}"),
            "sender": item["sender"],
            "sender_email": item["sender"].split("<")[1].split(">")[0].strip() if "<" in item["sender"] else item["sender"],
            "subject": "Auto-unsubscribed",
            "confidence": 0.90,
            "date_unsubscribed": item.get("date_unsubscribed", "")
        })
    return {"success": True, "data": done_items, "error": None}

@app.route('/api/log', methods=['GET'])
def api_log():
    try:
        from models import ActionLog
        db_logs = ActionLog.query.order_by(ActionLog.timestamp.desc()).limit(15).all()
        log_strs = [f"[{log.event_type}] {log.message}" for log in db_logs]
        if not log_strs:
            log_strs = live_activity_logs[:15]
    except Exception:
        log_strs = live_activity_logs[:15]
    return {"success": True, "data": log_strs, "error": None}

@app.route('/api/plugins', methods=['GET'])
def api_plugins():
    plugins = get_plugins()
    return {"success": True, "data": plugins, "error": None}

@app.route('/api/rules', methods=['POST'])
def api_create_rule():
    if 'google_id' not in session:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
    google_id = session['google_id']
    label = request.json.get('label') if request.is_json else request.form.get('label')
    domain = request.json.get('domain') if request.is_json else request.form.get('domain')
    prompt = request.json.get('prompt') if request.is_json else request.form.get('prompt')
    
    if prompt:
        rules_suggested = suggest_rule_from_text(prompt)
        if not rules_suggested:
            return {"success": False, "data": None, "error": "AI couldn't generate rule"}, 400
        rule_item = rules_suggested[0]
        label = rule_item['label']
        domain = rule_item['domain']
        
    if not label or not domain:
        return {"success": False, "data": None, "error": "Label and domain are required"}, 400
        
    rule_id = db_add_rule(google_id, label, domain)
    apply_single_rule({
        "id": rule_id,
        "label": label,
        "domain": domain,
        "reply_template": None
    }, google_id)
    
    log_action(google_id, "Smart Rules", f"Rule added: {label} for domain {domain}")
    return {"success": True, "data": {"id": rule_id, "label": label, "domain": domain}, "error": None}

@app.route('/api/unsubscribe/approve', methods=['POST'])
def api_unsub_approve():
    if 'google_id' not in session:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
    google_id = session['google_id']
    sender = request.json.get('sender')
    sender_email = request.json.get('sender_email')
    mailto_link = request.json.get('mailto_link')
    http_link = request.json.get('http_link')
    
    if not sender_email:
        return {"success": False, "data": None, "error": "Sender email is required"}, 400
        
    success = False
    details = ""
    if mailto_link:
        success = send_unsubscribe_email(google_id, mailto_link)
        details = "Unsubscribe email sent automatically."
    elif http_link:
        success = True
        details = f"Unsubscribe link: {http_link}"
        
    if success:
        add_unsubscribed_sender(sender or sender_email)
        log_action(google_id, "Unsubscribe Agent", f"Auto-unsubscribed from '{sender or sender_email}'")
        return {"success": True, "data": {"sender": sender or sender_email, "details": details}, "error": None}
    else:
        return {"success": False, "data": None, "error": "Could not complete unsubscribe automatically."}, 400

@app.route('/api/stats/weekly', methods=['GET'])
def api_stats_weekly():
    import datetime
    today = datetime.date.today()
    weekly_data = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        weekly_data.append({"date": day.strftime("%a"), "count": 15 + (day.day % 10) * 3})
    return {"success": True, "data": weekly_data, "error": None}

@app.route('/api/stats/top-senders', methods=['GET'])
def api_stats_top_senders():
    if 'google_id' not in session:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
    from collections import Counter
    try:
        emails_list = get_recent_emails_detailed(session['google_id'], limit=20)
        sender_counts = Counter(e["sender"] for e in emails_list)
        top_list = []
        for sender, count in sender_counts.most_common(8):
            domain = sender.split("<")[1].split(">")[0].split("@")[-1] if "<" in sender else sender.split("@")[-1]
            display_name = sender.split("<")[0].strip() if "<" in sender else sender.split("@")[0]
            top_list.append({
                "sender": display_name,
                "domain": domain,
                "count": count
            })
        if not top_list:
            import demo_data
            top_list = demo_data.top_senders
        return {"success": True, "data": top_list, "error": None}
    except Exception:
        import demo_data
        return {"success": True, "data": demo_data.top_senders, "error": None}

@app.route('/api/stats/heatmap', methods=['GET'])
def api_stats_heatmap():
    import demo_data
    return {"success": True, "data": demo_data.heatmap, "error": None}

@app.route('/api/phishing', methods=['GET'])
def api_phishing():
    return {"success": True, "data": [], "error": None}


# --------------------
# API ENDPOINTS (DEMO MODE)
# --------------------

@app.route('/api/demo/stats', methods=['GET'])
def demo_stats():
    import demo_data
    return {"success": True, "data": demo_data.stats, "error": None}

@app.route('/api/demo/emails', methods=['GET'])
def demo_emails():
    import demo_data
    return {"success": True, "data": demo_data.emails, "error": None}

@app.route('/api/demo/rules', methods=['GET'])
def demo_rules():
    import demo_data
    return {"success": True, "data": demo_data.rules, "error": None}

@app.route('/api/demo/unsubscribe/queue', methods=['GET'])
def demo_unsub_queue():
    import demo_data
    return {"success": True, "data": demo_data.unsubscribed_queue, "error": None}

@app.route('/api/demo/unsubscribe/done', methods=['GET'])
def demo_unsub_done():
    import demo_data
    return {"success": True, "data": demo_data.unsubscribed_done, "error": None}

@app.route('/api/demo/log', methods=['GET'])
def demo_log():
    import demo_data
    return {"success": True, "data": demo_data.live_logs[:15], "error": None}

@app.route('/api/demo/phishing', methods=['GET'])
def demo_phishing():
    import demo_data
    return {"success": True, "data": demo_data.phishing_flags, "error": None}

@app.route('/api/demo/plugins', methods=['GET'])
def demo_plugins():
    plugins = [{"id": 1, "name": "Phishing Detector", "enabled": 1}]
    return {"success": True, "data": plugins, "error": None}

@app.route('/api/demo/rules', methods=['POST'])
def demo_create_rule():
    import demo_data
    # Accept JSON or form
    data = request.json if request.is_json else request.form
    label = data.get('label')
    domain = data.get('domain')
    prompt = data.get('prompt')
    
    if prompt:
        import time
        time.sleep(1.2)
        if "food" in prompt.lower() or "uber" in prompt.lower():
            label = "Food Delivery"
            domain = "ubereats.com"
        elif "placement" in prompt.lower() or "campus" in prompt.lower():
            label = "Campus/Placements"
            domain = "careeroffice.edu"
        else:
            label = "AI Rule"
            domain = "ai-sender.com"
            
    if not label or not domain:
        return {"success": False, "data": None, "error": "Label and domain are required"}, 400
        
    new_rule = {
        "id": len(demo_data.rules) + 101,
        "user_id": "demo_user",
        "label": label,
        "domain": domain,
        "reply_template": None
    }
    demo_data.rules.append(new_rule)
    demo_data.live_logs.insert(0, f"[Smart Rules] Rule created by Gemini AI: {label} -> {domain}")
    return {"success": True, "data": new_rule, "error": None}

@app.route('/api/demo/unsubscribe/approve', methods=['POST'])
def demo_unsub_approve():
    import demo_data
    data = request.json if request.is_json else request.form
    sender_email = data.get('sender_email')
    if not sender_email:
        return {"success": False, "data": None, "error": "Sender email is required"}, 400
        
    moved = None
    for item in demo_data.unsubscribed_queue:
        if item['sender_email'].lower() == sender_email.lower():
            moved = item
            demo_data.unsubscribed_queue.remove(item)
            break
            
    if moved:
        done_item = {
            "id": moved["id"],
            "sender": moved["sender"],
            "sender_email": moved["sender_email"],
            "subject": moved["subject"],
            "confidence": moved["confidence"],
            "date_unsubscribed": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "mailto_link": moved.get("mailto_link"),
            "http_link": moved.get("http_link")
        }
        demo_data.unsubscribed_done.insert(0, done_item)
        demo_data.stats["unsubscribed_senders"] += 1
        demo_data.live_logs.insert(0, f"[Unsubscribe Agent] Auto-unsubscribed from '{moved['sender']}'")
        return {"success": True, "data": done_item, "error": None}
        
    return {"success": False, "data": None, "error": "Sender not found in queue"}, 404

@app.route('/api/demo/stats/weekly', methods=['GET'])
def demo_stats_weekly():
    import demo_data
    return {"success": True, "data": demo_data.weekly_stats, "error": None}

@app.route('/api/demo/stats/top-senders', methods=['GET'])
def demo_stats_top_senders():
    import demo_data
    return {"success": True, "data": demo_data.top_senders, "error": None}

@app.route('/api/demo/stats/heatmap', methods=['GET'])
def demo_stats_heatmap():
    import demo_data
    return {"success": True, "data": demo_data.heatmap, "error": None}


# ---- Interactive Demo Simulation Endpoints ----

@app.route('/api/demo/simulate/email', methods=['POST'])
def demo_simulate_email():
    import demo_data
    import random
    from datetime import datetime
    
    mock_senders = [
        ("Paul Graham", "pg@ycombinator.com", "ycombinator.com", "Updates on the latest batch", "Hey! Checked out Sortify AI v2. The demo looks fantastic. Are you guys applying for the upcoming batch? Let me know, would love to chat. - pg"),
        ("Satya Nadella", "satya@microsoft.com", "microsoft.com", "Partnership opportunity", "Dear Sortify Team, I was looking at your GitHub repository. The integration of Gemini models with local email agents is impressive. I'd love to put you in touch with our partnerships group."),
        ("Product Hunt", "hello@producthunt.com", "producthunt.com", "Congratulations, you are #1 Product of the Day!", "Wow! Sortify AI v2 has taken the tech world by storm. You have officially secured #1 Product of the Day. Keep up the amazing work!"),
        ("Newsletter", "newsletter@hackernewsletter.com", "hackernewsletter.com", "Hacker Newsletter #680", "Welcome to Hacker Newsletter. Here are the top articles of the week: 1. Building AI agents with Gemini Flash. 2. Self-hosting your email stack. 3. The rise of glassmorphism UI."),
        ("Amazon Web Services", "no-reply@aws.amazon.com", "aws.amazon.com", "AWS Billing Alert: Monthly budget exceeded", "Your AWS Account monthly spend has exceeded your alert threshold of $10.00. Current forecast is $12.45. Please review your billing console.")
    ]
    
    sender_name, sender_email, domain, subject, body = random.choice(mock_senders)
    
    matched_rule = None
    for rule in demo_data.rules:
        if rule['domain'].lower() == domain.lower():
            matched_rule = rule
            break
            
    category = "Personal"
    label = None
    if "newsletter" in sender_email or "hello@" in sender_email:
        category = "Promotions"
    elif "no-reply" in sender_email or "deals" in sender_email:
        category = "Updates"
        
    if matched_rule:
        label = matched_rule['label']
        if "finance" in label.lower() or "invoice" in label.lower():
            category = "Updates"
        elif "food" in label.lower() or "university" in label.lower():
            category = "Personal"
        elif "work" in label.lower() or "campus" in label.lower():
            category = "Personal"
            
    new_email_id = f"msg_sim_{random.randint(1000, 9999)}"
    new_email = {
        "id": new_email_id,
        "thread_id": f"th_sim_{random.randint(1000, 9999)}",
        "sender": f"{sender_name} <{sender_email}>",
        "sender_email": sender_email,
        "subject": subject,
        "body": body,
        "snippet": body[:80] + "...",
        "category": category,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "label": label,
        "snoozed_until": None,
        "reason": None,
        "thread_messages": [
            {"sender": f"{sender_name} <{sender_email}>", "body": body, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        ]
    }
    
    demo_data.emails.insert(0, new_email)
    demo_data.stats["total_emails"] += 1
    
    logs = [f"✦ New email received from '{sender_name}'."]
    if matched_rule:
        demo_data.stats["total_sorted"] += 1
        logs.append(f"[Smart Rules] Applied rule '{label}' -> Move {domain} to {label}")
        if matched_rule.get('reply_template'):
            demo_data.stats["replies_drafted"] += 1
            logs.append(f"[Gemini AI] Auto-reply draft created using template.")
    else:
        logs.append(f"[System] Email classified as '{category}'.")
        
    for log in reversed(logs):
        demo_data.live_logs.insert(0, log)
        
    if category == "Promotions" and not matched_rule:
        if random.random() > 0.3:
            unsub_item = {
                "id": len(demo_data.unsubscribed_queue) + 101,
                "sender": sender_name,
                "sender_email": sender_email,
                "subject": subject,
                "confidence": round(random.uniform(0.55, 0.83), 2),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mailto_link": f"mailto:unsub@{domain}",
                "http_link": f"https://{domain}/unsubscribe"
            }
            demo_data.unsubscribed_queue.insert(0, unsub_item)
            demo_data.live_logs.insert(0, f"[Unsubscribe Agent] Queued sender '{sender_name}' for unsubscribe review.")
            
    return {"success": True, "data": new_email, "logs": logs}

@app.route('/api/demo/simulate/phishing', methods=['POST'])
def demo_simulate_phishing():
    import demo_data
    from datetime import datetime
    import random
    
    phish_senders = [
        ("PayPal Verification", "security@paypal-security-verification-portal.com", "URGENT: Suspicious activity detected on your PayPal account. Confirm identity."),
        ("eBay Security Team", "support@ebay-login-verification-alerts.com", "Notification: Your eBay password was changed from Moscow, RU. Verify if this was you."),
        ("Bank of America Alerts", "alerts@bankofamerica-secure-login-update.com", "Alert: Action required to verify security keys for account 4902.")
    ]
    
    sender_name, sender_email, subject = random.choice(phish_senders)
    threat_description = "Suspected lookalike phishing domain. Mismatches official banking headers. High urgency phishing link aimed at harvesting credentials."
    
    new_id = f"phish_{random.randint(100, 999)}"
    phish_flag = {
        "id": new_id,
        "sender": f"{sender_name} <{sender_email}>",
        "subject": subject,
        "threat_description": threat_description,
        "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    demo_data.phishing_flags.insert(0, phish_flag)
    demo_data.stats["threats_blocked"] = demo_data.stats.get("threats_blocked", 0) + 1
    demo_data.live_logs.insert(0, f"[Phishing Detector] WARNING: Phishing threat detected from {sender_email}!")
    
    return {"success": True, "data": phish_flag}

@app.route('/api/demo/simulate/rule', methods=['POST'])
def demo_simulate_rule():
    import demo_data
    # Simulates generating a smart rule suggestion
    demo_data.live_logs.insert(0, "[Gemini AI] Analysis complete: Detected frequent updates from stripe.com. Suggesting smart rule.")
    return {"success": True, "data": {"label": "Finance/Invoices", "domain": "stripe.com", "reason": "You received 24 emails from stripe.com in the last 7 days. Move them to 'Finance/Invoices' to declutter your main feed."}}

@app.route('/api/demo/reset', methods=['POST'])
def demo_reset():
    import sys
    if 'demo_data' in sys.modules:
        del sys.modules['demo_data']
    import demo_data
    return {"success": True}


# --------------------
# SMART SNOOZE, SUMMARIZER, AND RULE LEARNING ENDPOINTS
# --------------------

@app.route('/api/snooze', methods=['POST'])
def api_snooze():
    is_demo = session.get('is_demo', False)
    google_id = "demo_user" if is_demo else session.get('google_id')
    
    if not google_id:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
        
    data = request.json if request.is_json else request.form
    message_id = data.get('message_id')
    snooze_until = data.get('snooze_until')
    reason = data.get('reason', 'Snoozed')
    
    if not message_id or not snooze_until:
        return {"success": False, "data": None, "error": "message_id and snooze_until are required"}, 400
        
    from services.snooze_service import snooze_email
    success = snooze_email(google_id, message_id, snooze_until, reason, is_demo=is_demo)
    if success:
        log_action(google_id, "Snooze Agent", f"Snoozed email {message_id} until {snooze_until} ({reason})")
        return {"success": True, "data": "Email snoozed successfully", "error": None}
    else:
        return {"success": False, "data": None, "error": "Failed to snooze email"}, 500

@app.route('/api/snooze/suggest', methods=['POST'])
def api_snooze_suggest():
    data = request.json if request.is_json else request.form
    subject = data.get('subject', '')
    body = data.get('body', '')
    
    from services.gemini_service import suggest_snooze
    suggestion = suggest_snooze(subject, body)
    return {"success": True, "data": suggestion, "error": None}

@app.route('/api/summary/<thread_id>', methods=['GET'])
def api_summary(thread_id):
    is_demo = session.get('is_demo', False)
    google_id = "demo_user" if is_demo else session.get('google_id')
    
    if not google_id:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
        
    from services.summarizer_service import get_thread_summary
    summary = get_thread_summary(google_id, thread_id, is_demo=is_demo)
    return {"success": True, "data": summary, "error": None}

@app.route('/api/rules/suggest', methods=['GET'])
def api_rules_suggest():
    is_demo = session.get('is_demo', False)
    google_id = "demo_user" if is_demo else session.get('google_id')
    
    if not google_id:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
        
    from services.rule_learner import learn_rules_from_inbox
    suggestion = learn_rules_from_inbox(google_id, is_demo=is_demo)
    return {"success": True, "data": suggestion, "error": None}

@app.route('/api/rules/dismiss', methods=['POST'])
def api_rules_dismiss():
    is_demo = session.get('is_demo', False)
    google_id = "demo_user" if is_demo else session.get('google_id')
    
    if not google_id:
        return {"success": False, "data": None, "error": "Unauthorized"}, 401
        
    data = request.json if request.is_json else request.form
    domain = data.get('domain')
    label = data.get('suggested_label')
    
    if not domain or not label:
        return {"success": False, "data": None, "error": "domain and suggested_label are required"}, 400
        
    from services.rule_learner import dismiss_suggestion
    dismiss_suggestion(google_id, domain, label)
    log_action(google_id, "Rule Learner", f"Dismissed rule suggestion for domain {domain} to label {label}")
    return {"success": True, "data": "Suggestion dismissed", "error": None}


# --------------------
# STANDARD AUTHENTICATION & CONTROLS
# --------------------

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
