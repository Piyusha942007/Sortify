# Sortify AI ✉️🤖

An intelligent, self-hosting email organizer that connects to Gmail, uses Gemini AI to analyze your inbox, and automatically categorizes incoming mail using nested labels and smart rules.

Achieve "Inbox Zen" without manual sorting. Sortify works in the background to automatically triage promotions, identify high-priority updates, create draft responses, and construct visual hierarchies with Gmail labels and sub-labels.

---

## 🌟 Key Features

- **Gmail OAuth2 Integration**: Secure multi-user login and token management.
- **Gemini AI Analysis**: Automatically inspects emails to recommend new sorting rules based on your receiving patterns.
- **Nested Labels & Sub-labels**: Supports advanced hierarchy rules (e.g., `University/Grades`, `Work/Project-A`).
- **Auto-Pilot Worker**: A background thread running every 10 minutes to auto-triage incoming emails for all authorized users.
- **Smart AI Drafts**: Generates context-aware, professional draft replies directly in your Gmail account.
- **Interactive UI**: A dashboard featuring visual analytics, active rule managers, custom rule forms, and real-time AI suggestions.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, SQLite / Supabase (for persistent user rules)
- **Frontend**: HTML5, Vanilla CSS, Vanilla JS
- **Animations**: GSAP (GreenSock Animation Platform)
- **AI Integrations**: Gemini API (`google-genai` / `google-generativeai`)
- **APIs**: Google Gmail API

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js (for frontend dependencies like GSAP)
- A Google Cloud Console project with the Gmail API enabled
- Gemini API Key from Google AI Studio

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/sortify.git
   cd sortify
   ```

2. **Set up the virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory and add the following configuration:
   ```env
   # Flask Config
   FLASK_SECRET_KEY=your_flask_secret_key
   OAUTHLIB_INSECURE_TRANSPORT=1

   # Google OAuth Credentials
   GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_PROJECT_ID=your_google_project_id
   GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/oauth2callback

   # Gemini API
   GEMINI_API_KEY=your_gemini_api_key

   # Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your web browser.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
