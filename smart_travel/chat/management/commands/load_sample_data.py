from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from chat.models import User, Conversation


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        User.objects.all().delete()
        Conversation.objects.all().delete()

        new_user = User.objects.create(first_name="Jason Pittman")

        new_convo = Conversation.objects.create(
            title="New Convo", user=new_user, file_name="new_convo.txt"
        )
        new_convo.add_message("This is a new conversations!")
