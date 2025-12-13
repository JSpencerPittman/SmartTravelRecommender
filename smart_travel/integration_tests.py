import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from accounts.models import AccountModel
from chat.models import ConversationModel
from chat.utility.message import Message
from django.contrib.auth.hashers import make_password  # type: ignore
from django.test import Client, TestCase  # type: ignore
from django.urls import reverse  # type: ignore
from django.utils import timezone  # type: ignore


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
