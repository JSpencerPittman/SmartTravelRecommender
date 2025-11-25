from accounts.models import AccountModel
from chat.models import ConversationModel, Message
from django.core.management.base import BaseCommand  # type: ignore
from accounts.cqrs.commands import CommandCreateUser
from accounts.cqrs.queries import QueryFindUser
from eda.event_dispatcher import register_subscriber


def _create_convo_on_user_creation(data: dict):
    user_id = data["user_id"]
    new_user = QueryFindUser.execute(user_id)["data"][0]
    new_convo = ConversationModel.create(title="New Convo", user=new_user)
    new_message = Message("This is a new conversation", False)
    new_convo.save_message(new_message)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        AccountModel.objects.all().delete()
        ConversationModel.objects.all().delete()

        register_subscriber("CREATED_USER", _create_convo_on_user_creation)
        CommandCreateUser.create(
            first_name="Jason",
            last_name="Pittman",
            user_name="jspencerpittman",
            password="hello",
        )
