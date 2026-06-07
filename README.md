# Sortify AI v2 ✉️🤖

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open-source, AI-powered email organizer that connects to Gmail, uses Gemini AI to analyze your inbox, and automatically categorizes incoming mail using nested labels and smart rules.

Sortify AI v2 introduces a self-contained **Demo Mode** for zero-auth evaluation, along with advanced email triage tools like **Smart Snooze**, **Thread Summarizer**, **Inbox Intelligence**, and a **Rule Learning Engine**.

---

## 🌟 Key Features

* **Zero-Auth Demo Mode**: Instantly experience the full features of Sortify AI (including analytics, rules, snoozing, and plugins) without connecting a Google account. Navigate to `/demo` to start.
* **Smart Snooze**: Snooze emails to clean up your workspace. Powered by Gemini AI, it suggests optimal times to unsnooze based on email body context (e.g., event dates or deadlines).
* **Thread Summarizer**: Summarize entire conversational threads into clean, action-oriented bullet points using Gemini, cached locally for performance.
* **Inbox Intelligence**:
  * **Weekly Volume Chart**: Multi-series bar chart for email ingestion frequency.
  * **Top Senders Widget**: Tracks high-frequency senders and enables instant one-click rule creation.
  * **Peak Heatmap Grid**: 7×24 calendar density matrix showing when you receive the most emails.
* **Rule Learning Engine**: Background analyzer that automatically detects manual email categorization patterns (e.g., moving 3+ emails from a domain to a label) and suggests active rules.
* **PWA Support**: Full Progressive Web App support (offline warning banner, custom launch icon, standalone frame, and cache-first/network-first caching strategy via Service Worker).
* **AI Drafts & Auto-Pilot**: Background worker thread checks for new messages, applies rules, checks snooze expiries, and pre-drafts replies.
* **Plugin System**: Modular plugins, such as the built-in Gemini Phishing/Suspicious Email Detector, to analyze message risks.

---

## 🏗️ Architecture Flow

```
                  ┌─────────────────────────────────────┐
                  │          Sortify AI v2 Web UI       │
                  │   (HTML/CSS/JS + GSAP Animations)   │
                  │      (PWA Offline Mode / sw.js)     │
                  └──────────┬───────────────┬──────────┘
                             │               │
                    Real API │               │ Demo Mode
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

## 🛠️ Tech Stack

* **Backend**: Python, Flask, Flask-SQLAlchemy (SQLite database `february.db`), Supabase integration (optional rules backup).
* **Frontend**: HTML5, Vanilla CSS, Vanilla JS, Chart.js (analytics), GSAP (UI animations).
* **AI**: Google Gemini Flash API (`google-genai` SDK).
* **PWA**: manifest.json, sw.js service worker.
* **Containerization**: Docker, Docker Compose.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10 or 3.11 (highly recommended)
* A Google Cloud Console project with the Gmail API enabled (for real mode)
* Gemini API Key from Google AI Studio (for AI features)

### Local Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Piyusha942007/Sortify.git
   cd Sortify
   ```

2. **Set up the virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Setup Environment**:
   Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
   * Populate `.env` with your `GEMINI_API_KEY` and Google OAuth credentials.

5. **Run the Application**:
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` for real mode, or `http://127.0.0.1:5000/demo` for Demo Mode.

---

## 🐳 Docker Deployment

To spin up the containerized environment using Docker Compose:

1. Setup your `.env` file first.
2. Build and run the service:
   ```bash
   docker-compose up --build -d
   ```
3. Access the application at `http://localhost:5000`. The container mounts `february.db` on your local host for persistent storage.

---

## 🧪 Testing

Run the test suite using pytest:
```bash
python -m pytest tests/ -v
```

For guidelines on writing code, adding plugins, or modifying database schemas, refer to the [Contributor Guide](file:///c:/Users/PIYUSHA/OneDrive/Desktop/MyPassionProjects/Sortify/docs/CONTRIBUTING.md).

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
