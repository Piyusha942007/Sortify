import pytest
from services.gmail_service import parse_list_unsubscribe

def test_parse_list_unsubscribe_mailto_only():
    header = '<mailto:unsub-123@pinterest.com?subject=unsubscribe>'
    mailto, http = parse_list_unsubscribe(header)
    assert mailto == 'mailto:unsub-123@pinterest.com?subject=unsubscribe'
    assert http is None

def test_parse_list_unsubscribe_both():
    header = '<mailto:unsub-123@pinterest.com?subject=unsub>, <https://pinterest.com/unsub>'
    mailto, http = parse_list_unsubscribe(header)
    assert mailto == 'mailto:unsub-123@pinterest.com?subject=unsub'
    assert http == 'https://pinterest.com/unsub'

def test_parse_list_unsubscribe_empty():
    mailto, http = parse_list_unsubscribe("")
    assert mailto is None
    assert http is None

def test_unsubscribe_confidence_thresholding():
    import demo_data
    import importlib
    importlib.reload(demo_data)
    # 14 auto-unsubscribed senders have confidence >= 0.85
    for item in demo_data.unsubscribed_done:
        assert item["confidence"] >= 0.85
    # 5 pending review senders have confidence between 0.50 and 0.84
    for item in demo_data.unsubscribed_queue:
        assert 0.50 <= item["confidence"] <= 0.84
