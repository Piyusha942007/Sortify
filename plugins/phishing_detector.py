import json
from plugins import BasePlugin
from services.gemini_service import client, types

class PhishingDetector(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "Phishing Detector"
        self.description = "Analyzes incoming email bodies and senders using Gemini AI to flag phishing risks and social engineering."

    def run(self, message_details, google_id):
        if not client:
            return None

        system_instruction = """
        Analyze the email header and content details below to check for potential Phishing, Fraud, or Social Engineering attempts.
        
        Evaluate the email and return a JSON object with:
        1. 'classification': 'Safe', 'Suspicious', or 'Phishing'.
        2. 'reason': A short one-sentence explanation of why it was classified this way.
        
        Return ONLY the raw JSON object. Do not include explanations, markdown, or code fences.
        """

        prompt = (
            f"From: {message_details.get('sender', 'Unknown')}\n"
            f"Subject: {message_details.get('subject', 'No Subject')}\n"
            f"Content:\n{message_details.get('body', '')}"
        )

        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1),
                contents=prompt
            )
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
                
            res = json.loads(text)
            classification = res.get("classification", "Safe")
            if classification in ["Suspicious", "Phishing"]:
                return {
                    "status": "warning",
                    "tag": classification.upper(),
                    "message": res.get("reason", "Detected suspicious indicators.")
                }
        except Exception as e:
            print(f"Phishing Detector Plugin Error: {e}")

        return None
