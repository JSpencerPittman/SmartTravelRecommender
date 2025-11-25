from eda.cqrs import CQRSCommand
from accounts.models import AccountModel
from eda.event_dispatcher import publish_event
from django.contrib.auth.hashers import make_password  # type: ignore


"""
Command: Create User
"""


class CommandCreateUser(CQRSCommand):
    EVENT_NAME = "CREATED_USER"

    @staticmethod
    def execute(first_name: str, last_name: str, user_name: str, password: str) -> bool:
        try:
            new_user = AccountModel.objects.create(
                first_name=first_name,
                last_name=last_name,
                user_name=user_name,
                password_hash=make_password(password),
            )
        except Exception:
            return False

        CommandCreateUser.publish_event(new_user.id)
        return True

    @staticmethod
    def publish_event(user_id: int):
        publish_event(CommandCreateUser.EVENT_NAME, {"user_id": user_id})
