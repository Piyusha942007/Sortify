import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize the Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

def suggest_rule_from_text(prompt):
    """Generates a list of {label, domain} rules from a natural language prompt."""
    if not client:
        return []

    model_name = "gemini-flash-latest"
    system_instruction = """
    You are an expert Gmail organizer. Convert the user's request into a JSON list of objects.
    Each object must have:
    1. 'label': A short, clear folder name.
    2. 'domain': The primary email domain (e.g., 'amazon.com').
    
    Example output: [{"label": "Travel", "domain": "expedia.com"}, {"label": "Shopping", "domain": "amazon.com"}]
    
    Return ONLY the raw JSON list. No markdown, no explanation.
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            ),
            contents=prompt
        )
        
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        print(f"DEBUG: AI Rule Gen failed with {model_name}: {str(e)}")
        return []

def analyze_emails_for_suggestions(email_samples):
    """Analyzes a list of emails and suggests 3 organization rules."""
    if not client or not email_samples:
        return []

    model_name = "gemini-flash-latest"
    system_instruction = """
    Analyze these recent emails and suggest 3 high-impact organization rules.
    Return a JSON list of objects, each with:
    1. 'label': Recommended label name.
    2. 'domain': The domain to filter.
    3. 'reason': A one-sentence explanation of why this is a good idea.
    
    Return ONLY the raw JSON list. No markdown.
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            ),
            contents=f"Recent Emails:\n{email_samples}"
        )
        
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        print(f"DEBUG: AI Suggestion failed with {model_name}: {str(e)}")
        return []

def analyze_for_opportunities(email_samples):
    """Detects high-value emails (selections, congratulations, action required)."""
    if not client or not email_samples:
        return []

    model_name = "gemini-flash-latest"
    system_instruction = """
    Analyze these emails and find ONLY the ones that are 'Opportunities' 
    (Job offers, interview invites, contest wins, or urgent selection news).
    
    Return a JSON list of objects, each with:
    1. 'id': The email ID (if available, else just a placeholder).
    2. 'sender': Who sent it.
    3. 'subject': The subject line.
    4. 'urgency': 'High', 'Medium', or 'Low'.
    5. 'summary': A 5-word summary of the opportunity.
    
    If none are found, return []. Return ONLY raw JSON.
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            ),
            contents=f"Emails:\n{email_samples}"
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        print(f"DEBUG: Opportunity detection failed: {str(e)}")
        return []

def generate_reply_draft(email_content, system_instruction=None):
    """Generates a professional reply to an email with optional custom guidelines."""
    if not client:
        return "I am interested in this opportunity. Let's discuss further."

    if not system_instruction:
        system_instruction = """
        Write a professional, enthusiastic, and concise reply to the following email.
        Maintain a helpful and polite tone. 
        Return ONLY the body text of the reply. No subject line.
        """
    
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(system_instruction=system_instruction),
            contents=email_content
        )
        return response.text.strip()
    except Exception as e:
        print(f"DEBUG: generate_reply_draft failed: {e}")
        return "Thank you for the update. I am excited to move forward with this opportunity."

def find_unsubscribe_link_in_body(body_text):
    """Uses Gemini to find any unsubscribe URL in the email body if no header exists."""
    if not client or not body_text:
        return None
        
    system_instruction = """
    Analyze the email body text and locate the absolute URL link for unsubscribing or managing subscription preferences.
    If multiple links are present, return the most direct unsubscribe link.
    Return ONLY the raw absolute URL string. If no unsubscribe link is found, return the word "None".
    Do not include markdown or explanations.
    """
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1),
            contents=body_text[:4000]
        )
        url = response.text.strip()
        return url if url.lower() != "none" and url.startswith("http") else None
    except Exception as e:
        print(f"DEBUG: find_unsubscribe_link_in_body failed: {e}")
        return None

def suggest_snooze(subject, body):
    """Suggests a snooze date/time and reason based on subject and body snippet."""
    if not client:
        import datetime
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        return {
            "suggested_time": tomorrow.strftime("%Y-%m-%d 09:00:00"),
            "reason": "Snooze until tomorrow morning - standard snooze fallback."
        }
    
    system_instruction = """
    You are an AI assistant helping a user manage their email inbox by suggesting when to snooze an email.
    Analyze the email subject and body snippet.
    Suggest a realistic date and time to snooze until (e.g., if it's a weekly newsletter, snooze until next Monday morning; if it's a weekend meetup, snooze until Friday afternoon; if it's a bill due in a week, snooze until 2 days before the due date).
    Also provide a short, clear one-sentence reason for this suggestion.
    
    You MUST output a valid JSON object matching the following structure:
    {
      "suggested_time": "YYYY-MM-DD HH:MM:SS",
      "reason": "Snooze until Monday 9am — this looks like a weekly digest"
    }
    
    Ensure suggested_time is formatted as YYYY-MM-DD HH:MM:SS. The current year is 2026. Make sure the date is in the future.
    Return ONLY raw JSON, no markdown, no comments.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            ),
            contents=f"Subject: {subject}\nBody Snippet: {body}"
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        print(f"DEBUG: suggest_snooze failed: {e}")
        import datetime
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        return {
            "suggested_time": tomorrow.strftime("%Y-%m-%d 09:00:00"),
            "reason": "Snooze until tomorrow 9am — fallback suggestion."
        }

def summarize_thread(thread_text):
    """Summarizes a concatenated email thread in 3 bullet points using Gemini."""
    if not client:
        return "• Main Topic: Discussion about the project status.\n• Action Items: Review draft layout files.\n• Status: Ongoing coordination."
        
    system_instruction = """
    Summarize this email thread in 3 bullet points. Be concise. Identify: main topic, any action items, and the current status/resolution if any.
    Return ONLY the bulleted list. Do not include markdown code block formatting or introductory text.
    """
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            ),
            contents=thread_text
        )
        return response.text.strip()
    except Exception as e:
        print(f"DEBUG: summarize_thread failed: {e}")
        return "• Main Topic: Discussion thread details.\n• Action Items: Action required by recipient.\n• Status: Awaiting response."

