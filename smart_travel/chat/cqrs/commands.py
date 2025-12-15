import hashlib
from pathlib import Path

from accounts.models import AccountModel
from chat.models import ConversationModel, ConvoRepo
from chat.utility.message import Message
from django.utils import timezone  # type: ignore
from eda.cqrs import CQRSCommand
from eda.event_dispatcher import publish
from chat.cqrs.queries import (
    QueryFindConversation,
    _ensure_file_exists,
    _retrieve_convo_by_id,
)


"""
Command: Create Conversation
"""


class CommandCreateConversation(CQRSCommand):
    EVENT_NAME = "NEW_CONVERSATION"

    @staticmethod
    def execute(title: str) -> bool:
        """
        Create a new conversation.

        Args:
            title (str): Title of the conversation.
            user (AccountModel): User creating new conversation.

        Returns:
            ConversationModel: New conversation.
        """

        def create_unique_filename(title: str, chatId: int) -> str:
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
            user_name_hash = hashlib.sha256(str(chatId).encode("utf-8")).hexdigest()
            return f"{user_name_hash}__{title_hash}.txt"

        try:
            new_convo = ConversationModel.objects.create(
                title=title,
                time_of_last_message=timezone.now(),
            )
            new_convo.file_name = create_unique_filename(new_convo.title, new_convo.id)
            new_convo.save()
        except Exception:
            return False

        publish(CommandCreateConversation.EVENT_NAME, {"conv_id": new_convo.id})
        return True


"""
Command: Delete Conversation
"""


class CommandDeleteConversation(CQRSCommand):
    EVENT_NAME = "DELETE_CONVERSATION"

    @staticmethod
    def execute(user_id: str, conv_id: int) -> bool:
        try:    
            convo = _retrieve_convo_by_id(conv_id)
            #retrieve userId for convo from ConvoRepo and match against
            repoInst = ConvoRepo.objects.get(convoId = conv_id)
            if str(user_id) != repoInst.userId:
                return False
            convo.delete()
        except Exception:
            return False

        publish(CommandDeleteConversation.EVENT_NAME, {"conv_id": conv_id})
        return True


"""
Command: Save Message
"""


class CommandSaveMessage(CQRSCommand):
    EVENT_NAME = "SAVE_MESSAGE"

    @staticmethod
    def execute(conv_id: int, message: Message) -> bool:
        """
        Save the message to this conversation's file.

        Args:
            message (Message): Message to be saved.
        """
        try:
            convo = _retrieve_convo_by_id(conv_id)
            _ensure_file_exists(convo.abs_path)
            with open(convo.abs_path, "a") as conv_file:
                conv_file.write(message.serialize())
            convo.time_of_last_message = timezone.now()
            convo.save()
        except Exception:
            return False

        publish(CommandSaveMessage.EVENT_NAME)
        return True
