from flask import Flask, redirect, url_for, request, render_template, session
import os
from dotenv import load_dotenv
load_dotenv()

from gmail_utils import (
    apply_single_rule,
    apply_all_rules,
    get_recent_emails,
    archive_old_promotions,
    get_inbox_stats,
    delete_gmail_label,
    rename_gmail_label,
    get_gmail_service,
    create_gmail_draft
)
from ai_utils import suggest_rule_from_text, analyze_emails_for_suggestions, analyze_for_opportunities, generate_reply_draft
from database import init_db, save_user, get_user_rules, add_rule as db_add_rule, delete_rule, update_rule
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

# Background Worker to sync all users
def background_sync_worker():
    while True:
        try:
            print("DEBUG: Background Sync Worker starting...")
            # We need to get all users from Supabase and run their rules
            from database import supabase
            users = supabase.table("users").select("google_id").execute()
            for user in users.data:
                gid = user['google_id']
                print(f"DEBUG: Auto-sorting for user {gid}")
                apply_all_rules(gid)
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
# Use 127.0.0.1 consistently to match Google Console entries
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
    
    # 2. Get AI Suggestions and Opportunities (if possible)
    suggestions = []
    opportunities = []
    if creds:
        try:
            email_samples = get_recent_emails(20, google_id)
            samples_str = "\n".join(email_samples)
            suggestions = analyze_emails_for_suggestions(samples_str)
            opportunities = analyze_for_opportunities(samples_str)
        except Exception as e:
            print(f"AI Panel Error: {e}")

    return render_template("index.html", 
                           rules=rules, 
                           stats=stats,
                           suggestions=suggestions,
                           opportunities=opportunities,
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
        
    current_rules = get_user_rules(google_id)
    applied_count = 0
    for r in rules:
        db_add_rule(google_id, r['label'], r['domain'])
        apply_single_rule(r, google_id)
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
    
    # Extract email for AI context
    email_context = f"Sender: {sender}\nSubject: {subject}\nTopic: {summary}"
    
    # Generate AI draft
    reply_body = generate_reply_draft(email_context)
    
    # Create in Gmail
    draft = create_gmail_draft(google_id, sender, subject, reply_body)
    
    if draft:
        return {"status": "success", "message": "Draft created in your Gmail!"}
    else:
        return {"status": "error", "message": "Failed to create draft."}

@app.route("/sync", methods=["POST"])
def sync():
    if 'google_id' not in session:
        return {"status": "error", "message": "Not authorized"}
    result = apply_all_rules(session['google_id'])
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

    # Apply this rule immediately for this user
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
    
    # Get label name before deleting from DB
    rules = get_user_rules(google_id)
    label_to_delete = next((r['label'] for r in rules if r['id'] == rule_id), None)
    
    # Delete from Gmail
    if label_to_delete:
        delete_gmail_label(google_id, label_to_delete)
        
    # Delete from DB
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
        
    # Get old label name
    rules = get_user_rules(google_id)
    old_label = next((r['label'] for r in rules if r['id'] == rule_id), None)
    
    # Rename in Gmail
    if old_label and old_label.lower() != new_label.lower():
        rename_gmail_label(google_id, old_label, new_label)
        
    # Update DB
    update_rule(rule_id, google_id, new_label, new_reply_template)
    return {"status": "success", "message": f"Rule updated successfully. Gmail label renamed to '{new_label}'"}

# ---- OAuth routes ----

@app.route("/authorize")
def authorize():
    """
    Start the OAuth flow (no temporary extra server). We redirect the user to Google.
    Google will send the user back to /oauth2callback on THIS SAME Flask server (port 5000).
    """
    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    # Force account chooser + request offline access (refresh token)
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
    """
    Handle Google's redirect here, exchange code for tokens, then save credentials for reuse.
    """
    state = session.get("state")
    if not state:
        # if state is missing, restart auth flow cleanly
        return redirect(url_for("authorize"))

    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
    )
    flow.code_verifier = session.get("code_verifier")

    # Exchange the authorization code for tokens
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        alt_url = request.url.replace("localhost", "127.0.0.1")
        if alt_url != request.url:
            flow.fetch_token(authorization_response=alt_url)
        else:
            raise e

    creds = flow.credentials
    
    # Fetch User Profile Info
    from googleapiclient.discovery import build
    service = build('oauth2', 'v2', credentials=creds)
    user_info = service.userinfo().get().execute()
    
    google_id = user_info.get('id')
    email = user_info.get('email')
    name = user_info.get('name')
    picture = user_info.get('picture')
    
    # Save to Session (Permanent)
    session.permanent = True
    session['google_id'] = google_id
    session['user_email'] = email
    session['user_name'] = name
    session['user_picture'] = picture
    
    # Save to Database
    save_user(google_id, email, name, picture, creds.to_json())

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    # remove saved tokens so next login is fresh
    try:
        os.remove("token.json")
    except FileNotFoundError:
        pass
    # if your gmail_utils uses token.pickle, clear that too
    try:
        os.remove("token.pickle")
    except FileNotFoundError:
        pass
    session.clear()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    # Keep Flask on port 5000, and DO NOT run any other server on this port
    app.run(host="127.0.0.1", port=5000, debug=True)
