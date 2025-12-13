from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from accounts.models import AccountModel
from .models import ConversationModel
from .forms import NewChatForm, MessageForm
from .utility.message import Message
from .cqrs.commands import CommandCreateConversation, CommandDeleteConversation, CommandSaveMessage
from .cqrs.queries import QueryFindConversation, QueryRetrieveMessages


class ConversationModelTests(TestCase):
    def setUp(self):
        self.user = AccountModel.objects.create(
            first_name='Test',
            last_name='User',
            user_name='testuser',
            password_hash=make_password('testpass')
        )
        self.conversation_data = {
            'title': 'Test Conversation',
            'user': self.user,
            'file_name': 'test_conv.txt',
            'time_of_last_message': timezone.now()
        }

    def test_create_conversation(self):
        conversation = ConversationModel.objects.create(**self.conversation_data)
        self.assertEqual(conversation.title, 'Test Conversation')
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.file_name, 'test_conv.txt')
        self.assertIsNotNone(conversation.time_of_last_message)
        self.assertIsNotNone(conversation.id)

    def test_conversation_user_foreign_key(self):
        conversation = ConversationModel.objects.create(**self.conversation_data)
        self.assertEqual(conversation.user.user_name, 'testuser')

    def test_conversation_cascade_delete(self):
        conversation = ConversationModel.objects.create(**self.conversation_data)
        conv_id = conversation.id
        self.user.delete()
        with self.assertRaises(ConversationModel.DoesNotExist):
            ConversationModel.objects.get(id=conv_id)

    def test_abs_path_property(self):
        conversation = ConversationModel.objects.create(**self.conversation_data)
        expected_path = Path(conversation._meta.app_config.path).parent / ConversationModel.MEDIA_DIR / 'test_conv.txt'
        self.assertEqual(conversation.abs_path, expected_path)

    def test_title_max_length(self):
        long_title = 'A' * 50
        conversation = ConversationModel.objects.create(
            title=long_title,
            user=self.user,
            file_name='test.txt',
            time_of_last_message=timezone.now()
        )
        self.assertEqual(len(conversation.title), 50)

    def test_update_conversation(self):
        conversation = ConversationModel.objects.create(**self.conversation_data)
        new_time = timezone.now()
        conversation.time_of_last_message = new_time
        conversation.save()
        updated = ConversationModel.objects.get(id=conversation.id)
        self.assertEqual(updated.time_of_last_message, new_time)


class NewChatFormTests(TestCase):
    def test_valid_form(self):
        form_data = {'title': 'My Trip to Paris'}
        form = NewChatForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_title(self):
        form_data = {}
        form = NewChatForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_title_max_length(self):
        form_data = {'title': 'A' * 51}
        form = NewChatForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_empty_title(self):
        form_data = {'title': ''}
        form = NewChatForm(data=form_data)
        self.assertFalse(form.is_valid())


class MessageFormTests(TestCase):
    def test_valid_form(self):
        form_data = {'message': 'What are some good restaurants in Rome?'}
        form = MessageForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_message(self):
        form_data = {}
        form = MessageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('message', form.errors)

    def test_message_max_length(self):
        form_data = {'message': 'A' * 201}
        form = MessageForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_empty_message(self):
        form_data = {'message': ''}
        form = MessageForm(data=form_data)
        self.assertFalse(form.is_valid())


class MessageUtilityTests(TestCase):
    def test_message_creation(self):
        msg = Message(message='Hello', is_user=True)
        self.assertEqual(msg.message, 'Hello')
        self.assertTrue(msg.is_user)

    def test_serialize_user_message(self):
        msg = Message(message='Hello World', is_user=True)
        serialized = msg.serialize()
        self.assertEqual(serialized, '### User\nHello World\n')

    def test_serialize_agent_message(self):
        msg = Message(message='Hello User', is_user=False)
        serialized = msg.serialize()
        self.assertEqual(serialized, '### Agent\nHello User\n')

    def test_deserialize_single_message(self):
        raw_contents = ['### User\n', 'Hello World\n']
        messages = Message.deserialize_messages(raw_contents)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, 'Hello World\n')
        self.assertTrue(messages[0].is_user)

    def test_deserialize_multiple_messages(self):
        raw_contents = [
            '### User\n',
            'Hello\n',
            '### Agent\n',
            'Hi there!\n',
            '### User\n',
            'How are you?\n'
        ]
        messages = Message.deserialize_messages(raw_contents)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0].message, 'Hello\n')
        self.assertTrue(messages[0].is_user)
        self.assertEqual(messages[1].message, 'Hi there!\n')
        self.assertFalse(messages[1].is_user)
        self.assertEqual(messages[2].message, 'How are you?\n')
        self.assertTrue(messages[2].is_user)

    def test_deserialize_multiline_message(self):
        raw_contents = [
            '### User\n',
            'Line 1\n',
            'Line 2\n',
            'Line 3\n',
            '### Agent\n',
            'Response\n'
        ]
        messages = Message.deserialize_messages(raw_contents)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].message, 'Line 1\nLine 2\nLine 3\n')

    def test_deserialize_empty_list(self):
        messages = Message.deserialize_messages([])
        self.assertEqual(len(messages), 0)

    def test_deserialize_invalid_format(self):
        raw_contents = ['Random text\n', 'More text\n']
        messages = Message.deserialize_messages(raw_contents)
        self.assertEqual(len(messages), 0)


