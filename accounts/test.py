
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationTest(APITestCase):

    def test_user_registration(self):

        data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "Test@12345"
        }

        response = self.client.post(
            "/api/accounts/register/",
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(username="testuser").exists()
        )


class UserProfileTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="Test@12345"
        )

    def test_authenticated_user_can_view_profile(self):

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/accounts/profile/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_view_profile(self):

        response = self.client.get("/api/accounts/profile/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
