from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdminLoginAttemptLimitTests(TestCase):
    def setUp(self):
        self.username = "lockout-test-admin"
        get_user_model().objects.create_superuser(
            username=self.username,
            email="lockout-test@example.com",
            password="Correct-password-123!",
        )
        self.login_url = reverse("admin:login")

    def test_admin_login_is_blocked_after_three_failed_password_attempts(self):
        for _ in range(3):
            response = self.client.post(
                self.login_url,
                {
                    "username": self.username,
                    "password": "incorrect-password",
                    "next": "/admin/",
                },
            )
            self.assertEqual(response.status_code, 200)

        blocked_response = self.client.post(
            self.login_url,
            {
                "username": self.username,
                "password": "incorrect-password",
                "next": "/admin/",
            },
        )
        self.assertEqual(blocked_response.status_code, 403)

    def test_successful_login_before_limit_resets_failed_attempts(self):
        for _ in range(2):
            response = self.client.post(
                self.login_url,
                {
                    "username": self.username,
                    "password": "incorrect-password",
                    "next": "/admin/",
                },
            )
            self.assertEqual(response.status_code, 200)

        successful_response = self.client.post(
            self.login_url,
            {
                "username": self.username,
                "password": "Correct-password-123!",
                "next": "/admin/",
            },
        )
        self.assertEqual(successful_response.status_code, 302)
