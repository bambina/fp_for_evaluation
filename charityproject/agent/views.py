from django.shortcuts import render
from agent.utils import generate_session_id
from core.utils import track_user_with_session


# Create your views here.
def start_chat(request):
    """View for the chat room."""
    # Track user with session key
    track_user_with_session(request, event="Viewed Chat Room")

    return render(
        request, "agent/chat.html", context={"room_name": generate_session_id()}
    )