class CommandCreateConversationTests(TestCase):
    def setUp(self):
        self.user = AccountModel.objects.create(
            first_name='Test',
            last_name='User',
            user_name='testuser',
            password_hash=make_password('testpass')
        )

    def test_create_conversation_command(self):
        result = CommandCreateConversation.execute(
            title='Paris Trip',
            user=self.user
        )
        self.assertTrue(result)

        conversation = ConversationModel.objects.get(title='Paris Trip', user=self.user)
        self.assertEqual(conversation.title, 'Paris Trip')
        self.assertEqual(conversation.user, self.user)
        self.assertIsNotNone(conversation.file_name)

    def test_unique_file_names(self):
        result1 = CommandCreateConversation.execute(title='Trip 1', user=self.user)
        self.assertTrue(result1)

        result2 = CommandCreateConversation.execute(title='Trip 2', user=self.user)
        self.assertTrue(result2)

        conv1 = ConversationModel.objects.get(title='Trip 1', user=self.user)
        conv2 = ConversationModel.objects.get(title='Trip 2', user=self.user)
        self.assertNotEqual(conv1.file_name, conv2.file_name)


class CommandDeleteConversationTests(TestCase):
    def setUp(self):
        self.user = AccountModel.objects.create(
            first_name='Test',
            last_name='User',
            user_name='testuser',
            password_hash=make_password('testpass')
        )
        self.other_user = AccountModel.objects.create(
            first_name='Other',
            last_name='User',
            user_name='otheruser',
            password_hash=make_password('testpass')
        )
        self.conversation = ConversationModel.objects.create(
            title='Test Chat',
            user=self.user,
            file_name='test.txt',
            time_of_last_message=timezone.now()
        )

    def test_delete_conversation_valid_user(self):
        conv_id = self.conversation.id
        result = CommandDeleteConversation.execute(
            user_id=self.user.id,
            conv_id=conv_id
        )
        self.assertTrue(result)

        with self.assertRaises(ConversationModel.DoesNotExist):
            ConversationModel.objects.get(id=conv_id)

    def test_delete_conversation_wrong_user(self):
        conv_id = self.conversation.id
        result = CommandDeleteConversation.execute(
            user_id=self.other_user.id,
            conv_id=conv_id
        )
        self.assertFalse(result)
        self.assertTrue(ConversationModel.objects.filter(id=conv_id).exists())


class CommandSaveMessageTests(TestCase):
    def setUp(self):
        self.user = AccountModel.objects.create(
            first_name='Test',
            last_name='User',
            user_name='testuser',
            password_hash=make_password('testpass')
        )
        self.conversation = ConversationModel.objects.create(
            title='Test Chat',
            user=self.user,
            file_name='test_messages.txt',
            time_of_last_message=timezone.now()
        )
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch.object(ConversationModel, 'abs_path', new_callable=lambda: property(lambda self: Path(tempfile.gettempdir()) / self.file_name))
    def test_save_single_message(self, mock_abs_path):
        message = Message(message='Hello', is_user=True)
        result = CommandSaveMessage.execute(
            conv_id=self.conversation.id,
            message=message
        )
        self.assertTrue(result)

        file_path = Path(tempfile.gettempdir()) / 'test_messages.txt'
        if file_path.exists():
            content = file_path.read_text()
            self.assertIn('### User\nHello\n', content)
            file_path.unlink()

    @patch.object(ConversationModel, 'abs_path', new_callable=lambda: property(lambda self: Path(tempfile.gettempdir()) / self.file_name))
    def test_save_multiple_messages(self, mock_abs_path):
        file_path = Path(tempfile.gettempdir()) / 'test_messages.txt'

        try:
            messages = [
                Message(message='Hello', is_user=True),
                Message(message='Hi there', is_user=False),
                Message(message='How are you?', is_user=True)
            ]

            for msg in messages:
                result = CommandSaveMessage.execute(
                    conv_id=self.conversation.id,
                    message=msg
                )
                self.assertTrue(result)

            if file_path.exists():
                content = file_path.read_text()
                self.assertIn('### User\nHello\n', content)
                self.assertIn('### Agent\nHi there\n', content)
                self.assertIn('### User\nHow are you?\n', content)
        finally:
            if file_path.exists():
                file_path.unlink()


