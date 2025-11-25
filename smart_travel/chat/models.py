from pathlib import Path
from typing import Any, Optional
import hashlib

from accounts.models import AccountModel
from chat.utility.message import Message
from django.db import models  # type: ignore
from django.utils import timezone  # type: ignore


PROJECT_DIR = Path(__file__).parent.parent


class ConversationModel(models.Model):
    MEDIA_DIR = "media/conversations"

    title = models.CharField(max_length=50)
    user = models.ForeignKey(AccountModel, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200)
    time_of_last_message = models.DateTimeField()

    @property
    def abs_path(self) -> Path:
        return Path(PROJECT_DIR) / ConversationModel.MEDIA_DIR / self.file_name

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
