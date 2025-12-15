from pathlib import Path

from accounts.models import AccountModel
from django.db import models  # type: ignore

PROJECT_DIR = Path(__file__).parent.parent


class ConvoRepo(models.Model):

    userId = models.CharField(max_length = 50)
    convoId = models.CharField(max_length = 50)

    @classmethod
    def _add_Repo_inst(cls, user_id : str, conv_id : str) -> bool:
        try:
            cls.objects.create(
                    userId = user_id,
                    convoId = conv_id,
                )
            return True
        except Exception:
            return  False

    @classmethod
    def _delete_Repo_inst(cls, conv_id: str) -> bool:
        try:
            repoInst =  list(cls.objects.filter(convoId = conv_id))[0]
            repoInst.delete()
            return True 
        except Exception:
            return False


class ConversationModel(models.Model):
    MEDIA_DIR = "media/conversations"

    title = models.CharField(max_length=50)
    #user = models.ForeignKey(AccountModel, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200)
    time_of_last_message = models.DateTimeField()

    @property
    def abs_path(self) -> Path:
        return Path(PROJECT_DIR) / ConversationModel.MEDIA_DIR / self.file_name
