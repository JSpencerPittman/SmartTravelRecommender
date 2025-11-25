from django.urls import path  # type: ignore
from . import views

urlpatterns = [
    # Views
    path("", views.chat_controller, name="chat"),
    # Operations
    path(
        "operation/select_chat/<int:conv_id>",
        views.handle_select_chat,
        name="operation__select_chat",
    ),
    path(
        "operation/delete_chat/<int:conv_id>",
        views.handle_delete_chat,
        name="operation__delete_chat",
    ),
    path("operation/new_chat", views.handle_new_chat, name="operation__new_chat"),
    path(
        "operation/go_to_select",
        views.handle_go_to_select,
        name="operation__go_to_select",
    ),
    path(
        "operation/new_user_message",
        views.handle_new_user_message,
        name="operation__new_user_message",
    ),
    path("event_stream", views.event_stream, name="event_stream"),
]
