import re
import hashlib

from django.test import override_settings

from agent.utils import *


@override_settings(SESSION_ID_SECRET="test")
def test_generate_session_id():
    session_id = generate_session_id()
    # Check format: 8 hex chars + '.' + 16 hex chars
    assert re.match(r"^[a-f0-9]{8}\.[a-f0-9]{16}$", session_id)
    header, hashed = session_id.split(".")
    expected_hash = hashlib.sha256((header + "test").encode()).hexdigest()[:16]
    assert hashed == expected_hash


@override_settings(SESSION_ID_SECRET="test")
def test_verify_session_id_valid():
    # Should return True for a correctly formatted and valid session ID
    header = "abcd1234"
    expected_hash = hashlib.sha256((header + "test").encode()).hexdigest()[:16]
    session_id = f"{header}.{expected_hash}"
    assert verify_session_id(session_id) is True


@override_settings(SESSION_ID_SECRET="test")
def test_verify_session_id_malformed():
    # Should return False if the session ID format is invalid (missing period)
    session_id = "invalidsessionid"
    assert verify_session_id(session_id) is False
