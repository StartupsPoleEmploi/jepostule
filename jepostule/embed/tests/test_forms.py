from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils.datastructures import MultiValueDict

from jepostule.embed import forms
from jepostule.pipeline import models
from .base import JobApplicationFormTestCase


class FormsTest(JobApplicationFormTestCase):

    def test_valid_client_id_token(self):
        form = forms.JobApplicationForm(data=self.form_data())
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken') as make_application_token:
            is_valid = form.is_valid()

            self.assertEqual({}, form.errors)
            self.assertTrue(is_valid)
            make_application_token.assert_called_once()

            form.save()
            job_application = models.JobApplication.objects.get()
            self.assertEqual(self.client_platform.id, job_application.client_platform.id)

    def test_invalid_token(self):
        form = forms.JobApplicationForm(data=self.form_data(token='invalid'))
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken') as make_application_token:
            is_valid = form.is_valid()
            self.assertEqual(['__all__'], list(form.errors.keys()))
            self.assertFalse(is_valid)
            make_application_token.assert_called_once()

    def test_invalid_client_id(self):
        form = forms.JobApplicationForm(data=self.form_data(client_id="invalid"))
        self.assertFalse(form.is_valid())
        self.assertEqual(['Paramètres client ID/secret invalides'], list(form.errors['__all__']))

    def test_expired_token(self):
        form = forms.JobApplicationForm(data=self.form_data(timestamp=0))
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken'):
            self.assertFalse(form.is_valid())
        self.assertEqual(["Jeton d'authentification expiré"], list(form.errors['__all__']))

    def test_too_large_attachments(self):
        attachment = SimpleUploadedFile('moncv.doc', b'\0'*1000)

        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken'):
            with override_settings(ATTACHMENTS_MAX_SIZE_BYTES=1000):
                form = forms.AttachmentsForm(files=MultiValueDict({'attachments': [attachment]}))
                self.assertEqual({}, form.errors)
                self.assertTrue(form.is_valid())

            with override_settings(ATTACHMENTS_MAX_SIZE_BYTES=999):
                form = forms.AttachmentsForm(files=MultiValueDict({'attachments': [attachment]}))
                self.assertFalse(form.is_valid())
