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
    curr_user = AccountModel.get_current_user(request, debug=True)
    assert curr_user is not None

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
    curr_user = AccountModel.get_current_user(request, debug=True)
    assert curr_user is not None
    convo: ConversationModel = ConversationModel.find_conversation(
        user=curr_user, chat_id=chat_id
    )[0]

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

    curr_user = AccountModel.get_current_user(request, debug=True)
    assert curr_user is not None
    new_convo = ConversationModel.create(form.cleaned_data["title"], curr_user)

    return redirect(f"/chat/{new_convo.id}")


def handle_user_message(request, chat_id: int):
    if request.method != "POST":
        return _handle_error(request, "Invalid new chat request.")

    form = MessageForm(request.POST)
    if not form.is_valid():
        return _handle_error(request, "Invalid message request.")

    message = Message(form.cleaned_data["message"], True)

    curr_user = AccountModel.get_current_user(request, True)
    assert curr_user is not None
    convo: ConversationModel = ConversationModel.find_conversation(curr_user, chat_id)[
        0
    ]
    convo.save_message(message)

    thread = threading.Thread(
        target=_submit_message_to_agent,
        args=(request, message.message, convo.id),
        daemon=True,
    )
    thread.start()

    return redirect(f"/chat/{chat_id}")


def handle_agent_message(request, chat_id: int, message: Message):
    curr_user = AccountModel.get_current_user(request, debug=True)
    assert curr_user is not None
    convo: ConversationModel = ConversationModel.find_conversation(curr_user, chat_id)[
        0
    ]
    convo.save_message(message)
