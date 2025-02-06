from django.shortcuts import render
from agent.utils import generate_session_id
from core.utils import track_user_with_session
from agent.constants import *


# Create your views here.
def start_chat(request):
    """View for the chat room."""
    # Track user with session key
    track_user_with_session(request, event="Viewed Chat Room")

    context = {"room_name": generate_session_id(), "selected_model": SELECTED_MODEL}
    return render(request, "agent/chat.html", context=context)
