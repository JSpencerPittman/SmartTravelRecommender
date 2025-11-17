from accounts.models import AccountModel
from chat.models import ConversationModel
from django.core.management.base import BaseCommand  # type: ignore
from django.utils import timezone  # type: ignore


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
            time_of_last_message=timezone.now(),
        )
        new_convo.save_message("This is a new conversations!")