class QueryFindConversationTests(TestCase):
    def setUp(self):
        self.user1 = AccountModel.objects.create(
            first_name='User',
            last_name='One',
            user_name='user1',
            password_hash=make_password('pass')
        )
        self.user2 = AccountModel.objects.create(
            first_name='User',
            last_name='Two',
            user_name='user2',
            password_hash=make_password('pass')
        )

        ConversationModel.objects.create(
            title='Paris Trip',
            user=self.user1,
            file_name='paris.txt',
            time_of_last_message=timezone.now()
        )
        ConversationModel.objects.create(
            title='Rome Trip',
            user=self.user1,
            file_name='rome.txt',
            time_of_last_message=timezone.now()
        )
        ConversationModel.objects.create(
            title='London Trip',
            user=self.user2,
            file_name='london.txt',
            time_of_last_message=timezone.now()
        )

    def test_find_by_user(self):
        response = QueryFindConversation.execute(user=self.user1)
        self.assertTrue(response['status'])
        self.assertEqual(len(response['data']), 2)

    def test_find_by_chat_id(self):
        conv = ConversationModel.objects.get(title='Paris Trip')
        response = QueryFindConversation.execute(chat_id=conv.id)
        self.assertTrue(response['status'])
        self.assertEqual(len(response['data']), 1)
        self.assertEqual(response['data'][0].title, 'Paris Trip')

    def test_find_with_limit(self):
        response = QueryFindConversation.execute(user=self.user1, limit=1)
        self.assertTrue(response['status'])
        self.assertEqual(len(response['data']), 1)

    def test_find_no_results(self):
        response = QueryFindConversation.execute(chat_id=99999)
        self.assertTrue(response['status'])
        self.assertEqual(len(response['data']), 0)


class QueryRetrieveMessagesTests(TestCase):
    def setUp(self):
        self.user = AccountModel.objects.create(
            first_name='Test',
            last_name='User',
            user_name='testuser',
            password_hash=make_password('testpass')
        )
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / 'messages.txt'

        message_content = '### User\nHello\n### Agent\nHi there!\n'
        self.temp_file.write_text(message_content)

        self.conversation = ConversationModel.objects.create(
            title='Test Chat',
            user=self.user,
            file_name='messages.txt',
            time_of_last_message=timezone.now()
        )

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @patch.object(ConversationModel, 'abs_path', new_callable=lambda: property(lambda self: Path(tempfile.gettempdir()) / self.file_name))
    def test_retrieve_messages(self, mock_abs_path):
        temp_file = Path(tempfile.gettempdir()) / 'messages.txt'
        temp_file.write_text('### User\nHello\n### Agent\nHi there!\n')

        try:
            response = QueryRetrieveMessages.execute(conv_id=self.conversation.id)

            self.assertTrue(response['status'])
            self.assertEqual(response['title'], 'Test Chat')
            self.assertEqual(len(response['data']), 2)
            self.assertEqual(response['data'][0].message, 'Hello\n')
            self.assertTrue(response['data'][0].is_user)
            self.assertEqual(response['data'][1].message, 'Hi there!\n')
            self.assertFalse(response['data'][1].is_user)
        finally:
            if temp_file.exists():
                temp_file.unlink()


class ChatViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = AccountModel.objects.create(
            first_name='Test',
            last_name='User',
            user_name='testuser',
            password_hash=make_password('testpass123')
        )

        session = self.client.session
        session['user_id'] = self.user.id
        session.save()

    def test_chat_controller_authenticated(self):
        response = self.client.get(reverse('chat'))
        self.assertEqual(response.status_code, 200)

    def test_chat_controller_unauthenticated(self):
        self.client.session.flush()
        with self.assertRaises(AssertionError):
            response = self.client.get(reverse('chat'))

    def test_handle_new_chat(self):
        response = self.client.post(
            reverse('chat') + 'operation/new_chat',
            data={'title': 'New Trip'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ConversationModel.objects.filter(title='New Trip').exists())

    def test_handle_delete_chat(self):
        conversation = ConversationModel.objects.create(
            title='Delete Me',
            user=self.user,
            file_name='delete.txt',
            time_of_last_message=timezone.now()
        )

        response = self.client.post(
            reverse('chat') + f'operation/delete_chat/{conversation.id}'
        )
        self.assertEqual(response.status_code, 302)

    def test_handle_select_chat(self):
        conversation = ConversationModel.objects.create(
            title='Select Me',
            user=self.user,
            file_name='select.txt',
            time_of_last_message=timezone.now()
        )

        response = self.client.post(
            reverse('chat') + f'operation/select_chat/{conversation.id}'
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session.get('conv_id'), conversation.id)
