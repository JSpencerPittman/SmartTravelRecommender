from eda.cqrs import CQRSCommand
from accounts.models import AccountModel
from eda.event_dispatcher import publish
import hashlib

from chat.models import ConversationModel
from django.utils import timezone  # type: ignore

"""
Command: Create Conversation
"""


class CommandCreateConversation(CQRSCommand):
    EVENT_NAME = "NEW_CONVERSATION"

    @staticmethod
    def execute(title: str, user: AccountModel) -> bool:
        """
        Create a new conversation.

        Args:
            title (str): Title of the conversation.
            user (AccountModel): User creating new conversation.

        Returns:
            ConversationModel: New conversation.
        """

        def create_unique_filename(title: str, user_name: str) -> str:
            """
            Create a unique filename using the title and user name.

            Note:
                Uses hashing to create a unique filename for each user x title combination. This
                makes it easier to handle special characters in the consituent title and user
                strings if they have been hashed.

            Args:
                title (str): Title of the conversation.
                user_name (str): User's user name.

            Returns:
                str: Unique filename.
            """

            title_hash = hashlib.sha256(title.encode("utf-8")).hexdigest()
            user_name_hash = hashlib.sha256(user_name.encode("utf-8")).hexdigest()
            return f"{user_name_hash}__{title_hash}.txt"

        try:
            new_convo = ConversationModel.objects.create(
                title=title,
                user=user,
                file_name=create_unique_filename(title, user.user_name),
                time_of_last_message=timezone.now(),
            )
        except Exception:
            return False

        publish(CommandCreateConversation.EVENT_NAME, {"conv_id": new_convo.id})
        return True
