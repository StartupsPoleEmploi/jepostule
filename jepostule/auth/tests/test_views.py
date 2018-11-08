import json
from unittest import mock
from django.test import Client, TestCase
from django.urls import reverse

from jepostule.auth import models


class ApplicationKeyTests(TestCase):

    def setUp(self):
        models.ClientPlatform.objects.create(client_id='id', client_secret='secret')
        self.form_data = {
            'candidate_email': 'applicant@pe.fr',
            'candidate_peid': '123456',
            'employer_email': 'boss@bigco.com',
            'client_id': 'id',
            'client_secret': 'secret',
        }

    def test_application_token(self):
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken') as make_application_token:
            with mock.patch('jepostule.auth.utils.time', return_value=3.14):
                response = self.client.post(reverse('auth:application_token'), self.form_data)

            self.assertEqual(200, response.status_code)
            self.assertEqual("apptoken", response.json()["token"])
            self.assertEqual(3, response.json()["timestamp"])
            make_application_token.assert_called_once_with(timestamp=3, **self.form_data)

    def test_application_token_without_candidate_email(self):
        self.form_data.pop('candidate_email')
        response = self.client.post(reverse('auth:application_token'), self.form_data)
        self.assertEqual(403, response.status_code)
        self.assertIn("error", response.json())

    def test_application_token_with_wrong_authentication(self):
        self.form_data['client_secret'] = 'wrong'
        response = self.client.post(reverse('auth:application_token'), self.form_data)
        self.assertEqual(403, response.status_code)
        self.assertIn("error", response.json())

    def test_refresh_token(self):
        # Get token/timestamp
        with mock.patch('jepostule.auth.utils.time', return_value=0):
            response = self.client.post(reverse('auth:application_token'), self.form_data)
        token = response.json()["token"]
        timestamp = response.json()["timestamp"]

        # Refresh token/timestamp
        self.form_data['token'] = token
        self.form_data['timestamp'] = timestamp
        with mock.patch('jepostule.auth.utils.time', return_value=1):
            response = self.client.post(reverse('auth:application_token_refresh'), self.form_data)

        self.assertEqual(200, response.status_code)
        new_token = response.json()['token']
        new_timestamp = response.json()['timestamp']

        self.assertEqual(0, timestamp)
        self.assertEqual(1, new_timestamp)
        self.assertNotEqual(token, new_token)

    def test_refresh_token_too_late(self):
        # Get token/timestamp
        response = self.client.post(reverse('auth:application_token'), self.form_data)
        token = response.json()["token"]
        timestamp = response.json()["timestamp"]

        # Refresh token/timestamp
        self.form_data['token'] = token
        self.form_data['timestamp'] = timestamp
        with mock.patch('jepostule.auth.utils.time', return_value=timestamp+11):
            with mock.patch('jepostule.auth.utils.TOKEN_VALIDITY_SECONDS', 10):
                response = self.client.post(reverse('auth:application_token_refresh'), self.form_data)

        self.assertEqual(403, response.status_code)
        self.assertEqual("Jeton d'authentification expiré", response.json()['error'])

    def test_refresh_token_with_invalid_client_id(self):
        self.form_data['token'] = 'apptoken'
        self.form_data['timestamp'] = 0
        self.form_data['client_id'] = 'invalid'
        with mock.patch('jepostule.auth.utils.time', return_value=1):
            response = self.client.post(reverse('auth:application_token_refresh'), self.form_data)
        self.assertEqual(403, response.status_code)
        self.assertEqual('Paramètres client ID/secret invalides', response.json()['error'])


class EventCallbackTest(TestCase):

    def test_open_events(self):
        # Sample data from mailjet's documentation
        data = [
            {
                "event": "sent",
                "time": 1433333949,
                "MessageID": 19421777835146490,
                "email": "api@mailjet.com",
                "mj_campaign_id": 7257,
                "mj_contact_id": 4,
                "customcampaign": "",
                "mj_message_id": "19421777835146490",
                "smtp_reply": "sent (250 2.0.0 OK 1433333948 fa5si855896wjc.199 - gsmtp)",
                "CustomID": "helloworld",
                "Payload": ""
            },
            {
                "event": "sent",
                "time": 1433333949,
                "MessageID": 19421777835146491,
                "email": "api@mailjet.com",
                "mj_campaign_id": 7257,
                "mj_contact_id": 4,
                "customcampaign": "",
                "mj_message_id": "19421777835146491",
                "smtp_reply": "sent (250 2.0.0 OK 1433333948 fa5si855896wjc.199 - gsmtp)",
                "CustomID": "helloworld",
                "Payload": ""
            }
        ]
        response = self.client.post(
            reverse('auth:application_event_callback'),
            json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)

    def test_no_event(self):
        response = self.client.post(
            reverse('auth:application_event_callback'),
            json.dumps([]),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)

    def test_incorrect_content_type(self):
        response = self.client.post(
            reverse('auth:application_event_callback'),
        )
        self.assertEqual(400, response.status_code)
        self.assertIn('content type', response.json()['error'])

    def test_json_content_invalid_data(self):
        response = self.client.post(
            reverse('auth:application_event_callback'),
            json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(400, response.status_code)
        self.assertIn('Expected array', response.json()['error'])

    def test_callback_garbage_event(self):
        response = self.client.post(
            reverse('auth:application_event_callback'),
            b'[garbagecontent}',
            content_type='application/json',
        )
        self.assertEqual(400, response.status_code)

    def test_event_does_not_require_csrf(self):
        data = [
            {
                'event': 'sent',
            }
        ]
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse('auth:application_event_callback'),
            json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)
