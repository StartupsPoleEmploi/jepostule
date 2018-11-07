from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape as html_escape
from django.utils import timezone

from jepostule.pipeline import forms
from jepostule.pipeline import models


class EmailViewsTests(TestCase):

    def setUp(self):
        user = User.objects.create(username='john')
        user.set_password('password')
        user.save()
        self.assertTrue(self.client.login(username='john', password='password'))

    def test_email_application(self):
        job_application = models.JobApplication.objects.create()
        response = self.client.get(reverse(
            'pipeline:email_application',
            kwargs={'job_application_id': job_application.id}
        ))
        self.assertEqual(200, response.status_code)

    def test_email_confirmation(self):
        job_application = models.JobApplication.objects.create()
        response = self.client.get(reverse(
            'pipeline:email_confirmation',
            kwargs={'job_application_id': job_application.id}
        ))
        self.assertEqual(200, response.status_code)


class AnswerViewsTests(TestCase):

    def test_answer_interview_get(self):
        job_application = models.JobApplication.objects.create()
        response = self.client.get(reverse(
            'pipeline:answer',
            kwargs={'answer_uuid': job_application.answer_uuid, 'status': models.JobApplication.ANSWER_INTERVIEW}
        ))

        self.assertEqual(200, response.status_code)

    def test_answer_interview_post(self):
        job_application = models.JobApplication.objects.create()
        response = self.client.post(
            reverse(
                'pipeline:answer',
                kwargs={'answer_uuid': job_application.answer_uuid, 'status': models.JobApplication.ANSWER_INTERVIEW}
            ),
            data={
                'location': models.AnswerInterview.LOCATION_ONSITE,
                'datetime': '31/12/2018 08:00',
                'employer_name': 'Jessica Lange',
                'employer_email': 'jessica@example.com',
                'employer_phone': '0123456789',
                'employer_address': 'Hollywood Blvd',
                'message': 'Thanks for your application!',
            }
        )

        self.assertEqual(200, response.status_code)
        self.assertIn(
            html_escape(forms.InterviewForm.success_message),
            response.content.decode()
        )
        self.assertEqual('Jessica Lange', job_application.answer.answerinterview.employer_name)
        self.assertEqual(
            timezone.make_aware(datetime(2018, 12, 31, 8)).astimezone(timezone.utc),
            job_application.answer.answerinterview.datetime
        )
