from django.urls import path  # type: ignore
from . import views

urlpatterns = [
    path("", views.load_chat_selection, name="select"),
    path("<int:chat_id>", views.load_chat, name="chat"),
    path("new_chat", views.handle_new_chat, name="new_chat"),
    path("new_user_message/<int:chat_id>", views.handle_user_message, name="message"),
]
