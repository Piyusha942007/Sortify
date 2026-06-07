from collections import defaultdict
from models import db, DismissedSuggestion
from services.gmail_service import get_gmail_service, get_email_details
import re

def get_domain_from_email(email_address):
    if not email_address:
        return None
    if "<" in email_address:
        email_address = email_address.split("<")[1].split(">")[0].strip()
    match = re.search(r"@([\w.-]+)", email_address)
    return match.group(1).lower() if match else None

def learn_rules_from_inbox(google_id, is_demo=False):
    """
    Scans the user's Gmail labels for domains that have 3+ emails manually moved to a specific user label,
    but no corresponding rule exists yet.
    """
    if is_demo:
        # Check if the stripe.com suggestion was already dismissed or already exists
        dismissed = DismissedSuggestion.query.filter_by(google_id=google_id, domain="stripe.com", suggested_label="Finance").first()
        if dismissed:
            return None
        
        # Check if rule exists
        from services.db_service import get_user_rules
        rules = get_user_rules(google_id)
        for r in rules:
            if r["domain"] == "stripe.com" and r["label"] == "Finance":
                return None
                
        return {
            "domain": "stripe.com",
            "suggested_label": "Finance",
            "confidence": 0.95,
            "sample_subjects": [
                "Your monthly invoice #10245 is ready",
                "Your monthly invoice #10244 is ready",
                "Invoice #10243 paid successfully"
            ]
        }

    service = get_gmail_service(google_id)
    if not service:
        return None

    try:
        # 1. Fetch user rules to check existing rules
        from services.db_service import get_user_rules
        existing_rules = get_user_rules(google_id)
        existing_pairs = {(r["domain"].lower(), r["label"].lower()) for r in existing_rules}

        # 2. Get list of user labels
        labels_res = service.users().labels().list(userId="me").execute()
        labels = labels_res.get("labels", [])
        user_labels = [l for l in labels if l.get("type") == "user" and not l["name"].startswith("Snoozed")]

        # 3. For each label, fetch recent messages and analyze domains
        # We group by (domain, label_name) -> list of subjects
        candidates = defaultdict(list)

        for label in user_labels:
            label_name = label["name"]
            # Fetch max 15 messages in this label to keep sync reasonable
            msg_res = service.users().messages().list(userId="me", q=f"label:\"{label_name}\"", maxResults=15).execute()
            messages = msg_res.get("messages", [])
            
            for msg in messages:
                details = get_email_details(service, msg["id"])
                if not details:
                    continue
                sender = details.get("sender")
                subject = details.get("subject", "No Subject")
                domain = get_domain_from_email(sender)
                
                if domain:
                    candidates[(domain, label_name)].append(subject)

        # 4. Filter candidates that have >= 3 messages and no rule and not dismissed
        for (domain, label_name), subjects in candidates.items():
            if len(subjects) >= 3:
                # Check if rule already exists
                if (domain.lower(), label_name.lower()) in existing_pairs:
                    continue
                
                # Check if suggestion was dismissed
                dismissed = DismissedSuggestion.query.filter_by(
                    google_id=google_id,
                    domain=domain,
                    suggested_label=label_name
                ).first()
                
                if dismissed:
                    continue

                # Return the first learned suggestion
                return {
                    "domain": domain,
                    "suggested_label": label_name,
                    "confidence": min(0.99, 0.70 + (len(subjects) * 0.05)),
                    "sample_subjects": list(set(subjects))[:3]
                }
                
    except Exception as e:
        print(f"Error in rule learning engine: {e}")
        
    return None

def dismiss_suggestion(google_id, domain, label_name):
    """Saves a dismissed suggestion to the database so we don't show it again."""
    import datetime
    dismissed = DismissedSuggestion(
        google_id=google_id,
        domain=domain,
        suggested_label=label_name,
        created_at=datetime.datetime.utcnow()
    )
    db.session.add(dismissed)
    db.session.commit()
    return True
