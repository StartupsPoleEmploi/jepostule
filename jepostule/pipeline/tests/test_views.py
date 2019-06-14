import json
from datetime import datetime
from unittest import mock

from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.urls import reverse
from django.utils.html import escape as html_escape
from django.utils import timezone

from jepostule.tests.base import PipelineTestCase
from jepostule.auth.models import ClientPlatform
from jepostule.pipeline import events
from jepostule.pipeline import forms
from jepostule.pipeline import models


def interview_form_data(**kwargs):
    data = {
        'location': models.AnswerInterview.LOCATION_ONSITE,
        'datetime': '31/12/2051 08:00',
        'employer_name': 'Jessica Lange',
        'employer_email': 'jessica@example.com',
        'employer_phone': '0123456789',
        'employer_address': 'Hollywood Blvd',
        'message': 'Thanks for your application!',
    }
    for k, v in kwargs.items():
        data[k] = v
    return data


class BaseViewTests(PipelineTestCase):

    def setUp(self):
        client_platform = ClientPlatform.objects.create(client_id="id")
        self.job_application = models.JobApplication.objects.create(client_platform=client_platform)


class EmailViewsTests(BaseViewTests):

    def setUp(self):
        super().setUp()
        user = User.objects.create(username='john')
        user.set_password('password')
        user.save()
        self.assertTrue(self.client.login(username='john', password='password'))

    def test_email_application(self):
        response = self.client.get(reverse(
            'pipeline:email_application',
            kwargs={'job_application_id': self.job_application.id}
        ))
        self.assertEqual(200, response.status_code)

    def test_email_confirmation(self):
        response = self.client.get(reverse(
            'pipeline:email_confirmation',
            kwargs={'job_application_id': self.job_application.id}
        ))
        self.assertEqual(200, response.status_code)


class AnswerViewsTests(BaseViewTests):

    def test_answer_interview_get(self):
        response = self.client.get(self.job_application.get_answer_url(models.Answer.Types.INTERVIEW))
        self.assertEqual(200, response.status_code)

    def test_answer_interview_post(self):
        response = self.client.post(
            self.job_application.get_answer_url(models.Answer.Types.INTERVIEW),
            data=interview_form_data(),
        )
        self.assertEqual(200, response.status_code)
        self.assertIn(
            html_escape(forms.InterviewForm.success_message),
            response.content.decode()
        )
        self.assertEqual('Jessica Lange', self.job_application.answer.answerinterview.employer_name)
        self.assertEqual(
            timezone.make_aware(datetime(2051, 12, 31, 8)).astimezone(timezone.utc),
            self.job_application.answer.answerinterview.datetime
        )

    def test_answer_twice(self):
        self.client.post(
            self.job_application.get_answer_url(models.Answer.Types.INTERVIEW),
            data=interview_form_data(),
        )
        response = self.client.post(
            self.job_application.get_answer_url(models.Answer.Types.INTERVIEW),
            data=interview_form_data(),
        )
        self.assertIn('Vous avez déjà répondu à cette candidature', response.content.decode())


class FormsTests(BaseViewTests):

    def test_interview_answer_form_with_datetime_in_the_past(self):
        with mock.patch.object(forms, 'now', return_value=timezone.make_aware(datetime(2051, 12, 31, 7, 59))):
            form = forms.InterviewForm(self.job_application, interview_form_data())
            self.assertEqual({}, form.errors)
            self.assertTrue(form.is_valid())

        with mock.patch.object(forms, 'now', return_value=timezone.make_aware(datetime(2051, 12, 31, 8, 1))):
            form = forms.InterviewForm(self.job_application, interview_form_data())
            self.assertIn('datetime', form.errors)
            self.assertFalse(form.is_valid())


class EventCallbackTest(PipelineTestCase):

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
            reverse('pipeline:event_callback'),
            json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)

    def test_no_event(self):
        response = self.client.post(
            reverse('pipeline:event_callback'),
            json.dumps([]),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)

    def test_incorrect_content_type(self):
        response = self.client.post(
            reverse('pipeline:event_callback'),
        )
        self.assertEqual(400, response.status_code)
        self.assertIn('content type', response.json()['error'])

    def test_json_content_invalid_data(self):
        response = self.client.post(
            reverse('pipeline:event_callback'),
            json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(400, response.status_code)
        self.assertIn('Expected array', response.json()['error'])

    def test_callback_garbage_event(self):
        response = self.client.post(
            reverse('pipeline:event_callback'),
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
            reverse('pipeline:event_callback'),
            json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)

    def test_spam_event(self):
        data = [
            {
                'event': 'spam',
                'email': 'hackz@loana.ru',
            }
        ]
        response = self.client.post(
            reverse('pipeline:event_callback'),
            json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)

    @override_settings(EVENT_CALLBACK_SECRET='abcd')
    def test_secret_verification(self):
        response = self.client.post(
            reverse('pipeline:event_callback') + '?secret=incorrect',
            json.dumps([]),
            content_type='application/json',
        )
        self.assertEqual(403, response.status_code)

        response = self.client.post(
            reverse('pipeline:event_callback') + '?secret=abcd',
            json.dumps([]),
            content_type='application/json',
        )
        self.assertEqual(200, response.status_code)
