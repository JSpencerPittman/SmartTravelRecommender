from django.shortcuts import render
from chat.models import User, Conversation


def index(request):
    user = User.objects.first()
    convo = Conversation.objects.first()

    text = "\n".join([v.decode() for v in convo.history_file_path.readlines()])

    context = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "conversation": text,
    }

    return render(request, "chat.html", context)
