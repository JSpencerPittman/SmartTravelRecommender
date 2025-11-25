from django.db import models  # type: ignore
from typing import Optional
from django.contrib.auth.hashers import make_password  # type: ignore


class AccountModel(models.Model):
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    user_name = models.CharField(max_length=25)
    password_hash = models.CharField(max_length=255)

    @staticmethod
    def create(
        first_name: str, last_name: str, user_name: str, password: str
    ) -> "AccountModel":
        return AccountModel.objects.create(
            first_name=first_name,
            last_name=last_name,
            user_name=user_name,
            password_hash=make_password(password),
        )

    @staticmethod
    def get_current_user(request, debug: bool = False) -> Optional["AccountModel"]:
        if debug:
            return AccountModel.objects.first()
        if "user_id" in request.session:
            user_id = request.session["user_id"]
            from accounts.cqrs.queries import QueryFindUser

            result = QueryFindUser.execute(user_id=user_id)
            if not result["status"]:
                return None
            matches = result["data"]
            if len(matches) == 1:
                return matches[0]

        return None
