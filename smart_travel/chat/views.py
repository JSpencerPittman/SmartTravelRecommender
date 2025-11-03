from django.shortcuts import render, redirect
from chat.models import User, Conversation
from django.core.files.base import ContentFile
from chat.forms import NewChatForm
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
        "new_chat_form": NewChatForm(),
    }

    return render(request, "select.html", context)


def new_chat(request):
    assert request.method == "POST"
    form = NewChatForm(request.POST)
    assert form.is_valid()
    title = form.cleaned_data["title"]

    curr_user = _get_current_user()
    new_convo = Conversation.objects.create(title=title, user=curr_user)
    history_file_path = f"{curr_user.id}_{hash(title)}.txt"
    new_convo.history_file_path.save(history_file_path, ContentFile("".encode()), True)

    return redirect(f"/chat/{new_convo.id}")
