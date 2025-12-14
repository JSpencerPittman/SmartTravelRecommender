import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from unittest.mock import patch

from accounts.models import AccountModel
from chat.models import ConversationModel
from chat.utility.message import Message
from chat.views import event_handler__new_conversation, event_handler__new_user_message
from django.contrib.auth.hashers import make_password  # type: ignore
from django.test import Client, TestCase, TransactionTestCase  # type: ignore
from django.urls import reverse  # type: ignore
from django.utils import timezone  # type: ignore
from eda.event_dispatcher import get_event, subscribe

MOCK__PROMPT_COMPLETION__RET_VAL = None


class MockedChatbot:
    def __init__(self, *_, **__):
        self._client = 1  # Not None

    def initialize_session(self) -> bool:
        return False

    def prompt_completion(self, _: list[Message]) -> Optional[str]:
        return MOCK__PROMPT_COMPLETION__RET_VAL


@dataclass
class MockRequest:
    session: Any


"""
Event Handling
"""

EVENT_LISTENER_NAME = "TESTING"
EVENT_HANDLER_CALLBACKS = {
    "NEW_CONVERSATION": event_handler__new_conversation,
    "NEW_USER_MESSAGE": event_handler__new_user_message,
}
for event in EVENT_HANDLER_CALLBACKS.keys():
    subscribe(EVENT_LISTENER_NAME, event)


def poll_event(name: Optional[str] = None, timeout: int = 2) -> Any:
    start = time.time()
    while (event := get_event(EVENT_LISTENER_NAME)) is None or (
        name is not None and event["name"] != name
    ):
        if time.time() - start > timeout:
            break
        continue
    return event


def poll_and_handle_event(request, name: Optional[str] = None):
    event = poll_event(name)
    if event["name"] in EVENT_HANDLER_CALLBACKS:
        EVENT_HANDLER_CALLBACKS[event["name"]](request, event)


def clear_events():
    while get_event(EVENT_LISTENER_NAME) is not None:
        continue


"""
Tests
"""


class UserAuthenticationWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_complete_signup_and_login_workflow(self):
        signup_data = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "user_name": "alicejohnson",
            "password": "securepassword123",
            "confirm_password": "securepassword123",
        }
        response = self.client.post(reverse("signup"), data=signup_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts", response.url)

        self.assertTrue(AccountModel.objects.filter(user_name="alicejohnson").exists())

        login_data = {"user_id": "alicejohnson", "password": "securepassword123"}
        response = self.client.post("/accounts/", data=login_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("chat"))
        self.assertIn("user_id", self.client.session)

    def test_signup_login_logout_workflow(self):

        signup_data = {
            "first_name": "Bob",
            "last_name": "Smith",
            "user_name": "bobsmith",
            "password": "mypassword123",
            "confirm_password": "mypassword123",
        }
        self.client.post(reverse("signup"), data=signup_data)

        login_data = {"user_id": "bobsmith", "password": "mypassword123"}
        self.client.post(reverse("login"), data=login_data)
        self.assertIn("user_id", self.client.session)

        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("user_id", self.client.session)

    def test_failed_login_attempt(self):
        AccountModel.objects.create(
            first_name="Test",
            last_name="User",
            user_name="testuser",
            password_hash=make_password("correctpassword"),
        )

        login_data = {"user_id": "testuser", "password": "wrongpassword"}
        response = self.client.post(reverse("login"), data=login_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("user_id", self.client.session)

    def test_access_protected_page_without_login(self):
        response = self.client.get(reverse("chat"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts", response.url)


class ConversationManagementWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = AccountModel.objects.create(
            first_name="Test",
            last_name="User",
            user_name="testuser",
            password_hash=make_password("testpass123"),
        )

        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_and_select_conversation_workflow(self):
        response = self.client.post(
            reverse("chat") + "operation/new_chat", data={"title": "Trip to Tokyo"}
        )
        self.assertEqual(response.status_code, 302)

        conversation = ConversationModel.objects.get(title="Trip to Tokyo")
        self.assertEqual(conversation.user, self.user)

        response = self.client.post(
            reverse("chat") + f"operation/select_chat/{conversation.id}"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("conv_id"), conversation.id)

    def test_create_multiple_conversations(self):
        titles = ["Paris Trip", "Rome Adventure", "London Visit"]

        for title in titles:
            self.client.post(
                reverse("chat") + "operation/new_chat", data={"title": title}
            )

        user_conversations = ConversationModel.objects.filter(user=self.user)
        self.assertEqual(user_conversations.count(), 3)

        conv_titles = [conv.title for conv in user_conversations]
        for title in titles:
            self.assertIn(title, conv_titles)

    def test_delete_conversation_workflow(self):
        conversation = ConversationModel.objects.create(
            title="Temporary Chat",
            user=self.user,
            file_name="temp.txt",
            time_of_last_message=timezone.now(),
        )

        conv_id = conversation.id
        self.assertTrue(ConversationModel.objects.filter(id=conv_id).exists())

        response = self.client.post(
            reverse("chat") + f"operation/delete_chat/{conv_id}"
        )
        self.assertEqual(response.status_code, 302)

    def test_switch_between_conversations(self):
        conv1 = ConversationModel.objects.create(
            title="First Chat",
            user=self.user,
            file_name="first.txt",
            time_of_last_message=timezone.now(),
        )
        conv2 = ConversationModel.objects.create(
            title="Second Chat",
            user=self.user,
            file_name="second.txt",
            time_of_last_message=timezone.now(),
        )

        self.client.post(reverse("chat") + f"operation/select_chat/{conv1.id}")
        self.assertEqual(self.client.session.get("conv_id"), conv1.id)

        self.client.post(reverse("chat") + f"operation/select_chat/{conv2.id}")
        self.assertEqual(self.client.session.get("conv_id"), conv2.id)


class EndToEndUserJourneyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_complete_user_journey(self):
        signup_data = {
            "first_name": "Emma",
            "last_name": "Wilson",
            "user_name": "emmawilson",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }
        response = self.client.post(reverse("signup"), data=signup_data)
        self.assertEqual(response.status_code, 302)

        login_data = {"user_id": "emmawilson", "password": "securepass123"}
        response = self.client.post(reverse("login"), data=login_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("user_id", self.client.session)

        response = self.client.get(reverse("chat"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("chat") + "operation/new_chat", data={"title": "Barcelona Trip"}
        )
        self.assertEqual(response.status_code, 302)

        user = AccountModel.objects.get(user_name="emmawilson")
        conversation = ConversationModel.objects.get(title="Barcelona Trip", user=user)
        self.assertIsNotNone(conversation)

        response = self.client.post(
            reverse("chat") + f"operation/select_chat/{conversation.id}"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get("conv_id"), conversation.id)

        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("user_id", self.client.session)


class MessagePersistenceWorkflowTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch.object(
        ConversationModel,
        "abs_path",
        new_callable=lambda: property(
            lambda self: Path(tempfile.gettempdir()) / self.file_name
        ),
    )
    def test_save_and_retrieve_messages_workflow(self, mock_abs_path):
        from chat.cqrs.commands import CommandSaveMessage
        from chat.cqrs.queries import QueryRetrieveMessages

        user = AccountModel.objects.create(
            first_name="Test",
            last_name="User",
            user_name="testuser",
            password_hash=make_password("testpass"),
        )

        conversation = ConversationModel.objects.create(
            title="Test Conversation",
            user=user,
            file_name="test_messages.txt",
            time_of_last_message=timezone.now(),
        )

        messages = [
            Message(
                message="What are the best places to visit in Paris?", is_user=True
            ),
            Message(
                message="Paris has many wonderful attractions including the Eiffel Tower, Louvre Museum, and Notre-Dame Cathedral.",
                is_user=False,
            ),
            Message(message="What about restaurants?", is_user=True),
            Message(
                message="I recommend trying Le Jules Verne at the Eiffel Tower or L'Ambroisie in Le Marais.",
                is_user=False,
            ),
        ]

        file_path = Path(tempfile.gettempdir()) / "test_messages.txt"

        try:
            for msg in messages:
                result = CommandSaveMessage.execute(
                    conv_id=conversation.id, message=msg
                )
                self.assertTrue(result)

            self.assertTrue(file_path.exists())

            content = file_path.read_text()
            self.assertIn("### User", content)
            self.assertIn("### Agent", content)
            self.assertIn("What are the best places to visit in Paris?", content)
            self.assertIn("Eiffel Tower", content)

            raw_lines = content.split("\n")
            raw_lines = [line + "\n" for line in raw_lines if line]

            retrieved_messages = Message.deserialize_messages(raw_lines)
            self.assertEqual(len(retrieved_messages), 4)
            self.assertTrue(retrieved_messages[0].is_user)
            self.assertFalse(retrieved_messages[1].is_user)
            self.assertTrue(retrieved_messages[2].is_user)
            self.assertFalse(retrieved_messages[3].is_user)
        finally:
            if file_path.exists():
                file_path.unlink()


class MultiUserIsolationTests(TestCase):
    def setUp(self):
        self.client1 = Client()
        self.client2 = Client()

        self.user1 = AccountModel.objects.create(
            first_name="User",
            last_name="One",
            user_name="user1",
            password_hash=make_password("pass1"),
        )
        self.user2 = AccountModel.objects.create(
            first_name="User",
            last_name="Two",
            user_name="user2",
            password_hash=make_password("pass2"),
        )

        session1 = self.client1.session
        session1["user_id"] = self.user1.id
        session1.save()

        session2 = self.client2.session
        session2["user_id"] = self.user2.id
        session2.save()

    def test_users_have_separate_conversations(self):
        self.client1.post(
            reverse("chat") + "operation/new_chat", data={"title": "User1 Trip"}
        )

        self.client2.post(
            reverse("chat") + "operation/new_chat", data={"title": "User2 Trip"}
        )

        user1_conversations = ConversationModel.objects.filter(user=self.user1)
        user2_conversations = ConversationModel.objects.filter(user=self.user2)

        self.assertEqual(user1_conversations.count(), 1)
        self.assertEqual(user2_conversations.count(), 1)
        self.assertEqual(user1_conversations.first().title, "User1 Trip")
        self.assertEqual(user2_conversations.first().title, "User2 Trip")

    def test_user_cannot_access_other_user_conversation(self):
        from chat.cqrs.commands import CommandDeleteConversation

        conversation = ConversationModel.objects.create(
            title="User1 Private Chat",
            user=self.user1,
            file_name="private.txt",
            time_of_last_message=timezone.now(),
        )

        result = CommandDeleteConversation.execute(
            user_id=self.user2.id, conv_id=conversation.id
        )
        self.assertFalse(result)

        self.assertTrue(ConversationModel.objects.filter(id=conversation.id).exists())


class DataIntegrityTests(TestCase):
    def test_cascade_delete_conversations_on_user_delete(self):
        user = AccountModel.objects.create(
            first_name="Delete",
            last_name="Me",
            user_name="deleteme",
            password_hash=make_password("pass"),
        )

        conv1 = ConversationModel.objects.create(
            title="Conversation 1",
            user=user,
            file_name="conv1.txt",
            time_of_last_message=timezone.now(),
        )
        conv2 = ConversationModel.objects.create(
            title="Conversation 2",
            user=user,
            file_name="conv2.txt",
            time_of_last_message=timezone.now(),
        )

        conv1_id = conv1.id
        conv2_id = conv2.id

        user.delete()

        with self.assertRaises(ConversationModel.DoesNotExist):
            ConversationModel.objects.get(id=conv1_id)
        with self.assertRaises(ConversationModel.DoesNotExist):
            ConversationModel.objects.get(id=conv2_id)


class AgentConversationWorkflowTests(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        clear_events()

    @patch("chat.views.chatbot", new_callable=MockedChatbot)
    def test_complete_agent_conversation_workflow(self, mock_chatbot):
        global MOCK__PROMPT_COMPLETION__RET_VAL

        signup_data = {
            "first_name": "Travel",
            "last_name": "Enthusiast",
            "user_name": "traveler",
            "password": "password123",
            "confirm_password": "password123",
        }
        self.client.post(reverse("signup"), data=signup_data)

        login_data = {"user_id": "traveler", "password": "password123"}
        self.client.post(reverse("login"), data=login_data)

        self.client.post(
            reverse("chat") + "operation/new_chat", data={"title": "Europe Trip"}
        )

        user = AccountModel.objects.get(user_name="traveler")
        conversation = ConversationModel.objects.get(title="Europe Trip", user=user)
        if conversation.abs_path.exists():
            os.remove(conversation.abs_path)

        self.client.post(reverse("chat") + f"operation/select_chat/{conversation.id}")

        try:
            MOCK__PROMPT_COMPLETION__RET_VAL = (
                "Paris is a beautiful city with the Eiffel Tower, Louvre, and more!"
            )
            self.client.post(
                reverse("operation__new_user_message"),
                data={"message": "Tell me about Paris"},
            )
            poll_and_handle_event(MockRequest(self.client.session), "NEW_USER_MESSAGE")
            poll_event("NEW_AGENT_MESSAGE")

            content = conversation.abs_path.read_text()

            MOCK__PROMPT_COMPLETION__RET_VAL = (
                "You should visit in spring (April-May) or fall (September-October)."
            )
            self.client.post(
                reverse("operation__new_user_message"),
                data={"message": "When should I visit?"},
            )
            poll_and_handle_event(MockRequest(self.client.session), "NEW_USER_MESSAGE")
            poll_event("NEW_AGENT_MESSAGE")

            if conversation.abs_path.exists():
                content = conversation.abs_path.read_text()
                self.assertIn("### User\nTell me about Paris\n", content)
                self.assertIn("Paris is a beautiful city", content)
                self.assertIn("### User\nWhen should I visit?\n", content)
                self.assertIn("spring (April-May)", content)

            self.client.post(reverse("logout"))
            self.assertNotIn("user_id", self.client.session)

        finally:
            if conversation.abs_path.exists():
                conversation.abs_path.unlink()
            MOCK__PROMPT_COMPLETION__RET_VAL = None

    @patch("chat.views.chatbot", new_callable=MockedChatbot)
    def test_user_receives_agent_response(self, mock_chatbot):
        global MOCK__PROMPT_COMPLETION__RET_VAL

        user = AccountModel.objects.create(
            first_name="Test",
            last_name="User",
            user_name="testuser",
            password_hash=make_password("testpass"),
        )

        session = self.client.session
        session["user_id"] = user.id
        session.save()

        conversation = ConversationModel.objects.create(
            title="Italy Trip",
            user=user,
            file_name="italy_trip.txt",
            time_of_last_message=timezone.now(),
        )
        if conversation.abs_path.exists():
            os.remove(conversation.abs_path)

        session["conv_id"] = conversation.id
        session.save()

        try:
            MOCK__PROMPT_COMPLETION__RET_VAL = (
                "Rome has the Colosseum, Vatican City, and Trevi Fountain."
            )

            response = self.client.post(
                reverse("operation__new_user_message"),
                data={"message": "What are the best places in Rome?"},
            )
            poll_and_handle_event(MockRequest(self.client.session), "NEW_USER_MESSAGE")
            self.assertEqual(response.status_code, 302)
            poll_event("NEW_AGENT_MESSAGE")

            self.assertTrue(conversation.abs_path.exists())

            content = conversation.abs_path.read_text()
            self.assertIn("### User", content)
            self.assertIn("What are the best places in Rome?", content)
            self.assertIn("### Agent", content)
            self.assertIn("Colosseum", content)
            self.assertIn("Vatican City", content)

            messages = Message.deserialize_messages(
                [line + "\n" for line in content.split("\n") if line]
            )
            user_messages = [m for m in messages if m.is_user]
            agent_messages = [m for m in messages if not m.is_user]

            self.assertEqual(len(user_messages), 1)
            self.assertEqual(len(agent_messages), 1)
            self.assertIn("What are the best places in Rome?", user_messages[0].message)
            self.assertIn("Colosseum", agent_messages[0].message)

        finally:
            if conversation.abs_path.exists():
                conversation.abs_path.unlink()
            MOCK__PROMPT_COMPLETION__RET_VAL = None

    @patch("chat.views.chatbot", new_callable=MockedChatbot)
    def test_multi_turn_conversation_persistence(self, mock_chatbot):
        global MOCK__PROMPT_COMPLETION__RET_VAL

        user = AccountModel.objects.create(
            first_name="Test",
            last_name="User",
            user_name="testuser",
            password_hash=make_password("testpass"),
        )

        session = self.client.session
        session["user_id"] = user.id
        session.save()

        conversation = ConversationModel.objects.create(
            title="Japan Trip",
            user=user,
            file_name="japan_trip.txt",
            time_of_last_message=timezone.now(),
        )
        if conversation.abs_path.exists():
            os.remove(conversation.abs_path)

        session["conv_id"] = conversation.id
        session.save()

        try:
            messages_to_send = [
                (
                    "What should I see in Tokyo?",
                    "Tokyo has Shibuya, Shinjuku, and Senso-ji Temple.",
                ),
                (
                    "What about Kyoto?",
                    "Kyoto is famous for temples like Kinkaku-ji and Fushimi Inari.",
                ),
                (
                    "Best time to visit?",
                    "March-May for cherry blossoms or October-November for fall colors.",
                ),
            ]

            for user_msg, agent_response in messages_to_send:
                MOCK__PROMPT_COMPLETION__RET_VAL = agent_response
                self.client.post(
                    reverse("operation__new_user_message"),
                    data={"message": user_msg},
                )
                poll_and_handle_event(
                    MockRequest(self.client.session), "NEW_USER_MESSAGE"
                )
                poll_event("NEW_AGENT_MESSAGE")

            if conversation.abs_path.exists():
                content = conversation.abs_path.read_text()

                for user_msg, agent_response in messages_to_send:
                    self.assertIn(user_msg, content)
                    self.assertIn(agent_response, content)

                messages = Message.deserialize_messages(
                    [line + "\n" for line in content.split("\n") if line]
                )
                self.assertEqual(len(messages), 6)
                self.assertEqual(len([m for m in messages if m.is_user]), 3)
                self.assertEqual(len([m for m in messages if not m.is_user]), 3)

        finally:
            if conversation.abs_path.exists():
                conversation.abs_path.unlink()
            MOCK__PROMPT_COMPLETION__RET_VAL = None
