from django.urls import path
from . import views

urlpatterns = [
    path("<int:chat_id>", views.chat, name="chat"),
    path("select", views.select, name="select"),
    path("new_chat", views.new_chat, name="new_chat"),
    path("message/<int:chat_id>", views.message, name="message"),
]
