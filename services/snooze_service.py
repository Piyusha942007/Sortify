from datetime import datetime
from models import db, SnoozedEmail
from services.gmail_service import get_gmail_service, ensure_label_exists

def snooze_email(google_id, message_id, snooze_until, reason, is_demo=False):
    # If snooze_until is a string, parse it
    if isinstance(snooze_until, str):
        try:
            snooze_until = datetime.strptime(snooze_until, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            snooze_until = datetime.strptime(snooze_until, "%Y-%m-%dT%H:%M")
        
    # In both modes, save to DB
    snoozed = SnoozedEmail(
        google_id=google_id,
        gmail_message_id=message_id,
        snooze_until=snooze_until,
        reason=reason,
        created_at=datetime.utcnow()
    )
    db.session.add(snoozed)
    db.session.commit()
    
    if is_demo:
        # For demo mode: flag in demo_data
        import demo_data
        for email in demo_data.emails:
            if email["id"] == message_id:
                email["snoozed_until"] = snooze_until.strftime("%Y-%m-%d %H:%M:%S")
                email["reason"] = reason
        return True
    else:
        # Real mode
        service = get_gmail_service(google_id)
        if not service:
            return False
        label_id = ensure_label_exists(service, "Snoozed/Sortify")
        service.users().messages().batchModify(
            userId="me",
            body={
                "ids": [message_id],
                "addLabelIds": [label_id],
                "removeLabelIds": ["INBOX"]
            }
        ).execute()
        return True

def unsnooze_email(google_id, message_id, is_demo=False):
    # Remove from DB
    snoozed = SnoozedEmail.query.filter_by(google_id=google_id, gmail_message_id=message_id).first()
    if snoozed:
        db.session.delete(snoozed)
        db.session.commit()
        
    if is_demo:
        import demo_data
        for email in demo_data.emails:
            if email["id"] == message_id:
                email["snoozed_until"] = None
                email["reason"] = None
        return True
    else:
        service = get_gmail_service(google_id)
        if not service:
            return False
        labels = service.users().labels().list(userId="me").execute().get("labels", [])
        label_id = next((l["id"] for l in labels if l["name"].lower() == "snoozed/sortify"), None)
        remove_labels = [label_id] if label_id else []
        service.users().messages().batchModify(
            userId="me",
            body={
                "ids": [message_id],
                "addLabelIds": ["INBOX"],
                "removeLabelIds": remove_labels
            }
        ).execute()
        return True

def check_expired_snoozes(app):
    with app.app_context():
        now = datetime.utcnow()
        expired_emails = SnoozedEmail.query.filter(SnoozedEmail.snooze_until <= now).all()
        for item in expired_emails:
            print(f"DEBUG: Unsnoozing email {item.gmail_message_id} for user {item.google_id}")
            try:
                is_demo = (item.google_id == "demo_user")
                unsnooze_email(item.google_id, item.gmail_message_id, is_demo=is_demo)
                # Log action to db
                from models import ActionLog
                log_entry = ActionLog(
                    google_id=item.google_id,
                    event_type="Snooze Agent",
                    message=f"Email {item.gmail_message_id} unsnoozed successfully.",
                    timestamp=datetime.utcnow()
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception as e:
                print(f"Error checking expired snooze for {item.gmail_message_id}: {e}")
