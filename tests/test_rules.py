import pytest
from unittest.mock import MagicMock, patch
from services.gmail_service import apply_single_rule
from services.gemini_service import suggest_rule_from_text

def test_rule_matching_logic():
    with patch('services.gemini_service.client') as mock_client:
        mock_response = MagicMock()
        mock_response.text = '[{"label": "Food", "domain": "uber.com"}]'
        mock_client.models.generate_content.return_value = mock_response
        
        rules = suggest_rule_from_text("Move food to Food")
        assert len(rules) == 1
        assert rules[0]["label"] == "Food"
        assert rules[0]["domain"] == "uber.com"

@patch('services.gmail_service.get_gmail_service')
@patch('services.gmail_service.ensure_label_exists')
def test_apply_single_rule(mock_ensure_label, mock_get_gmail):
    mock_service = MagicMock()
    mock_get_gmail.return_value = mock_service
    mock_ensure_label.return_value = "label_123"
    
    mock_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg123"}],
        "nextPageToken": None
    }
    
    rule = {"id": 1, "label": "Work", "domain": "slack.com"}
    result = apply_single_rule(rule, "user_123")
    
    assert "Applied rule" in result
    assert "Work" in result
    assert "slack.com" in result
