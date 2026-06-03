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
