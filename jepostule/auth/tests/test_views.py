import json
from unittest import mock
from urllib.parse import urlencode

from django.test import Client, override_settings, TestCase
from django.urls import reverse


@override_settings(JEPOSTULE_CLIENTS={'id': 'secret'})
class ApplicationKeyTests(TestCase):

    def test_application_token(self):
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken') as make_application_token:
            response = self.client.get(
                reverse('auth:application_token') + '?' + urlencode({
                    'candidate_email': 'applicant@pe.fr',
                    'employer_email': 'boss@bigco.com',
                    'client_id': 'id',
                    'client_secret': 'secret',
                })
            )

            self.assertEqual(200, response.status_code)
            self.assertEqual("apptoken", response.json()["token"])
            make_application_token.assert_called_once_with('id', 'applicant@pe.fr', 'boss@bigco.com')

    def test_application_token_without_candidate_email(self):
        response = self.client.get(
                reverse('auth:application_token') + '?' + urlencode({
                    'employer_email': 'boss@bigco.com',
                    'client_id': 'id',
                    'client_secret': 'secret',
                })
        )
        self.assertEqual(400, response.status_code)
        self.assertIn("error", response.json())

    def test_application_token_with_wrong_authentication(self):
        response = self.client.get(
                reverse('auth:application_token') + '?' + urlencode({
                    'candidate_email': 'applicant@pe.fr',
                    'employer_email': 'boss@bigco.com',
                    'client_id': 'id',
                    'client_secret': 'wrongsecret',
                })
        )
        self.assertEqual(403, response.status_code)
        self.assertIn("error", response.json())


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
            data=json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)

    def test_no_event(self):
        response = self.client.post(
            reverse('auth:application_event_callback'),
            data=json.dumps([]),
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
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(400, response.status_code)
        self.assertIn('Expected array', response.json()['error'])

    def test_callback_garbage_event(self):
        response = self.client.post(
            reverse('auth:application_event_callback'),
            data=b'[garbagecontent}',
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
            data=json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)
