from pathlib import Path
from typing import Any, Optional

from accounts.models import AccountModel
from chat.models import ConversationModel
from eda.cqrs import CQRSQuery, CQRSQueryResponse
from eda.event_dispatcher import publish

PROJECT_DIR = Path(__file__).parent.parent

"""
Query: Find Conversation
"""


class QueryFindConversationResponse(CQRSQueryResponse):
    data: list[ConversationModel]


class QueryFindConversation(CQRSQuery):
    EVENT_NAME = "FOUND_CONVERSATION"

    @staticmethod
    def execute(
        user: Optional[AccountModel] = None,
        chat_id: Optional[int] = None,
        limit: Optional[int] = 5,
    ) -> QueryFindConversationResponse:
        """
        Find conversations matching the provided filters.

        Args:
            user (Optional[AccountModel], optional): Select conversations only from the provided
                user. Defaults to None.
            chat_id (Optional[int], optional): Select conversation by its ID. Defaults to None.

        Returns:
            QuerySet: matched conversations.
        """

        search_query: dict[str, Any] = dict()
        if user is not None:
            search_query["user"] = user
        if chat_id is not None:
            search_query["id"] = chat_id

        if chat_id is None:
            matches = list(
                ConversationModel.objects.filter(**search_query).order_by(
                    "-time_of_last_message"
                )[:limit]
            )
        else:
            matches = list(ConversationModel.objects.filter(**search_query))

        publish(QueryFindConversation.EVENT_NAME)
        return QueryFindConversationResponse(status=True, data=matches)
