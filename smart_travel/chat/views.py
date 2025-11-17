import threading
import time
from pathlib import Path

from chat.forms import MessageForm, NewChatForm
from chat.models import ConversationModel, Message
from accounts.models import AccountModel
from django.shortcuts import HttpResponseRedirect, redirect, render  # type: ignore
from lorem_text import lorem  # type: ignore

PROJECT_DIR = Path(__file__).parent.parent


"""
Auxillary
"""


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
    response = Message(lorem.paragraph(), False)
    handle_agent_message(response, chat_id, response)


def _handle_error(request, message: str) -> HttpResponseRedirect:
    request.session["error"] = message
    return redirect("/chat")


"""
Page Loaders
"""


def load_chat_selection(request):
    curr_user = _get_current_user(request)

    convos = [
        (convo.id, convo.title)
        for convo in ConversationModel.find_conversation(curr_user)
    ]

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


def load_chat(request, chat_id: int):
    curr_user = _get_current_user(request)
    convo: ConversationModel = ConversationModel.find_conversation(
        curr_user, chat_id
    ).first()

    context = {
        "chat_id": chat_id,
        "first_name": curr_user.first_name,
        "last_name": curr_user.last_name,
        "messages": convo.retrieve_messages(),
        "message_form": MessageForm(),
    }

    return render(request, "chat.html", context)


"""
Event Handlers
"""


def handle_new_chat(request):
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


def handle_user_message(request, chat_id: int):
    if request.method != "POST":
        return _handle_error(request, "Invalid new chat request.")

    form = MessageForm(request.POST)
    if not form.is_valid():
        return _handle_error(request, "Invalid message request.")

    message = Message(form.cleaned_data["message"], True)

    curr_user = _get_current_user(request)
    convo: ConversationModel = ConversationModel.find_conversation(
        curr_user, chat_id
    ).first()
    convo.save_message(message)

    thread = threading.Thread(
        target=_submit_message_to_agent,
        args=(request, message.message, convo.id),
        daemon=True,
    )
    thread.start()

    return redirect(f"/chat/{chat_id}")


def handle_agent_message(request, chat_id: int, message: Message):
    curr_user = _get_current_user(request)
    convo: ConversationModel = ConversationModel.find_conversation(
        curr_user, chat_id
    ).first()
    convo.save_message(message)
