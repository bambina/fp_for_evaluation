from django.shortcuts import render
from agent.utils import generate_session_id


# Create your views here.
def start_chat(request):
    return render(
        request, "agent/chat.html", context={"room_name": generate_session_id()}
    )
