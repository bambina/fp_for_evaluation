# Description: Utility functions for the core app.
from django.core.management.color import color_style

from django.utils.timezone import now
import logging

usertest_logger = logging.getLogger("usertest")


def write_success(stdout, style, msg):
    """
    Utility function to write a success message to stdout with SUCCESS styling.
    """
    stdout.write(style.SUCCESS(msg))


def write_error(stdout, style, msg):
    """
    Utility function to write an error message to stdout with ERROR styling.
    """
    stdout.write(style.ERROR(msg))


def track_user_with_session(request, event):
    """Track user with session key."""
    session_key = request.session.session_key

    # Create a new session if one does not exist
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # Log the event
    msg = f"[{event}] Session Key: {session_key}, Accessed Path: {request.path}, Time: {now()}"
    usertest_logger.info(msg)

    print(msg)


def log_user_test(text):
    """
    Log messages for user testing purposes.
    Captures user interactions and system responses for analysis.
    """
    usertest_logger.info(text)
