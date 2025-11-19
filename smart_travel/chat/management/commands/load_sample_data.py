from accounts.models import AccountModel
from chat.models import ConversationModel, Message
from django.core.management.base import BaseCommand  # type: ignore


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        AccountModel.objects.all().delete()
        ConversationModel.objects.all().delete()

        new_user = AccountModel.create(
            first_name="Jason",
            last_name="Pittman",
            user_name="jspencerpittman",
            password="hello",
        )
        new_convo = ConversationModel.create(title="New Convo", user=new_user)
        new_message = Message("This is a new conversation", False)
        new_convo.save_message(new_message)
