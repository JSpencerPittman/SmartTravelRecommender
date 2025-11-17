from django.core.management.base import BaseCommand
from chat.models import ConversationModel
from accounts.models import AccountModel


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        AccountModel.objects.all().delete()
        ConversationModel.objects.all().delete()

        new_user = AccountModel.objects.create(
            first_name="Jason",
            last_name="Pittman",
            user_name="jspencerpittman",
            password_hash="hello",
        )

        new_convo = ConversationModel.objects.create(
            title="New Convo",
            user=new_user,
            file_name="new_convo.txt",
        )
        new_convo.add_message("This is a new conversations!")
