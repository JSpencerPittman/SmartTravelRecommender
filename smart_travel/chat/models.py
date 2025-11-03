from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from django.db import models

PROJECT_DIR = Path(__file__).parent.parent


class User(models.Model):
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)


class Conversation(models.Model):
    @dataclass
    class Message(object):
        message: str
        is_user: bool

    MEDIA_DIR = "media/conversations"

    title = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200)

    @property
    def abs_path(self) -> Path:
        return Path(PROJECT_DIR) / Conversation.MEDIA_DIR / self.file_name

    def retrieve(self) -> list[Message]:
        def parse_divider(line: str) -> Optional[bool]:
            """
            A divider line must follow the following format:
            ### <USER|Agent>
            """

            if not line.startswith("### "):
                return None
            parts = line.split("### ")
            if len(parts) != 2 or len(parts[1]) == 0:
                return None
            return parts[1].strip().lower() == "user"

        self._ensure_file_exists()

        with open(self.abs_path, "r") as conv_file:
            line_iter = iter(conv_file.readlines())

        messages = []
        is_user = False
        message = ""

        while (line := next(line_iter, None)) is not None:
            if (next_is_user := parse_divider(line)) is not None:
                if len(message):
                    messages.append(Conversation.Message(message, is_user))
                is_user = next_is_user
                message = ""
            else:
                message += line
        if len(message):
            messages.append(Conversation.Message(message, is_user))

        return messages

    def add_message(self, text: str):
        self._ensure_file_exists()
        text = f"\n### User\n{text}"
        with open(self.abs_path, "a") as conv_file:
            conv_file.write(text)

    def _ensure_file_exists(self):
        if self.abs_path.exists():
            return
        if not self.abs_path.parent.exists():
            self.abs_path.parent.mkdir(parents=True)
        self.abs_path.touch()
