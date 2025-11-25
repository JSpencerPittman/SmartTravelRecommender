import threading
from pathlib import Path
import json

from chat.forms import MessageForm, NewChatForm
from chat.models import ConversationModel, Message
from accounts.models import AccountModel
from django.shortcuts import HttpResponseRedirect, redirect, render  # type: ignore
from django.http.response import StreamingHttpResponse

# from accounts.cqrs.queries import QueryGetCurrentUser
from chat.cqrs.queries import QueryFindConversation
from chat.cqrs.commands import CommandCreateConversation
from eda.event_dispatcher import get_event, subscribe, publish
import time

# from lorem_text import lorem  # type: ignore

# from chatbot.travel_chatbot import TravelChatbot
PROJECT_DIR = Path(__file__).parent.parent

# chatbot = TravelChatbot()


"""
Auxillary
"""


def get_current_user(request) -> AccountModel:
    # result = QueryGetCurrentUser.execute(request)
    # assert result["status"]
    # curr_user = result["data"]
    # assert curr_user is not None
    # return curr_user
    curr_user = AccountModel.objects.first()
    assert curr_user is not None
    return curr_user


def _submit_message_to_agent(request, last_user_message: str, chat_id: int):
    # curr_user = get_current_user(request)
    # convo: ConversationModel = ConversationModel.find_conversation(
    #     user=curr_user, chat_id=chat_id
    # )[0]
    # messages: list[Message] = convo.retrieve_messages()
    # response = Message(chatbot.generate_response(messages), False)
    time.sleep(1)
    message = Message("RESPONSE", False)
    curr_user = get_current_user(request)
    convo = QueryFindConversation.execute(curr_user, chat_id)["data"][0]
    convo.save_message(message)
    publish("NEW_AGENT_MESSAGE", data={"message": message})


def _handle_error(request, message: str) -> HttpResponseRedirect:
    request.session["error"] = message
    return redirect("/chat")


def event_stream(request):
    subscribe("select_page_view", "NEW_CONVERSATION")
    subscribe("select_page_view", "NEW_USER_MESSAGE")
    subscribe("select_page_view", "NEW_AGENT_MESSAGE")

    def idle():
        time.sleep(1)
        return ": keepalive\n\n"

    def event_generator():
        while True:
            event = get_event("select_page_view")
            if event is not None:
                match event["name"]:
                    case "NEW_CONVERSATION":
                        if "conv_id" not in request.session:
                            request.session["conv_id"] = event["data"]["conv_id"]
                            request.session.save()
                            yield f"data: {json.dumps({'action': 'reload'})}\n\n"
                        else:
                            yield idle()
                    case "NEW_USER_MESSAGE":
                        message = event["data"]["message"]
                        curr_user = get_current_user(request)
                        convo = QueryFindConversation.execute(
                            curr_user, request.session["conv_id"]
                        )["data"][0]
                        convo.save_message(message)
                        thread = threading.Thread(
                            target=_submit_message_to_agent,
                            args=(request, message.message, convo.id),
                            daemon=True,
                        )
                        thread.start()
                        print("PROCESSED NEW MESSAGE")
                        yield f"data: {json.dumps({'action': 'reload'})}\n\n"
                    case "NEW_AGENT_MESSAGE":
                        yield f"data: {json.dumps({'action': 'reload'})}\n\n"
                    case _:
                        yield idle()
            else:
                yield idle()

    return StreamingHttpResponse(event_generator(), content_type="text/event-stream")


"""
Page Loaders
"""


def chat_controller(request):
    if "conv_id" in request.session:
        return chat_view_controller(request)
    else:
        return chat_selection_view_controller(request)


def chat_selection_view_controller(request):
    curr_user = get_current_user(request)

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
    conv_id = request.session["conv_id"]
    result = QueryFindConversation.execute(user=curr_user, chat_id=conv_id)
    convo: ConversationModel = result["data"][0]

    context = {
        "chat_id": conv_id,
        "first_name": curr_user.first_name,
        "last_name": curr_user.last_name,
        "messages": convo.retrieve_messages(),
        "message_form": MessageForm(),
    }

    return render(request, "chat.html", context)


"""
Event Handlers
"""


def handle_select_chat(request, conv_id: int):
    request.session["conv_id"] = conv_id
    return redirect("/chat")


def handle_new_chat(request):
    if request.method != "POST":
        return _handle_error(request, "Invalid new chat request.")

    form = NewChatForm(request.POST)
    if not form.is_valid():
        return _handle_error(request, "Invalid new chat request.")

    curr_user = get_current_user(request)
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
