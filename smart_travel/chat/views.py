import threading
import time
from pathlib import Path
from typing import Any, Optional

from chat.forms import MessageForm, NewChatForm
from chat.models import ConversationModel
from accounts.models import AccountModel
from django.db.models.query import QuerySet  # type: ignore
from django.shortcuts import HttpResponseRedirect, redirect, render  # type: ignore
from lorem_text import lorem  # type: ignore

PROJECT_DIR = Path(__file__).parent.parent


def _get_current_user(request) -> AccountModel:
    """
    Retrieve the current user.

    Note:
        For development purposes this returns the first entry in the AccountModel
        table.

    Returns:
        AccountModel: Current AccountModel
    """

    # TODO: Debug Only
    # user_id=request.session.get('user_id')
    # user=AccountModel.objects.get(id=user_id)
    # return user
    return AccountModel.objects.first()


def _submit_message_to_agent(request, _: str, chat_id: int):
    # TODO: Replace with real LLM agent API
    time.sleep(1)
    response = ConversationModel.Message(lorem.paragraph(), False)

    curr_user = _get_current_user(request)
    convo: ConversationModel = _find_convos(curr_user, chat_id).first()
    convo.add_message(response)


def _find_convos(a: AccountModel, chat_id: Optional[int] = None) -> QuerySet:
    """
    Filter Conversations using provided criteria.

    Args:
        a (AccountModel): Filter our conversations not tied to user.
        chat_id (Optional[int], optional): Find the conversation with the
            provided ID. Defaults to None.

    Returns:
        QuerySet: Filtered conversations.
    """

    search_query: dict[str, Any] = {"user": a}
    if chat_id is not None:
        search_query["id"] = chat_id

    return ConversationModel.objects.filter(**search_query)


def _handle_error(request, message: str) -> HttpResponseRedirect:
    request.session["error"] = message
    return redirect("/chat")


def chat(request, chat_id: int):
    curr_user = _get_current_user(request)
    convo: ConversationModel = _find_convos(curr_user, chat_id).first()

    context = {
        "chat_id": chat_id,
        "first_name": curr_user.first_name,
        "last_name": curr_user.last_name,
        "messages": convo.retrieve(),
        "message_form": MessageForm(),
    }

    return render(request, "chat.html", context)


def select(request):
    curr_user = _get_current_user(request)

    convos = [(convo.id, convo.title) for convo in _find_convos(curr_user)]

    error = request.session.get("error", None)
    if "error" in request.session:
        del request.session["error"]

    context = {
        "first_name": curr_user.first_name,
        "last_name": curr_user.last_name,
        "convos": convos,
        "new_chat_form": NewChatForm(),
        "error": error,
    }

    return render(request, "select.html", context)


def new_chat(request):
    if request.method != "POST":
        return _handle_error(request, "Invalid new chat request.")

    form = NewChatForm(request.POST)
    if not form.is_valid():
        return _handle_error(request, "Invalid new chat request.")

    curr_user = _get_current_user(request)
    title = form.cleaned_data["title"]

    # Create new conversation
    file_name = f"{curr_user.id}_{hash(title)}.txt"
    new_convo = ConversationModel.objects.create(
        title=title, user=curr_user, file_name=file_name
    )

    return redirect(f"/chat/{new_convo.id}")


def new_user_message(request, chat_id: int):
    if request.method != "POST":
        return _handle_error(request, "Invalid new chat request.")

    form = MessageForm(request.POST)
    if not form.is_valid():
        return _handle_error(request, "Invalid message request.")

    message = ConversationModel.Message(form.cleaned_data["message"], True)

    curr_user = _get_current_user(request)
    convo: ConversationModel = _find_convos(curr_user, chat_id).first()
    convo.add_message(message)

    thread = threading.Thread(
        target=_submit_message_to_agent,
        args=(request, message.message, convo.id),
        daemon=True,
    )
    thread.start()

    return redirect(f"/chat/{chat_id}")
