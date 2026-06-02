import os
import json
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from database import get_user_credentials_json, update_user_credentials

# --------------------
# CREDENTIAL HANDLING
# --------------------

def get_user_credentials(google_id):
    creds_json_str = get_user_credentials_json(google_id)
    if not creds_json_str:
        return None
    
    try:
        creds_json = json.loads(creds_json_str)
        creds = Credentials.from_authorized_user_info(creds_json)
    except Exception as e:
        print(f"Error parsing credentials: {e}")
        return None
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Update Supabase with new tokens
        update_user_credentials(google_id, creds.to_json())
        
    return creds

# --------------------
# GMAIL ACTIONS
# --------------------

def get_gmail_service(google_id):
    creds = get_user_credentials(google_id)
    if not creds:
        return None
    return build("gmail", "v1", credentials=creds)

def ensure_label_exists(service, label_name):
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for l in labels:
        if l["name"].lower() == label_name.lower():
            return l["id"]
    # if not found, create
    label = service.users().labels().create(
        userId="me", body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    ).execute()
    return label["id"]

def apply_single_rule(rule, google_id):
    service = get_gmail_service(google_id)
    if not service:
        return "Not authorized"

    label_id = ensure_label_exists(service, rule["label"])
    query = f"from:{rule['domain']}"
    
    messages = []
    next_page_token = None
    while True:
        results = service.users().messages().list(userId="me", q=query, pageToken=next_page_token).execute()
        messages.extend(results.get("messages", []))
        next_page_token = results.get("nextPageToken")
        if not next_page_token: break

    if not messages:
        return f"No emails matched rule {rule}"

    batch_size = 50
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i+batch_size]
        ids = [msg["id"] for msg in batch]
        service.users().messages().batchModify(
            userId="me",
            body={"ids": ids, "addLabelIds": [label_id]}
        ).execute()

    return f"Applied rule {rule['label']} → {rule['domain']} to {len(messages)} emails"

def apply_all_rules(google_id):
    from database import get_user_rules
    rules = get_user_rules(google_id)
    results = []
    for rule in rules:
        results.append(apply_single_rule(rule, google_id))
    return "<br>".join(results)

def get_recent_emails(limit=20, google_id=None):
    if not google_id: return []
    service = get_gmail_service(google_id)
    if not service: return []
    
    results = service.users().messages().list(userId="me", maxResults=limit).execute()
    messages = results.get("messages", [])
    
    email_data = []
    for msg in messages:
        m = service.users().messages().get(userId="me", id=msg["id"], format="metadata", metadataHeaders=["Subject", "From"]).execute()
        headers = m.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        email_data.append(f"From: {sender} | Subject: {subject}")
    return email_data

def get_inbox_stats(google_id):
    service = get_gmail_service(google_id)
    if not service: return {}
    categories = {
        "Personal": "NOT category:promotions AND NOT category:social AND NOT category:updates",
        "Promotions": "category:promotions",
        "Social": "category:social",
        "Updates": "category:updates"
    }
    stats = {}
    total_emails = 0
    for name, query in categories.items():
        results = service.users().messages().list(userId="me", q=query, maxResults=1).execute()
        count = results.get("resultSizeEstimate", 0)
        stats[name] = count
        total_emails += count
    sorted_count = total_emails - stats.get("Personal", 0)
    return {"composition": stats, "total_sorted": sorted_count, "total_emails": total_emails}

def delete_gmail_label(google_id, label_name):
    service = get_gmail_service(google_id)
    if not service: return False
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for l in labels:
        if l["name"].lower() == label_name.lower():
            service.users().labels().delete(userId="me", id=l["id"]).execute()
            return True
    return False

def rename_gmail_label(google_id, old_name, new_name):
    service = get_gmail_service(google_id)
    if not service: return False
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for l in labels:
        if l["name"].lower() == old_name.lower():
            service.users().labels().patch(userId="me", id=l["id"], body={"name": new_name}).execute()
            return True
    return False

def create_gmail_draft(google_id, to_email, subject, body):
    service = get_gmail_service(google_id)
    if not service: return None
    message = EmailMessage()
    message.set_content(body)
    message['To'] = to_email
    message['Subject'] = f"Re: {subject}"
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {'message': {'raw': encoded_message}}
    draft = service.users().drafts().create(userId='me', body=create_message).execute()
    return draft

def archive_old_promotions(google_id):
    service = get_gmail_service(google_id)
    if not service: return "Error"
    query = "category:promotions older_than:30d"
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    if not messages: return "Clean!"
    ids = [msg["id"] for msg in messages]
    service.users().messages().batchModify(userId="me", body={"ids": ids, "removeLabelIds": ["INBOX"]}).execute()
    return f"Archived {len(messages)} emails"
