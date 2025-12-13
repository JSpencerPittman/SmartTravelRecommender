from eda.cqrs import CQRSCommand
from accounts.models import AccountModel
from eda.event_dispatcher import publish
from django.contrib.auth.hashers import make_password  # type: ignore


"""
Command: Create User
"""


class CommandCreateUser(CQRSCommand):
    EVENT_NAME = "CREATED_USER"

    @staticmethod
    def execute(first_name: str, last_name: str, user_name: str, password: str) -> bool:
        AccountModel.objects.create(
            first_name=first_name,
            last_name=last_name,
            user_name=user_name,
            password_hash=make_password(password),
        )

        publish(CommandCreateUser.EVENT_NAME)
        return True
