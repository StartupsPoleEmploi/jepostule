from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from jepostule.embed import forms


class FormsTest(TestCase):

    def form_data(self, **kwargs):
        data = {
            'client_id': 'id',
            'token': 'apptoken',
            'candidate_email': 'candidate@pe.fr',
            'employer_email': 'boss@bigco.fr',
            'job': 'Menuisier',
            'message': "Bonjour !" * 20,
            'coordinates': "Dernier café avant la fin du monde",
        }
        for key, value in kwargs.items():
            data[key] = value
        return data

    def test_valid_client_id_token(self):
        form = forms.JobApplicationForm(data=self.form_data())
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken') as make_application_token:
            is_valid = form.is_valid()
            self.assertEqual({}, form.errors)
            self.assertTrue(is_valid)
            make_application_token.assert_called_once()


    def test_invalid_token(self):
        form = forms.JobApplicationForm(data=self.form_data(token='invalid'))
        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken') as make_application_token:
            is_valid = form.is_valid()
            self.assertEqual(['__all__'], list(form.errors.keys()))
            self.assertFalse(is_valid)
            make_application_token.assert_called_once()

    def test_too_large_attachments(self):
        attachment = SimpleUploadedFile('moncv.doc', b'\0'*1000)

        with mock.patch('jepostule.auth.utils.make_application_token', return_value='apptoken'):
            with override_settings(ATTACHMENTS_MAX_SIZE_BYTES=1000):
                form = forms.JobApplicationForm(data=self.form_data(), files={'attachments': [attachment]})
                self.assertEqual({}, form.errors)
                self.assertTrue(form.is_valid())

            with override_settings(ATTACHMENTS_MAX_SIZE_BYTES=999):
                form = forms.JobApplicationForm(data=self.form_data(), files={'attachments': [attachment]})
                self.assertFalse(form.is_valid())
