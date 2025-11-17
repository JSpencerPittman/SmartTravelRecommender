from django.db import models  # type: ignore
from typing import Optional, Any
from django.contrib.auth.hashers import check_password, make_password  # type: ignore


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
    def find_matching_user(
        user_id: Optional[int] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        user_name: Optional[str] = None,
        password: Optional[str] = None,
    ) -> list["AccountModel"]:
        search_query: dict[str, Any] = dict()
        if user_id is not None:
            search_query["id"] = user_id
        if first_name is not None:
            search_query["first_name"] = first_name
        if last_name is not None:
            search_query["last_name"] = last_name
        if user_name is not None:
            search_query["user_name"] = user_name

        accounts = AccountModel.objects.filter(**search_query)

        if password is not None:
            return [
                account
                for account in accounts
                if check_password(password, account.password_hash)
            ]
        else:
            return list(accounts)

    @staticmethod
    def get_current_user(request, debug: bool = False) -> Optional["AccountModel"]:
        if debug:
            return AccountModel.objects.first()
        if "user_id" in request.session:
            user_id = request.session["user_id"]
            matches = AccountModel.find_matching_user(user_id=user_id)
            if len(matches) == 1:
                return matches[0]
        return None
