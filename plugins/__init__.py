class BasePlugin:
    def __init__(self):
        self.name = "Base Plugin"
        self.description = "Base class for all Sortify plugins."

    def run(self, message_details, google_id):
        """
        Runs the plugin action on a single email.
        message_details: dict containing 'sender', 'subject', 'body'
        google_id: user's Google ID for integration calls
        Returns a dict: {'status': 'info/warning/success', 'message': 'Result explanation'} or None.
        """
        pass
