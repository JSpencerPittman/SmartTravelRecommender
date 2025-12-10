from pathlib import Path
from typing import Any, Optional

from accounts.models import AccountModel
from chat.models import ConversationModel
from eda.cqrs import CQRSQuery, CQRSQueryResponse
from eda.event_dispatcher import publish
from chat.utility.message import Message

PROJECT_DIR = Path(__file__).parent.parent

"""
Auxillary
"""


def _ensure_file_exists(abs_path: Path):
    """
    Ensure this conversation's file exists. If it does not, then create the
    requisite directories with the conversation file.
    """

    if abs_path.exists():
        return
    if not abs_path.parent.exists():
        abs_path.parent.mkdir(parents=True)
    abs_path.touch()


def _retrieve_convo_by_id(conv_id: int) -> ConversationModel:
    result = QueryFindConversation.execute(chat_id=conv_id)
    assert result["status"]
    assert len(result["data"]) > 0
    return result["data"][0]


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


"""
Query: Retrieve Messages
"""


class QueryRetrieveMessagesResponse(CQRSQueryResponse):
    title: str
    data: list[Message]


class QueryRetrieveMessages(CQRSQuery):
    EVENT_NAME = "RETRIEVED_MESSAGES"

    @staticmethod
    def execute(conv_id: int) -> QueryRetrieveMessagesResponse:
        """
        Retrieve messages from this conversation's file.

        Note:
            If the file does not exist prior, it will be created.

        Returns:
            list[Message]: Loaded messages.
        """

        try:
            convo = _retrieve_convo_by_id(conv_id)
            _ensure_file_exists(convo.abs_path)
            with open(convo.abs_path, "r") as conv_file:
                messages = Message.deserialize_messages(conv_file.readlines())
        except Exception:
            return QueryRetrieveMessagesResponse(status=False, title="", data=[])

        publish(QueryRetrieveMessages.EVENT_NAME)
        return QueryRetrieveMessagesResponse(
            status=True, title=convo.title, data=messages
        )
