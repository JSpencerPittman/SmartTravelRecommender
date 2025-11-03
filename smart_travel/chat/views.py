from django.shortcuts import render
from chat.models import User, Conversation
from typing import Optional, Any


def _get_current_user() -> User:
    """
    Retrieve the current user.

    Note:
        For development purposes this returns the first entry in the User
        table.

    Returns:
        User: Current User
    """

    # TODO: Use session context to find current user
    user = User.objects.first()
    return user


def _find_convos(u: User, chat_id: Optional[int] = None):
    search_query: dict[str, Any] = {"user": u}
    if chat_id is not None:
        search_query["id"] = chat_id

    return Conversation.objects.filter(**search_query)


def chat(request, chat_id: int):
    curr_user = _get_current_user()
    convo = _find_convos(curr_user, chat_id).first()

    text = "\n".join([v.decode() for v in convo.history_file_path.readlines()])

    context = {
        "first_name": curr_user.first_name,
        "last_name": curr_user.last_name,
        "conversation": text,
    }

    return render(request, "chat.html", context)


def select(request):
    curr_user = _get_current_user()

    convos = [(convo.id, convo.title) for convo in _find_convos(curr_user)]

    context = {
        "first_name": curr_user.first_name,
        "last_name": curr_user.last_name,
        "convos": convos,
    }

    return render(request, "select.html", context)
