from pathlib import Path

from accounts.models import AccountModel
from django.db import models  # type: ignore

PROJECT_DIR = Path(__file__).parent.parent


class ConvoRepo(models.Model):

    userId = models.CharField(max_length = 50)
    convoId = models.CharField(max_length = 50)



class ConversationModel(models.Model):
    MEDIA_DIR = "media/conversations"

    title = models.CharField(max_length=50)
    #user = models.ForeignKey(AccountModel, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200)
    time_of_last_message = models.DateTimeField()

    @property
    def abs_path(self) -> Path:
        return Path(PROJECT_DIR) / ConversationModel.MEDIA_DIR / self.file_name
