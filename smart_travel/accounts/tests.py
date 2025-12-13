from django.test import TestCase, Client  # type: ignore
from django.urls import reverse  # type: ignore
from django.contrib.sessions.middleware import SessionMiddleware  # type: ignore
from .models import AccountModel
from .forms import SignUpForm, LoginForm
from .cqrs.commands import CommandCreateUser
from .cqrs.queries import QueryFindUser, QueryGetCurrentUser


class AccountModelTests(TestCase):
    def setUp(self):
        self.account_data = {
            "first_name": "John",
            "last_name": "Doe",
            "user_name": "johndoe",
            "password_hash": "hashed_password_123",
        }

    def test_create_account(self):
        account = AccountModel.objects.create(**self.account_data)
        self.assertEqual(account.first_name, "John")
        self.assertEqual(account.last_name, "Doe")
        self.assertEqual(account.user_name, "johndoe")
        self.assertEqual(account.password_hash, "hashed_password_123")
        self.assertIsNotNone(account.id)

    def test_account_fields_max_length(self):
        account = AccountModel.objects.create(
            first_name="A" * 25,
            last_name="B" * 25,
            user_name="C" * 25,
            password_hash="D" * 255,
        )
        self.assertEqual(len(account.first_name), 25)
        self.assertEqual(len(account.last_name), 25)
        self.assertEqual(len(account.user_name), 25)
        self.assertEqual(len(account.password_hash), 255)

    def test_account_retrieval(self):
        AccountModel.objects.create(**self.account_data)
        retrieved = AccountModel.objects.get(user_name="johndoe")
        self.assertEqual(retrieved.first_name, "John")
        self.assertEqual(retrieved.last_name, "Doe")

    def test_account_update(self):
        account = AccountModel.objects.create(**self.account_data)
        account.first_name = "Jane"
        account.save()
        updated = AccountModel.objects.get(id=account.id)
        self.assertEqual(updated.first_name, "Jane")

    def test_account_deletion(self):
        account = AccountModel.objects.create(**self.account_data)
        account_id = account.id
        account.delete()
        with self.assertRaises(AccountModel.DoesNotExist):
            AccountModel.objects.get(id=account_id)


class SignUpFormTests(TestCase):
    def test_valid_signup_form(self):
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "user_name": "johndoe",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "user_name": "johndoe",
            "password": "securepass123",
            "confirm_password": "differentpass",
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Passwords do not match.", form.errors["__all__"])

    def test_missing_required_fields(self):
        form_data = {
            "first_name": "John",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("last_name", form.errors)
        self.assertIn("user_name", form.errors)

    def test_empty_password(self):
        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "user_name": "johndoe",
            "password": "",
            "confirm_password": "",
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())


class LoginFormTests(TestCase):
    def test_valid_login_form(self):
        form_data = {"user_id": "johndoe", "password": "securepass123"}
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_user_id(self):
        form_data = {"password": "securepass123"}
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("user_id", form.errors)

    def test_missing_password(self):
        form_data = {"user_id": "johndoe"}
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)


class CommandCreateUserTests(TestCase):
    def test_create_user_command(self):
        result = CommandCreateUser.execute(
            first_name="Alice",
            last_name="Smith",
            user_name="alicesmith",
            password="mypassword",
        )
        self.assertTrue(result)

        user = AccountModel.objects.get(user_name="alicesmith")
        self.assertEqual(user.first_name, "Alice")
        self.assertEqual(user.last_name, "Smith")
        self.assertNotEqual(user.password_hash, "mypassword")

    def test_password_hashing(self):
        from django.contrib.auth.hashers import check_password  # type: ignore

        result = CommandCreateUser.execute(
            first_name="Bob",
            last_name="Johnson",
            user_name="bobjohnson",
            password="testpass123",
        )
        self.assertTrue(result)

        user = AccountModel.objects.get(user_name="bobjohnson")
        self.assertTrue(check_password("testpass123", user.password_hash))
        self.assertFalse(check_password("wrongpass", user.password_hash))


