# ✉️ Sortify AI — Your Inbox. Finally Under Control.

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-6366f1.svg?style=flat-square)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Gemini](https://img.shields.io/badge/gemini-ai-%238b5cf6.svg?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://opensource.org/licenses/MIT)

An open-source, AI-powered Gmail inbox command center that auto-triages, categorizes, drafts smart replies, and unsubscribes newsletters using Gemini AI. Built with Flask, SQLite, and Vanilla HTML/CSS/JS + GSAP.

---

## 📌 GitHub Repository Details (For "About" Section)

If you are setting up your GitHub repository, here is a polished description and a set of tags to use:

* **Description**: `✉️ AI-powered Gmail inbox command center that auto-triages, categorizes, drafts smart replies, and unsubscribes newsletters using Gemini AI. Built with Flask, SQLite, and Vanilla HTML/CSS/JS + GSAP.`
* **Topics/Tags**: `gmail-api`, `gemini-api`, `flask-app`, `email-triage`, `pwa`, `gsap-animation`, `dark-mode`, `sqlite`, `developer-tools`, `ai-agents`

---

## 🌟 Key Features

* **✨ Zero-Auth Sandbox Mode**: Explore the full capability of Sortify AI (metrics dashboard, smart rules, templates, sandbox controls, and mock data) immediately without configuring or sharing any real Gmail credentials.
* **🕰️ Smart Snooze**: Snooze emails out of sight. Powered by Gemini, the system inspects the email body to suggest optimal snooze times (e.g. matching an event date or deadline) and auto-unsnoozes them in the background.
* **📑 Conversational Thread Summarizer**: Condense long email threads into clean, actionable bullet points, with summaries cached locally for high performance.
* **📈 Inbox Intelligence Center**:
  * **Weekly Volume Chart**: Interactive multi-series bar chart tracking email ingestion.
  * **Top Senders Widget**: Pinpoints high-frequency senders and allows one-click rule creation.
  * **Peak Heatmap Grid**: A 7×24 grid visualizing hourly and daily email density patterns.
* **🧠 Rule Learning Engine**: A background analyzer that detects manual movement patterns (e.g., sorting multiple emails from a sender into a custom label) and automatically prompts active rules.
* **🔒 Security Center & Phishing Shield**: Automatically runs security analyses on incoming mail, quarantines threats, and highlights warning indicators.
* **📱 Progressive Web App (PWA)**: Full support with standalone windows, customized launch branding, and service-worker caching for high-speed offline capabilities.
* **🤖 Auto-Pilot Service**: Background worker thread dynamically checks new messages, applies active rules, updates snoozes, and drafts Gemini replies.

---

## 🏗️ Architecture

```
                  ┌─────────────────────────────────────┐
                  │          Sortify AI Web UI          │
                  │   (HTML/CSS/JS + GSAP Animations)   │
                  │      (PWA Offline Mode / sw.js)     │
                  └──────────┬───────────────┬──────────┘
                             │               │
                    Real API │               │ Sandbox Mode
                     Calls   ▼               ▼ (Zero Auth)
                  ┌──────────┴───────────────┴──────────┐
                  │            Flask Backend            │
                  │              (app.py)               │
                  └──────────┬───────────────┬──────────┘
                             │               │
                             ▼               ▼
                ┌────────────────────┐   ┌──────────────────────┐
                │  Service Layers &  │   │  In-Memory Mock Data │
                │   Gemini Client    │   │    (demo_data.py)    │
                └────────┬───────────┘   └──────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
 │  Gmail API  │  │ Gemini API  │  │ SQLite DB   │
 │ (Auto Sync) │  │ (LLM Core)  │  │ (february)  │
 └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 📁 Repository Directory Structure

```
Sortify/
├── app.py                  # Core Flask Application & API Endpoints
├── demo_data.py            # Sandbox Mode mock data & email simulator
├── models.py               # Database schemas (Snooze, ActionLogs, Rules)
├── scanner.py              # Background mail sync & automation engine
├── services/
│   └── snooze_service.py   # AI Smart Snooze calculations & expiries
├── static/
│   ├── css/
│   │   ├── design-system.css # Global style tokens (colors, variables)
│   │   ├── styles.css        # Main Command Center UI styles
│   │   └── walkthrough.css   # Onboarding tour stylesheet
│   ├── js/
│   │   └── animations.js     # GSAP page transitions and particle effects
│   ├── images/
│   │   └── favicon.svg       # Brand favicon
│   └── manifest.json       # PWA Manifest settings
├── templates/
│   ├── base.html           # Base layout template
│   ├── landing.html        # Premium responsive landing page
│   ├── index.html          # Modular Command Center Dashboard
│   └── walkthrough.html    # Guided tour layout
├── tests/                  # Pytest backend test suite
└── Dockerfile              # Standard Docker deployment configuration
```

---

## 🚀 Getting Started

### Prerequisites
* **Python**: `3.10` or `3.11` (highly recommended)
* **Google Cloud Console Project**: Gmail API enabled with OAuth Web App client credentials (for Real Mode connection)
* **Gemini API Key**: From Google AI Studio (for AI triage, summarization, and drafts)

---

### Local Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Piyusha942007/Sortify.git
   cd Sortify
   ```

2. **Set up Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Setup Environment Configuration**
   Copy the template environment file:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and insert your API keys:
   ```env
   # Flask Config
   FLASK_SECRET_KEY=secure-random-key
   OAUTHLIB_INSECURE_TRANSPORT=1 # Set to 0 in HTTPS production

   # Gemini API Key
   GEMINI_API_KEY=your-gemini-key

   # Google Client Credentials
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_PROJECT_ID=your-project-id
   GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/oauth2callback
   ```

5. **Start the Platform**
   ```bash
   python app.py
   ```
   * Open `http://127.0.0.1:5000` to access the Landing Page.
   * Click **Launch Demo Sandbox** to explore immediately without credentials!

---

## 🐳 Docker Deployment

The application is fully containerized. To spin up using Docker Compose:

1. Configure your `.env` variables as outlined above.
2. Build and run:
   ```bash
   docker-compose up --build -d
   ```
3. Visit `http://localhost:5000` on your host. The database is persistent and binds to `february.db` in your local directory.

---

## 🧪 Testing

The codebase includes a comprehensive backend validation suite. Run all tests locally:
```bash
python -m pytest tests/ -v
```

---

## 🤝 Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Please read our [Contributor Guide](docs/CONTRIBUTING.md) to get started on pull requests, database schema changes, and plugin additions.

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
