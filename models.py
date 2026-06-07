from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SnoozedEmail(db.Model):
    __tablename__ = 'snoozed_emails'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    google_id = db.Column(db.String(255), nullable=False)
    gmail_message_id = db.Column(db.String(255), nullable=False)
    snooze_until = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ThreadSummary(db.Model):
    __tablename__ = 'thread_summaries'
    thread_id = db.Column(db.String(255), primary_key=True)
    summary_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ActionLog(db.Model):
    __tablename__ = 'action_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    google_id = db.Column(db.String(255), nullable=True)
    event_type = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class DismissedSuggestion(db.Model):
    __tablename__ = 'dismissed_suggestions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    google_id = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    suggested_label = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
