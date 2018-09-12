from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from jepostule.pipeline.models import JobApplication
from jepostule.pipeline import application


class EmbedViewsTests(TestCase):

    def test_candidater(self):
        response = self.client.get(reverse('embed:candidater'))
        self.assertEqual(200, response.status_code)

    def test_demo(self):
        response = self.client.get(reverse('embed:demo'))
        self.assertEqual(200, response.status_code)

    def test_send(self):
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken') as make_application_token:
            response = self.client.post(
                reverse('embed:candidater'),
                data={
                    'client_id': 'id',
                    'token': 'apptoken',
                    'candidate_email': 'applicant@pe.fr',
                    'employer_email': 'boss@bigco.com',
                    'job': 'Menuisier',
                    'message': 'Bonjour ! ' * 20,
                    'coordinates': 'Last House On The Left',
                }
            )
            make_application_token.assert_called_once()
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, JobApplication.objects.count())

        application.send_application_to_employer.consume()
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(['boss@bigco.com'], mail.outbox[0].recipients())
        self.assertEqual(['applicant@pe.fr'], mail.outbox[0].reply_to)
        self.assertEqual(settings.JEPOSTULE_NO_REPLY, mail.outbox[0].from_email)

        application.send_confirmation_to_candidate.consume()
        self.assertEqual(2, len(mail.outbox))
        self.assertEqual(['applicant@pe.fr'], mail.outbox[1].recipients())
        self.assertEqual(settings.JEPOSTULE_NO_REPLY, mail.outbox[1].from_email)

    def test_send_with_incorrect_application_token(self):
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken'):
            response = self.client.post(
                reverse('embed:candidater'),
                data={
                    'client_id': 'id',
                    'token': 'invalid apptoken',
                    'candidate_email': 'applicant@pe.fr',
                    'employer_email': 'boss@bigco.com',
                    'job': 'Menuisier',
                    'message': 'Bonjour ! ' * 20,
                    'coordinates': 'Last House On The Left',
                }
            )

        self.assertEqual(200, response.status_code)
        application.send_application_to_employer.consume()
        application.send_confirmation_to_candidate.consume()
        self.assertEqual([], mail.outbox)
