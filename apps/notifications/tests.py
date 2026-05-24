from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from apps.notifications.models import Notification, FCMToken, UserNotificationPreference
from apps.notifications.services.notification_service import NotificationService

User = get_user_model()

class NotificationSystemTests(APITestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpassword",
            phone="966500000001"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpassword",
            phone="966500000002"
        )
        # Create user preference
        self.preference, _ = UserNotificationPreference.objects.get_or_create(
            user=self.user,
            push_enabled=True,
            email_enabled=False,
            in_app_enabled=True
        )

    @patch('apps.notifications.tasks.send_push_notification.delay')
    @patch('apps.notifications.tasks.send_email_notification.delay')
    def test_notification_service_dispatches_based_on_preferences(self, mock_email, mock_push):
        """NotificationService should only send notification types that are enabled by the user"""
        
        # Test sending push and in_app (both enabled)
        NotificationService.send_notification(
            user_id=self.user.id,
            title="Test Push/In-App",
            message="Hello user",
            notification_types=['push', 'in_app']
        )
        
        # In-app should be created and marked sent in DB
        in_app_notif = Notification.objects.filter(user=self.user, notification_type='in_app').first()
        self.assertIsNotNone(in_app_notif)
        self.assertIsNotNone(in_app_notif.sent_at)
        
        # Push should trigger the async task
        mock_push.assert_called_once()
        
        # Test sending email (disabled)
        NotificationService.send_notification(
            user_id=self.user.id,
            title="Test Email",
            message="Hello email",
            notification_types=['email']
        )
        
        # Email task should NOT be called, and no email notification record in DB
        mock_email.assert_not_called()
        email_notif = Notification.objects.filter(user=self.user, notification_type='email').first()
        self.assertNull(email_notif) if hasattr(self, 'assertNull') else self.assertIsNone(email_notif)

    def test_fcm_token_registration_endpoint(self):
        """Authenticated users can register device tokens"""
        self.client.force_authenticate(user=self.user)
        url = reverse('fcm-tokens-list')
        data = {
            "token": "fcm_test_token_12345",
            "device_type": "android"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check database
        token_obj = FCMToken.objects.filter(user=self.user, token="fcm_test_token_12345").first()
        self.assertIsNotNone(token_obj)
        self.assertTrue(token_obj.is_active)

    def test_notification_preferences_endpoint(self):
        """Users can view and update their notification preferences"""
        self.client.force_authenticate(user=self.user)
        url = reverse('notification-preferences')
        
        # Test GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['push_enabled'])
        self.assertFalse(response.data['data']['email_enabled'])
        
        # Test PUT
        update_data = {
            "push_enabled": False,
            "email_enabled": True,
            "sms_enabled": True
        }
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check DB values
        self.preference.refresh_from_db()
        self.assertFalse(self.preference.push_enabled)
        self.assertTrue(self.preference.email_enabled)
