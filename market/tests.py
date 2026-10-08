from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from .forms import SignUpForm
from .models import Profile


def signup_data(**overrides):
    data = {
        "username": "student01",
        "name": "홍길동",
        "birth_date": "2000-01-01",
        "phone": "01012345678",
        "password1": "StrongMarketPass!47",
        "password2": "StrongMarketPass!47",
    }
    data.update(overrides)
    return data


class SignUpFormTests(TestCase):
    def test_signup_saves_user_profile_and_hashed_password(self):
        form = SignUpForm(signup_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        user.refresh_from_db()
        self.assertEqual(user.first_name, "홍길동")
        self.assertEqual(user.profile.birth_date, date(2000, 1, 1))
        self.assertEqual(user.profile.phone, "01012345678")
        self.assertTrue(user.check_password(signup_data()["password1"]))
        self.assertNotEqual(user.password, signup_data()["password1"])
        self.assertFalse(user.is_staff)

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(username="student01")
        form = SignUpForm(signup_data())
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["username"], ["이미 사용 중인 아이디입니다."])

    def test_duplicate_phone_is_rejected(self):
        user = User.objects.create_user(username="existing")
        Profile.objects.create(user=user, birth_date=date(2000, 1, 1), phone="01012345678")
        form = SignUpForm(signup_data())
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["phone"], ["이미 사용 중인 휴대폰번호입니다."])

    def test_password_mismatch_is_rejected(self):
        form = SignUpForm(signup_data(password2="DifferentMarketPass!47"))
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_password_validators_reject_weak_passwords(self):
        for password in ["abc", "password", "123456789012", "student01"]:
            with self.subTest(password=password):
                form = SignUpForm(signup_data(password1=password, password2=password))
                self.assertFalse(form.is_valid())
                self.assertIn("password2", form.errors)

    def test_required_fields_and_invalid_date_are_rejected(self):
        for field in ["username", "name", "birth_date", "phone", "password1", "password2"]:
            with self.subTest(field=field):
                form = SignUpForm(signup_data(**{field: ""}))
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)
        form = SignUpForm(signup_data(birth_date="2000-02-30"))
        self.assertFalse(form.is_valid())
        self.assertIn("birth_date", form.errors)

    def test_commit_false_does_not_write_to_database(self):
        form = SignUpForm(signup_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save(commit=False)
        self.assertIsNone(user.pk)
        self.assertEqual(user.first_name, "홍길동")
        self.assertTrue(user.check_password(signup_data()["password1"]))
        self.assertFalse(User.objects.exists())
        self.assertFalse(Profile.objects.exists())

    def test_profile_write_failure_rolls_back_user(self):
        form = SignUpForm(signup_data())
        self.assertTrue(form.is_valid(), form.errors)
        with patch("market.forms.Profile.objects.create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                form.save()
        self.assertFalse(User.objects.exists())
        self.assertFalse(Profile.objects.exists())


class ProfileTests(TestCase):
    def test_phone_and_user_are_unique_at_database_level(self):
        first = User.objects.create_user(username="first")
        second = User.objects.create_user(username="second")
        Profile.objects.create(user=first, birth_date=date(2000, 1, 1), phone="01012345678")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.create(user=second, birth_date=date(2000, 1, 1), phone="01012345678")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.create(user=first, birth_date=date(2000, 1, 1), phone="01087654321")

    def test_deleting_user_deletes_profile(self):
        user = User.objects.create_user(username="student01")
        profile = Profile.objects.create(user=user, birth_date=date(2000, 1, 1), phone="01012345678")
        self.assertEqual(str(profile), "student01")
        user.delete()
        self.assertFalse(Profile.objects.exists())


class AuthenticationViewTests(TestCase):
    def create_user(self, **overrides):
        data = signup_data(**overrides)
        form = SignUpForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        return form.save()

    def test_anonymous_pages_show_forms_and_links(self):
        self.assertContains(self.client.get(reverse("main")), 'href="/signup/"')
        self.assertContains(self.client.get(reverse("main")), 'href="/login/"')
        self.assertContains(self.client.get(reverse("signup")), 'name="birth_date"')
        self.assertContains(self.client.get(reverse("signup")), "csrfmiddlewaretoken")
        self.assertContains(self.client.get(reverse("login")), 'name="password"')

    def test_signup_logs_in_and_displays_member_name(self):
        response = self.client.post(reverse("signup"), signup_data(), follow=True)
        self.assertRedirects(response, reverse("main"))
        self.assertContains(response, "홍길동님 환영합니다.")
        self.assertContains(response, "아이디: student01")
        self.assertContains(response, 'action="/logout/"')
        self.assertEqual(self.client.session["_auth_user_id"], str(User.objects.get().pk))
        self.assertEqual(Profile.objects.count(), 1)

    def test_invalid_signup_preserves_input_without_creating_member(self):
        response = self.client.post(reverse("signup"), signup_data(password2="wrong"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertContains(response, 'value="홍길동"')
        self.assertNotContains(response, signup_data()["password1"])
        self.assertFalse(User.objects.exists())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_duplicate_signup_displays_field_errors(self):
        self.create_user()
        response = self.client.post(reverse("signup"), signup_data())
        self.assertContains(response, "이미 사용 중인 아이디입니다.")
        self.assertContains(response, "이미 사용 중인 휴대폰번호입니다.")
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 1)

    def test_phone_reserved_after_validation_shows_error_and_rolls_back_user(self):
        existing = self.create_user(username="existing", phone="01087654321")
        original_save = SignUpForm.save

        def reserve_phone_then_save(form, commit=True):
            Profile.objects.filter(user=existing).update(phone=form.cleaned_data["phone"])
            return original_save(form, commit=commit)

        with patch.object(SignUpForm, "save", reserve_phone_then_save):
            response = self.client.post(reverse("signup"), signup_data())
        self.assertContains(response, "이미 사용 중인 휴대폰번호입니다.")
        self.assertFalse(User.objects.filter(username="student01").exists())

    def test_username_reserved_after_validation_shows_error(self):
        original_save = SignUpForm.save

        def reserve_username_then_save(form, commit=True):
            User.objects.create_user(username=form.cleaned_data["username"])
            return original_save(form, commit=commit)

        with patch.object(SignUpForm, "save", reserve_username_then_save):
            response = self.client.post(reverse("signup"), signup_data())
        self.assertContains(response, "이미 사용 중인 아이디입니다.")
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(Profile.objects.exists())

    def test_login_and_post_logout(self):
        user = self.create_user()
        response = self.client.post(reverse("login"), {
            "username": user.username, "password": signup_data()["password1"],
        }, follow=True)
        self.assertRedirects(response, reverse("main"))
        self.assertContains(response, "홍길동님 환영합니다.")
        response = self.client.post(reverse("logout"), follow=True)
        self.assertRedirects(response, reverse("main"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, 'href="/login/"')

    def test_invalid_and_inactive_logins_are_rejected(self):
        user = self.create_user()
        for credentials in [
            {"username": user.username, "password": "wrong"},
            {"username": "missing", "password": signup_data()["password1"]},
            {},
        ]:
            with self.subTest(credentials=credentials):
                response = self.client.post(reverse("login"), credentials)
                self.assertContains(response, "아이디 또는 비밀번호가 올바르지 않습니다.")
                self.assertNotIn("_auth_user_id", self.client.session)
        user.is_active = False
        user.save()
        response = self.client.post(reverse("login"), {
            "username": user.username, "password": signup_data()["password1"],
        })
        self.assertContains(response, "아이디 또는 비밀번호가 올바르지 않습니다.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_authenticated_user_is_redirected_from_login_and_signup(self):
        self.client.force_login(self.create_user())
        for name in ["login", "signup"]:
            for method in [self.client.get, self.client.post]:
                self.assertRedirects(method(reverse(name)), reverse("main"))

    def test_get_logout_keeps_user_logged_in(self):
        user = self.create_user()
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse("logout")), reverse("main"))
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_csrf_is_required_and_valid_token_allows_signup(self):
        client = Client(enforce_csrf_checks=True)
        for name in ["signup", "login", "logout"]:
            self.assertEqual(client.post(reverse(name), signup_data()).status_code, 403)
        client.get(reverse("signup"))
        token = client.cookies["csrftoken"].value
        response = client.post(reverse("signup"), signup_data(csrfmiddlewaretoken=token))
        self.assertRedirects(response, reverse("main"))
        # login rotates the CSRF token; use the new value for logout.
        self.assertEqual(client.post(reverse("logout")).status_code, 403)
        self.assertIn("_auth_user_id", client.session)
        response = client.post(reverse("logout"), {
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertRedirects(response, reverse("main"))
        self.assertNotIn("_auth_user_id", client.session)

    def test_profile_admin_lists_and_searches_member(self):
        self.create_user()
        admin = User.objects.create_superuser("admin", password="AdminMarketPass!47")
        self.client.force_login(admin)
        response = self.client.get(reverse("admin:market_profile_changelist"), {"q": "홍길동"})
        self.assertContains(response, "student01")
        self.assertContains(response, "01012345678")
