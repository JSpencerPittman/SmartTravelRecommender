from pathlib import Path
from typing import Any, Optional

from chat.forms import MessageForm, NewChatForm
from chat.models import Conversation, User
from django.core.files.base import ContentFile  # type: ignore
from django.db.models.query import QuerySet  # type: ignore
from django.shortcuts import redirect, render, HttpResponseRedirect  # type: ignore

PROJECT_DIR = Path(__file__).parent.parent


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


def _find_convos(u: User, chat_id: Optional[int] = None) -> QuerySet:
    """
    Filter Conversations using provided criteria.

    Args:
        u (User): Filter our conversations not tied to user.
        chat_id (Optional[int], optional): Find the conversation with the
            provided ID. Defaults to None.

    Returns:
        QuerySet: Filtered conversations.
    """

    search_query: dict[str, Any] = {"user": u}
    if chat_id is not None:
        search_query["id"] = chat_id

    return Conversation.objects.filter(**search_query)


def _handle_error(message: str) -> HttpResponseRedirect:
    return redirect("/chat")


def chat(request, chat_id: int):
    curr_user = _get_current_user()
    convo: Conversation = _find_convos(curr_user, chat_id).first()

    context = {
        "chat_id": chat_id,
        "first_name": curr_user.first_name,
        "last_name": curr_user.last_name,
        "conversation": convo.retrieve(),
        "message_form": MessageForm(),
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
    if request.method != "POST":
        return _handle_error("Invalid new chat request.")

    form = NewChatForm(request.POST)
    if not form.is_valid():
        return _handle_error("Invalid new chat request.")

    curr_user = _get_current_user()
    title = form.cleaned_data["title"]

    # Create new conversation
    file_name = f"{curr_user.id}_{hash(title)}.txt"
    new_convo = Conversation.objects.create(
        title=title, user=curr_user, file_name=file_name
    )

    return redirect(f"/chat/{new_convo.id}")


def message(request, chat_id: int):
    if request.method != "POST":
        return _handle_error("Invalid new chat request.")

    form = MessageForm(request.POST)
    if not form.is_valid():
        return _handle_error("Invalid message request.")

    message = form.cleaned_data["message"]

    curr_user = _get_current_user()
    convo: Conversation = _find_convos(curr_user, chat_id).first()
    convo.add_message(message)

    return redirect(f"/chat/{chat_id}")
