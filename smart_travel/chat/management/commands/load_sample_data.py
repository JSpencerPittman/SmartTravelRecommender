from accounts.models import AccountModel
from chat.models import ConversationModel
from chat.utility.message import Message
from django.core.management.base import BaseCommand  # type: ignore
from accounts.cqrs.commands import CommandCreateUser
from chat.cqrs.commands import CommandCreateConversation
from accounts.cqrs.queries import QueryFindUser
from eda.event_dispatcher import subscribe, get_event
from time import time


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

        subscribe("Command", "CREATED_USER")
        CommandCreateUser.execute(
            first_name="Jason",
            last_name="Pittman",
            user_name="jspencerpittman",
            password="hello",
        )

        while True:
            event = get_event("Command")
            if event is not None:
                break
            time.sleep(0.01)

        user = AccountModel.objects.first()
        CommandCreateConversation.execute("Paris Itinerary", user)
        CommandCreateConversation.execute("What is Spain like?", user)
        CommandCreateConversation.execute("Restaurants in Venice", user)
