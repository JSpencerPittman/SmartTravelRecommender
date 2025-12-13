import json
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Optional

from accounts.cqrs.queries import QueryGetCurrentUser
from accounts.models import AccountModel
from chat.cqrs.commands import (
    CommandCreateConversation,
    CommandDeleteConversation,
    CommandSaveMessage,
)
from chat.cqrs.queries import QueryFindConversation, QueryRetrieveMessages
from chat.forms import MessageForm, NewChatForm
from chat.models import ConversationModel
from chat.utility.message import Message
from chatbot.travel_chatbot import Chatbot
from django.http.response import StreamingHttpResponse  # type: ignore
from django.shortcuts import HttpResponseRedirect, redirect, render  # type: ignore
from eda.event_dispatcher import EmittedEvent, get_event, publish, subscribe

PROJECT_DIR = Path(__file__).parent.parent
DEBUG = False

chatbot = Chatbot()
if not DEBUG:
    chatbot.initialize_session()


"""
Auxillary
"""


def get_current_user(request) -> Optional[AccountModel]:
    curr_user = None

    if DEBUG:
        curr_user = AccountModel.objects.first()
    else:
        curr_user = QueryGetCurrentUser.execute(request)["data"]

    return curr_user


def _submit_message_to_agent(request, last_user_message: str, conv_id: int):
    message: Optional[Message] = None
    if DEBUG:
        time.sleep(1)
        message = Message("RESPONSE", False)
    else:
        prev_messages = QueryRetrieveMessages.execute(request.session["conv_id"])[
            "data"
        ]
        response = chatbot.prompt_completion(prev_messages)
        if response is not None:
            message = Message(response, False)

    if message is not None:
        CommandSaveMessage.execute(conv_id, message)
        publish("NEW_AGENT_MESSAGE", data={"message": message})


def _handle_error(request, message: str) -> HttpResponseRedirect:
    request.session["error"] = message
    return redirect("/chat")


"""
Event Handlers
"""


class EventHandlerAction(Enum):
    IDLE = 0
    RELOAD = 1

    def response(self) -> str:
        if EventHandlerAction.IDLE == self:
            time.sleep(1)
            return ": keepalive\n\n"
        else:
            return f"data: {json.dumps({'action': 'reload'})}\n\n"


def event_handler__new_conversation(request, event: EmittedEvent) -> EventHandlerAction:
    if "conv_id" not in request.session:
        request.session["conv_id"] = event["data"]["conv_id"]
        request.session.save()
        return EventHandlerAction.RELOAD
    else:
        return EventHandlerAction.IDLE


def event_handler__new_user_message(request, event: EmittedEvent) -> EventHandlerAction:
    message = event["data"]["message"]
    conv_id = request.session["conv_id"]
    CommandSaveMessage.execute(conv_id, message)
    thread = threading.Thread(
        target=_submit_message_to_agent,
        args=(request, message.message, conv_id),
        daemon=True,
    )
    thread.start()
    return EventHandlerAction.RELOAD


EVENT_HANDLER_CALLBACKS = {
    "NEW_CONVERSATION": event_handler__new_conversation,
    "NEW_USER_MESSAGE": event_handler__new_user_message,
    "NEW_AGENT_MESSAGE": EventHandlerAction.RELOAD,
    "DELETE_CONVERSATION": EventHandlerAction.RELOAD,
}
SUBSCRIBER__EVENT_STREAM = "event_stream"


def event_stream(request):
    for event in EVENT_HANDLER_CALLBACKS.keys():
        subscribe(SUBSCRIBER__EVENT_STREAM, event)

    def event_generator():
        while True:
            action = EventHandlerAction.IDLE
            event = get_event(SUBSCRIBER__EVENT_STREAM)
            if event is not None and event["name"] in EVENT_HANDLER_CALLBACKS:
                handler = EVENT_HANDLER_CALLBACKS[event["name"]]

                if isinstance(handler, EventHandlerAction):
                    action = handler
                else:
                    action = handler(request, event)

            yield action.response()

    return StreamingHttpResponse(event_generator(), content_type="text/event-stream")


"""
Request Handlers
"""


def handle_select_chat(request, conv_id: int):
    request.session["conv_id"] = conv_id
    return redirect("/chat")


def handle_delete_chat(request, conv_id: int):
    curr_user = get_current_user(request)
    assert curr_user is not None
    CommandDeleteConversation.execute(curr_user.id, conv_id)
    return redirect("/chat")


def handle_new_chat(request):
    if request.method != "POST":
        return _handle_error(request, "Invalid new chat request.")

    form = NewChatForm(request.POST)
    if not form.is_valid():
        return _handle_error(request, "Invalid new chat request.")

    curr_user = get_current_user(request)
    assert curr_user is not None
    CommandCreateConversation.execute(form.cleaned_data["title"], curr_user)

    return redirect("/chat")


def handle_go_to_select(request):
    del request.session["conv_id"]
    return redirect("/chat")


def handle_new_user_message(request):
    if request.method != "POST":
        return _handle_error(request, "Invalid new chat request.")

    form = MessageForm(request.POST)
    if not form.is_valid():
        return _handle_error(request, "Invalid message request.")

    message = Message(form.cleaned_data["message"], True)

    publish("NEW_USER_MESSAGE", data={"message": message})
    return redirect("/chat")


"""
Controllers
"""


def chat_controller(request):
    if "conv_id" in request.session:
        return chat_view_controller(request)
    else:
        return chat_selection_view_controller(request)


def chat_selection_view_controller(request):
    curr_user = get_current_user(request)
    if curr_user is None:
        return redirect("/accounts")

    limit = 5  # intital count of convos to be displayed
    if request.method == "POST":
        limit = int(request.POST.get("limit", 5))
        limit += 5  # output additional 5 convos for every load more request made

    result = QueryFindConversation.execute(curr_user, limit=limit)
    convos = [(convo.id, convo.title) for convo in result["data"]]
    totalConvos = ConversationModel.objects.filter(user=curr_user).count()

    error = request.session.get("error", None)
    if "error" in request.session:
        del request.session["error"]

    context = {
        "first_name": curr_user.first_name,
        "last_name": curr_user.last_name,
        "convos": convos,
        "new_chat_form": NewChatForm(),
        "error": error,
        "totalConvos": totalConvos,
        "limit": 5,
    }

    return render(request, "select.html", context)


def chat_view_controller(request):
    curr_user = get_current_user(request)
    if curr_user is None:
        return redirect("/accounts")

    conv_id = request.session["conv_id"]
    result = QueryRetrieveMessages.execute(conv_id)
    messages = result["data"]

    context = {
        "chat_id": conv_id,
        "first_name": curr_user.first_name,
        "last_name": curr_user.last_name,
        "title": result["title"],
        "messages": messages,
        "message_form": MessageForm(),
    }

    return render(request, "chat.html", context)
