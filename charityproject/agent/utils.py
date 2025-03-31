# This file contains utility functions for the webapp.
import uuid, hashlib

from django.conf import settings


def generate_session_id():
    header = uuid.uuid4().hex[:8]
    # Hash the header and secret together
    hash_obj = hashlib.sha256((header + settings.SESSION_ID_SECRET).encode())
    hashed_str = hash_obj.hexdigest()[:16]
    return f"{header}.{hashed_str}"


def verify_session_id(session_id):
    try:
        header, hashed_str = session_id.split(".")
        hash_obj = hashlib.sha256((header + settings.SESSION_ID_SECRET).encode())
        return hashed_str == hash_obj.hexdigest()[:16]
    except ValueError:
        return False
