from datetime import datetime, timedelta
from models import db, ThreadSummary
from services.gmail_service import get_gmail_service, get_email_details
from services.gemini_service import summarize_thread

def get_thread_summary(google_id, thread_id, is_demo=False):
    # Check cache first
    cached = ThreadSummary.query.filter_by(thread_id=thread_id).first()
    if cached:
        # Check if < 24 hours old
        if datetime.utcnow() - cached.created_at < timedelta(hours=24):
            print(f"DEBUG: Returning cached summary for thread {thread_id}")
            return cached.summary_text

    # Cache miss or expired, fetch thread
    bodies = []
    if is_demo:
        import demo_data
        # Find email with this thread_id
        for email in demo_data.emails:
            if email["thread_id"] == thread_id:
                for msg in email.get("thread_messages", []):
                    bodies.append(f"From: {msg['sender']}\nBody: {msg['body']}")
                break
    else:
        service = get_gmail_service(google_id)
        if not service:
            return "Gmail authentication required."
        try:
            thread = service.users().threads().get(userId='me', id=thread_id).execute()
            messages = thread.get('messages', [])
            for msg in messages:
                details = get_email_details(service, msg['id'])
                if details:
                    bodies.append(f"From: {details['sender']}\nBody: {details['body']}")
        except Exception as e:
            print(f"Error fetching thread {thread_id} from Gmail: {e}")
                
    if not bodies:
        return "Could not retrieve thread messages to summarize."
        
    thread_text = "\n\n---\n\n".join(bodies)
    summary_text = summarize_thread(thread_text)
    
    # Save or update cache
    if cached:
        cached.summary_text = summary_text
        cached.created_at = datetime.utcnow()
    else:
        new_cache = ThreadSummary(
            thread_id=thread_id,
            summary_text=summary_text,
            created_at=datetime.utcnow()
        )
        db.session.add(new_cache)
        
    db.session.commit()
    return summary_text
