from django.db import models


class User(models.Model):
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)


class Conversation(models.Model):
    title = models.CharField(max_length=50)
    history_file_path = models.FileField(upload_to="media/conversations")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
