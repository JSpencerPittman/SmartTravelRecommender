from django.core.management.base import BaseCommand
from chat.models import Conversation
from accounts.models import AccountModel


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print("Users:")
        for user in AccountModel.objects.all():
            print(f"User: {user.first_name} {user.last_name}")

        print("Conversations:")
        for convo in Conversation.objects.all():
            print(f"Conversation: {convo.title} {convo.history_file_path} {convo.user}")
