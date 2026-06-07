# Contributor Guide for Sortify AI

Thank you for your interest in contributing to **Sortify AI v2**! This document provides information on setting up the codebase locally, understanding project architecture, writing and running tests, and developing custom plugins.

---

## 1. Local Development Setup

Follow these steps to run Sortify AI locally:

### Prerequisites
* Python 3.10 or 3.11 (Python 3.11 is recommended)
* Git

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Piyusha942007/Sortify.git
   cd Sortify
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Setup Environment Variables**:
   Copy the example environment file and fill in your values:
   ```bash
   cp .env.example .env
   ```
   * Open `.env` and fill in your `GEMINI_API_KEY`.
   * For real Gmail sync, populate the `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_PROJECT_ID`.
   * Supabase configuration is optional; Sortify automatically falls back to a local SQLite database (`february.db`) if Supabase is unavailable.

5. **Start the Application**:
   ```bash
   python app.py
   ```
   The application will be accessible at [http://127.0.0.1:5000](http://127.0.0.1:5000). To test the no-auth experience, navigate to [http://127.0.0.1:5000/demo](http://127.0.0.1:5000/demo).

---

## 2. Environment Variables & Database

Sortify AI dynamically detects storage backends:
* **SQLite Database**: Handled via Flask-SQLAlchemy, utilizing a local `february.db` file. The schema is defined in [models.py](file:///c:/Users/PIYUSHA/OneDrive/Desktop/MyPassionProjects/Sortify/models.py). Tables are automatically initialized during startup using `db.create_all()`.
* **Supabase**: If `SUPABASE_URL` and `SUPABASE_KEY` are provided and online, Sortify will use it to pull and push rules. If connection fails, it reverts gracefully to SQLite.

---

## 3. Running Tests

The test suite validates mock API functionality, smart rules processing, snooze timeouts, and list-unsubscribe header parsing.

Run all tests with:
```bash
python -m pytest tests/ -v
```

### Writing New Tests
* Place new test scripts inside the [tests/](file:///c:/Users/PIYUSHA/OneDrive/Desktop/MyPassionProjects/Sortify/tests) directory.
* Prefix filenames with `test_` (e.g., `test_my_feature.py`).
* If modifying mock data lists, remember to reload the `demo_data` module using `importlib.reload(demo_data)` to prevent state pollution in other test modules.

---

## 4. Developing Plugins

Sortify AI includes a extensible Plugin/Extension system. Plugins run during email ingestion and can flag messages, trigger notifications, or tag threads.

### Create a Custom Plugin

1. **Define your Plugin class**:
   Create a new Python file in the `plugins/` directory (e.g., `plugins/spam_tagger.py`). Inherit from `BasePlugin` and implement the `run` method.

   ```python
   from plugins import BasePlugin

   class SpamTaggerPlugin(BasePlugin):
       def __init__(self):
           super().__init__()
           self.name = "Spam Tagger"
           self.description = "Identifies high-frequency marketing buzzwords to flag marketing material."

       def run(self, message_details, google_id):
           """
           message_details: dict containing 'sender', 'subject', 'body'
           google_id: str representing the authenticated Google user ID
           
           Returns a dict to raise a warning/notification, or None if safe.
           """
           body = message_details.get("body", "").lower()
           keywords = ["buy now", "limited offer", "exclusive deal", "win cash"]
           
           for kw in keywords:
               if kw in body:
                   return {
                       "status": "info", # Can be 'info', 'warning', or 'success'
                       "tag": "MARKETING",
                       "message": f"Contains promotional keyword: '{kw}'"
                   }
           return None
   ```

2. **Register the Plugin**:
   Import and register your plugin in [app.py](file:///c:/Users/PIYUSHA/OneDrive/Desktop/MyPassionProjects/Sortify/app.py):
   
   ```python
   # Import your plugin
   from plugins.spam_tagger import SpamTaggerPlugin

   # Inside the global plugins list (around line 90):
   ACTIVE_PLUGINS = [
       PhishingDetector(),
       SpamTaggerPlugin() # Add it here
   ]
   ```

3. **Verify the Plugin**:
   Run the Flask server, visit the plugins tab in the dashboard, and make sure your plugin displays and executes correctly.
