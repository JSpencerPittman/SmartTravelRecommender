from django.db import models


class AccountModel(models.Model):
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    user_name = models.CharField(max_length=25)
    password_hash = models.CharField(max_length=255)
