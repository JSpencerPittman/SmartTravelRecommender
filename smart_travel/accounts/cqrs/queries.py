from eda.cqrs import CQRSQuery, CQRSQueryResponse
from accounts.models import AccountModel
from typing import Optional, Any
from django.contrib.auth.hashers import check_password  # type: ignore
from eda.event_dispatcher import publish


"""
Query: Find User
"""


class QueryFindUserResponse(CQRSQueryResponse):
    data: list[AccountModel]


class QueryFindUser(CQRSQuery):
    EVENT_NAME = "FOUND_USER"

    @staticmethod
    def execute(
        user_id: Optional[int] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        user_name: Optional[str] = None,
        password: Optional[str] = None,
    ) -> QueryFindUserResponse:
        search_query: dict[str, Any] = dict()
        if user_id is not None:
            search_query["id"] = user_id
        if first_name is not None:
            search_query["first_name"] = first_name
        if last_name is not None:
            search_query["last_name"] = last_name
        if user_name is not None:
            search_query["user_name"] = user_name

        try:
            accounts = list(AccountModel.objects.filter(**search_query))
        except Exception:
            return QueryFindUserResponse(status=False, data=[])

        if password is not None:
            accounts = [
                acc for acc in accounts if check_password(password, acc.password_hash)
            ]

        publish(QueryFindUser.EVENT_NAME)
        return QueryFindUserResponse(status=True, data=accounts)


"""
Query: Get Current User
"""


class QueryGetCurrentUserResponse(CQRSQueryResponse):
    data: Optional[AccountModel]


class QueryGetCurrentUser(CQRSQuery):
    EVENT_NAME = "FOUND_CURRENT_USER"

    @staticmethod
    def execute(request) -> QueryGetCurrentUserResponse:
        if "user_id" in request.session:
            user_id = request.session["user_id"]
            result = QueryFindUser.execute(user_id=user_id)
            if not result["status"]:
                return QueryGetCurrentUserResponse(status=False, data=None)
            matches = result["data"]
            if len(matches) == 1:

                return QueryGetCurrentUserResponse(status=True, data=matches[0])

        QueryGetCurrentUser.publish_event()
        return QueryGetCurrentUserResponse(status=False, data=None)

    @staticmethod
    def publish_event():
        publish(QueryGetCurrentUser.EVENT_NAME)
