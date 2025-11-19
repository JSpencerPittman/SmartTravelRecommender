from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import hashlib

from accounts.models import AccountModel 
from django.db import models  # type: ignore
from django.utils import timezone  # type: ignore


PROJECT_DIR = Path(__file__).parent.parent


@dataclass
class Message(object):
    message: str
    is_user: bool

    def serialize(self) -> str:
        """
        Serialize the message.

        Returns:
            str: Serialized message with the proper source label.
        """

        return f"### {'User' if self.is_user else 'Agent'}\n{self.message}\n"

    @classmethod
    def deserialize_messages(cls, raw_contents: list[str]) -> list["Message"]:
        """
        Deserialize a series of messages from the raw contents of a text file.

        Args:
            raw_contents (list[str]): lines of text file to be parsed.

        Returns:
            list[Message]: All parsed messages from the text file.
        """

        def parse_source_label(line: str) -> Optional[bool]:
            """
            A source label is a line above a message's contents indicating who is the source or
            of the message: user or agent.

            A source label must follow the following format:
            ### <User|Agent>

            Args:
                line (str): potential source label to be parsed.

            Returns:
                Optional[bool]: If the line is not a source label, return None. Otherwise,
                return a boolean indicating if the source is the user, if not then it's the
                agent.
            """

            if not line.startswith("### "):
                return None
            parts = line.split("### ")
            if len(parts) != 2 or len(parts[1]) == 0:
                return None
            return parts[1].strip().lower() == "user"

        line_iter = iter(raw_contents)
        messages = []
        is_user = False
        message = ""
        source_label_encountered = False

        while (line := next(line_iter, None)) is not None:
            if (next_is_user := parse_source_label(line)) is not None:
                if len(message) and source_label_encountered:
                    messages.append(Message(message, is_user))
                is_user = next_is_user
                message = ""
                source_label_encountered = True
            else:
                message += line
        # loop terminates before the adding the final message.
        if len(message) and source_label_encountered:
            messages.append(cls(message, is_user))

        return messages


class ConversationModel(models.Model):
    MEDIA_DIR = "media/conversations"

    title = models.CharField(max_length=50)
    user = models.ForeignKey(AccountModel, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200)
    time_of_last_message = models.DateTimeField()

    @property
    def abs_path(self) -> Path:
        return Path(PROJECT_DIR) / ConversationModel.MEDIA_DIR / self.file_name

    @staticmethod
    def create(title: str, user: AccountModel) -> "ConversationModel":
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

        return ConversationModel.objects.create(
            title=title,
            user=user,
            file_name=create_unique_filename(title, user.user_name),
            time_of_last_message=timezone.now(),
        )

    @staticmethod
    def find_conversation(
        user: Optional[AccountModel] = None, chat_id: Optional[int] = None,
        limit: Optional[int] = 5
    ) -> list["ConversationModel"]:
        """
        Find conversations matching the provided filters.

        Args:
            user (Optional[AccountModel], optional): Select conversations only from the provided
                user. Defaults to None.
            chat_id (Optional[int], optional): Select conversation by its ID. Defaults to None.

        Returns:
            QuerySet: matched conversations.
        """

        search_query: dict[str, Any] = dict()
        if user is not None:
            search_query["user"] = user
        if chat_id is not None:
            search_query["id"] = chat_id

        print("SEARCH QUERY:", search_query)

        
        if chat_id is None:
            return list(ConversationModel.objects.filter(**search_query)
                        .order_by('-time_of_last_message')
                        [:limit]
                        )
        else:
            return list(ConversationModel.objects.filter(**search_query))
        

    def retrieve_messages(self) -> list[Message]:
        """
        Retrieve messages from this conversation's file.

        Note:
            If the file does not exist prior, it will be created.

        Returns:
            list[Message]: Loaded messages.
        """

        self._ensure_file_exists()
        with open(self.abs_path, "r") as conv_file:
            return Message.deserialize_messages(conv_file.readlines())

    def save_message(self, message: Message):
        """
        Save the message to this conversation's file.

        Args:
            message (Message): Message to be saved.
        """

        self._ensure_file_exists()
        with open(self.abs_path, "a") as conv_file:
            conv_file.write(message.serialize())
        self.time_of_last_message = timezone.now()
        self.save()

    def _ensure_file_exists(self):
        """
        Ensure this conversation's file exists. If it does not, then create the
        requisite directories with the conversation file.
        """

        if self.abs_path.exists():
            return
        if not self.abs_path.parent.exists():
            self.abs_path.parent.mkdir(parents=True)
        self.abs_path.touch()
