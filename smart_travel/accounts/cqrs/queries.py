from eda.cqrs import CQRSQuery, CQRSQueryResponse
from accounts.models import AccountModel
from typing import Optional, Any
from django.contrib.auth.hashers import check_password  # type: ignore
from eda.event_dispatcher import publish_event


class QueryFindUserResponse(CQRSQueryResponse):
    status: bool
    data: list[AccountModel]


class QueryFindUser(CQRSQuery):
    EVENT_NAME = "QUERY_FIND_USER"

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
            return CQRSQueryResponse(status=False, data=[])

        if password is not None:
            accounts = [
                acc for acc in accounts if check_password(password, acc.password_hash)
            ]

        QueryFindUser.publish_event()

        return CQRSQueryResponse(status=True, data=accounts)

    @staticmethod
    def publish_event():
        publish_event(QueryFindUser.EVENT_NAME)
