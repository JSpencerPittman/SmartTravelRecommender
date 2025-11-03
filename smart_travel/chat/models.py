from django.db import models
from typing import Optional
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent


class User(models.Model):
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)


class Conversation(models.Model):
    MEDIA_DIR = "media/conversations"

    title = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200)

    @property
    def abs_path(self) -> Path:
        return Path(PROJECT_DIR) / Conversation.MEDIA_DIR / self.file_name

    def retrieve(self) -> str:
        self._ensure_file_exists()
        return self.abs_path.read_bytes().decode()

    def add_message(self, text: str):
        self._ensure_file_exists()
        with open(self.abs_path, "a") as conv_file:
            conv_file.write(text)

    def _ensure_file_exists(self):
        if self.abs_path.exists():
            return
        if not self.abs_path.parent.exists():
            self.abs_path.parent.mkdir(parents=True)
        self.abs_path.touch()
