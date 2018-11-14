from datetime import datetime
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape as html_escape
from django.utils import timezone

from jepostule.auth.models import ClientPlatform
from jepostule.pipeline import forms
from jepostule.pipeline import models


def interview_form_data(**kwargs):
    data = {
        'location': models.AnswerInterview.LOCATION_ONSITE,
        'datetime': '31/12/2018 08:00',
        'employer_name': 'Jessica Lange',
        'employer_email': 'jessica@example.com',
        'employer_phone': '0123456789',
        'employer_address': 'Hollywood Blvd',
        'message': 'Thanks for your application!',
    }
    for k, v in kwargs.items():
        data[k] = v
    return data


class BaseViewTests(TestCase):

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
        response = self.client.get(reverse(
            'pipeline:send_answer',
            kwargs={
                'answer_uuid': self.job_application.answer_uuid,
                'status': models.JobApplication.ANSWER_INTERVIEW
            }
        ))

        self.assertEqual(200, response.status_code)

    def test_answer_interview_post(self):
        response = self.client.post(
            reverse(
                'pipeline:send_answer',
                kwargs={
                    'answer_uuid': self.job_application.answer_uuid,
                    'status': models.JobApplication.ANSWER_INTERVIEW
                }
            ),
            data=interview_form_data(),
        )

        self.assertEqual(200, response.status_code)
        self.assertIn(
            html_escape(forms.InterviewForm.success_message),
            response.content.decode()
        )
        self.assertEqual('Jessica Lange', self.job_application.answer.answerinterview.employer_name)
        self.assertEqual(
            timezone.make_aware(datetime(2018, 12, 31, 8)).astimezone(timezone.utc),
            self.job_application.answer.answerinterview.datetime
        )

    def test_answer_twice(self):
        self.client.post(
            reverse(
                'pipeline:send_answer',
                kwargs={
                    'answer_uuid': self.job_application.answer_uuid,
                    'status': models.JobApplication.ANSWER_INTERVIEW
                }
            ),
            data=interview_form_data(),
        )
        response = self.client.post(
            reverse(
                'pipeline:send_answer',
                kwargs={
                    'answer_uuid': self.job_application.answer_uuid,
                    'status': models.JobApplication.ANSWER_INTERVIEW
                }
            ),
            data=interview_form_data(),
        )
        self.assertIn('Vous avez déjà répondu à cette candidature', response.content.decode())


class FormsTests(BaseViewTests):

    def test_interview_answer_form_with_datetime_in_the_past(self):
        with mock.patch.object(forms, 'now', return_value=timezone.make_aware(datetime(2018, 12, 31, 7, 59))):
            form = forms.InterviewForm(self.job_application, interview_form_data())
            self.assertEqual({}, form.errors)
            self.assertTrue(form.is_valid())

        with mock.patch.object(forms, 'now', return_value=timezone.make_aware(datetime(2018, 12, 31, 8, 1))):
            form = forms.InterviewForm(self.job_application, interview_form_data())
            self.assertIn('datetime', form.errors)
            self.assertFalse(form.is_valid())