class QueryFindUserTests(TestCase):
    def setUp(self):
        from django.contrib.auth.hashers import make_password

        AccountModel.objects.create(
            first_name="John",
            last_name="Doe",
            user_name="johndoe",
            password_hash=make_password("password123"),
        )
        AccountModel.objects.create(
            first_name="Jane",
            last_name="Doe",
            user_name="janedoe",
            password_hash=make_password("password456"),
        )

    def test_find_by_username(self):
        response = QueryFindUser.execute(user_name="johndoe")
        self.assertTrue(response["status"])
        self.assertEqual(len(response["data"]), 1)
        self.assertEqual(response["data"][0].user_name, "johndoe")

    def test_find_by_last_name(self):
        response = QueryFindUser.execute(last_name="Doe")
        self.assertTrue(response["status"])
        self.assertEqual(len(response["data"]), 2)

    def test_find_by_id(self):
        user = AccountModel.objects.get(user_name="johndoe")
        response = QueryFindUser.execute(user_id=user.id)
        self.assertTrue(response["status"])
        self.assertEqual(len(response["data"]), 1)
        self.assertEqual(response["data"][0].id, user.id)

    def test_password_verification(self):
        response = QueryFindUser.execute(user_name="johndoe", password="password123")
        self.assertTrue(response["status"])
        self.assertEqual(len(response["data"]), 1)

        response_wrong = QueryFindUser.execute(
            user_name="johndoe", password="wrongpass"
        )
        self.assertTrue(response_wrong["status"])
        self.assertEqual(len(response_wrong["data"]), 0)

    def test_no_results(self):
        response = QueryFindUser.execute(user_name="nonexistent")
        self.assertTrue(response["status"])
        self.assertEqual(len(response["data"]), 0)


class QueryGetCurrentUserTests(TestCase):
    def setUp(self):
        self.client = Client()
        from django.contrib.auth.hashers import make_password

        self.user = AccountModel.objects.create(
            first_name="Test",
            last_name="User",
            user_name="testuser",
            password_hash=make_password("testpass"),
        )

    def test_get_current_user_with_session(self):
        from django.http import HttpRequest

        request = HttpRequest()
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session["user_id"] = self.user.id
        request.session.save()

        response = QueryGetCurrentUser.execute(request)
        self.assertTrue(response["status"])
        self.assertIsNotNone(response["data"])
        self.assertEqual(response["data"].id, self.user.id)

    def test_get_current_user_no_session(self):
        from django.http import HttpRequest

        request = HttpRequest()
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        response = QueryGetCurrentUser.execute(request)
        self.assertFalse(response["status"])
        self.assertIsNone(response["data"])


class AccountsViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_view_get(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "signup.html")
        self.assertIsInstance(response.context["form"], SignUpForm)

    def test_signup_view_post_valid(self):
        form_data = {
            "first_name": "Test",
            "last_name": "User",
            "user_name": "testuser",
            "password": "testpass123",
            "confirm_password": "testpass123",
        }
        response = self.client.post(reverse("signup"), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(AccountModel.objects.filter(user_name="testuser").exists())

    def test_signup_view_post_invalid(self):
        form_data = {
            "first_name": "Test",
            "last_name": "User",
            "user_name": "testuser",
            "password": "testpass123",
            "confirm_password": "wrongpass",
        }
        response = self.client.post(reverse("signup"), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AccountModel.objects.filter(user_name="testuser").exists())

    def test_login_view_get(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        self.assertIsInstance(response.context["form"], LoginForm)

    def test_login_view_post_valid(self):
        from django.contrib.auth.hashers import make_password

        AccountModel.objects.create(
            first_name="Test",
            last_name="User",
            user_name="testuser",
            password_hash=make_password("testpass123"),
        )

        form_data = {"user_id": "testuser", "password": "testpass123"}
        response = self.client.post(reverse("login"), data=form_data, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/chat/")
        self.assertIn("user_id", self.client.session)

    def test_login_view_post_invalid_credentials(self):
        from django.contrib.auth.hashers import make_password

        AccountModel.objects.create(
            first_name="Test",
            last_name="User",
            user_name="testuser",
            password_hash=make_password("testpass123"),
        )

        form_data = {"user_id": "testuser", "password": "wrongpass"}
        response = self.client.post(reverse("login"), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("user_id", self.client.session)

    def test_logout_view(self):
        from django.contrib.auth.hashers import make_password

        user = AccountModel.objects.create(
            first_name="Test",
            last_name="User",
            user_name="testuser",
            password_hash=make_password("testpass123"),
        )

        session = self.client.session
        session["user_id"] = user.id
        session.save()

        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("user_id", self.client.session)
