from unittest import mock
from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils.html import escape as html_escape
from django.core.files.uploadedfile import SimpleUploadedFile

from jepostule.auth.models import ClientPlatform
from jepostule.pipeline.models import JobApplication
from jepostule.pipeline import application
from .base import JobApplicationFormTestCase


class EmbedViewsTests(JobApplicationFormTestCase):

    def test_candidater(self):
        # Note that this should result in a bunch of errors, in particular
        # regarding invalid token
        response = self.client.get(reverse('embed:candidater'))
        self.assertEqual(200, response.status_code)

    def test_demo(self):
        ClientPlatform.objects.create(client_id=ClientPlatform.DEMO_CLIENT_ID)
        response = self.client.get(reverse('embed:demo'))
        self.assertEqual(200, response.status_code)

    def test_demo_without_client(self):
        response = self.client.get(reverse('embed:demo'))
        self.assertEqual(404, response.status_code)

    def test_demo_with_parameters(self):
        ClientPlatform.objects.create(client_id=ClientPlatform.DEMO_CLIENT_ID)
        response = self.client.get(reverse('embed:demo'), {'employer_email': 'boss@big.co'})
        self.assertEqual(200, response.status_code)
        self.assertIn(b'employer_email=boss%40big.co', response.content)

    def test_demo_with_custom_client_secret(self):
        platform = ClientPlatform.objects.create(client_id='testclient')
        response = self.client.get(reverse('embed:demo'), {'client_id': platform.client_id, 'client_secret': platform.client_secret})
        self.assertEqual(200, response.status_code)

    def test_send(self):
        attachment1 = SimpleUploadedFile('moncv.doc', b'\0')
        attachment2 = SimpleUploadedFile('lettre.doc', b'\0')
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken') as make_application_token:
            response = self.client.post(
                reverse('embed:candidater'),
                data=self.form_data(attachments=[attachment1, attachment2]),
            )
            make_application_token.assert_called_once()
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, JobApplication.objects.count())

        application.send_application_to_employer.consume()
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(['boss@bigco.fr'], mail.outbox[0].recipients())
        self.assertEqual(['candidate@pe.fr'], mail.outbox[0].reply_to)
        self.assertEqual("John Doe <{}>".format(settings.JEPOSTULE_NO_REPLY), mail.outbox[0].from_email)

        application.send_confirmation_to_candidate.consume()
        self.assertEqual(2, len(mail.outbox))
        self.assertEqual(['candidate@pe.fr'], mail.outbox[1].recipients())
        self.assertEqual("La Bonne Boite <{}>".format(settings.JEPOSTULE_NO_REPLY), mail.outbox[1].from_email)


    def test_send_with_incorrect_application_token(self):
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken'):
            response = self.client.post(
                reverse('embed:candidater'),
                data=self.form_data(token='invalid apptoken'),
            )

        self.assertEqual(200, response.status_code)
        self.assertIn(
            html_escape("Jeton d'authentification invalide"),
            response.content.decode()
        )
        application.send_application_to_employer.consume()
        application.send_confirmation_to_candidate.consume()
        self.assertEqual([], mail.outbox)

    def test_validate_form(self):
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken'):
            response = self.client.post(
                reverse('embed:validate'),
                data=self.form_data()
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual({"errors": {}}, response.json())


    def test_validate_field_empty_message(self):
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken'):
            response = self.client.post(
                reverse('embed:validate'),
                data=self.form_data(message="")
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual({
            "errors": {
                'message': ["Ce champ est obligatoire."],
            }
        }, response.json())
