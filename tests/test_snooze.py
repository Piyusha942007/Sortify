import pytest
from datetime import datetime, timedelta
from app import app
from models import db, SnoozedEmail
from services.snooze_service import snooze_email, check_expired_snoozes

@pytest.fixture
def client_app():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

def test_snooze_model_creation(client_app):
    with client_app.app_context():
        snooze_time = datetime.utcnow() + timedelta(hours=2)
        snooze_email(
            google_id="test_user",
            message_id="msg_123",
            snooze_until=snooze_time,
            reason="Follow-up needed",
            is_demo=True
        )
        
        record = SnoozedEmail.query.filter_by(gmail_message_id="msg_123").first()
        assert record is not None
        assert record.google_id == "test_user"
        assert record.reason == "Follow-up needed"
        assert record.snooze_until > datetime.utcnow()

def test_snooze_expiry_detection(client_app):
    with client_app.app_context():
        expired_time = datetime.utcnow() - timedelta(minutes=5)
        snooze_email(
            google_id="demo_user",
            message_id="msg_expired",
            snooze_until=expired_time,
            reason="Expired",
            is_demo=True
        )
        
        record = SnoozedEmail.query.filter_by(gmail_message_id="msg_expired").first()
        assert record is not None
        
        check_expired_snoozes(client_app)
        
        record_after = SnoozedEmail.query.filter_by(gmail_message_id="msg_expired").first()
        assert record_after is None
