from django.urls import path
from . import views

urlpatterns = [
    path("", views.select, name="select"),
    path("<int:chat_id>", views.chat, name="chat"),
    path("new_chat", views.new_chat, name="new_chat"),
    path("new_user_message/<int:chat_id>", views.new_user_message, name="message"),
]
