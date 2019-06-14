from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings

from jepostule.email.services import mailjet
from jepostule.email.utils import send_mail


class UtilsTests(TestCase):

    @override_settings(EMAIL_DELIVERY_SERVICE='mailjet')
    def test_send_mail_mailjet(self):
        """
        Ensures that the given arguments and settings trigger the right payload
        to the mailjet API.
        """
        email_args = ('subject', 'html_content', 'from@from.com', ['to@to.com'])
        email_kwargs = {'from_name': None, 'attachments': None}
        # Patch `requests.post` since it's used by mailjet_rest's Client.
        with mock.patch.object(mailjet, "post_api") as mock_post_api:
            send_mail(*email_args, **email_kwargs)
            mock_post_api.assert_called_with(
                {
                    "Messages": [
                        {
                            "From": {
                                "Email": "from@from.com",
                            },
                            "To": [{
                                "Email": "to@to.com",
                            }],
                            "Subject": "subject",
                            "HTMLPart": "html_content",
                            "Attachments": [],
                        }
                    ]
                }
            )

    @override_settings(EMAIL_DELIVERY_SERVICE='mailjet')
    def test_send_template_mail_mailjet(self):
        """
        Ensures that the given arguments and settings trigger the right payload
        to the mailjet API.
        """
        email_args = ('subject', 'html_content', 'from@from.com', ['to@to.com'])
        email_kwargs = {
            'mailjet_template_id': settings.MAILJET_TEMPLATES['SEND_APPLICATION_TO_EMPLOYER'],
            'mailjet_template_data': {'template_data': 'foo'},
        }
        # Patch `requests.post` since it's used by mailjet_rest's Client.
        with mock.patch.object(mailjet, "post_api") as mock_post_api:
            send_mail(*email_args, **email_kwargs)
            mock_post_api.assert_called_with(
                {
                    "Messages": [
                        {
                            "From": {
                                "Email": "from@from.com",
                            },
                            "To": [{
                                "Email": "to@to.com",
                            }],
                            "Subject": "subject",
                            "Attachments": [],
                            "TemplateID": email_kwargs['mailjet_template_id'],
                            "TemplateLanguage": True,
                            "Variables": email_kwargs['mailjet_template_data'],
                        }
                    ]
                }
            )

    @override_settings(EMAIL_DELIVERY_SERVICE='django')
    def test_send_mail_django(self):
        """
        Ensures that the given arguments and settings trigger the default
        `django.core.mail`.
        """
        email_args = ('subject', 'html_content', 'from@from.com', ['to@to.com'])
        email_kwargs = {'from_name': None, 'attachments': None}
        send_mail(*email_args, **email_kwargs)
        self.assertEqual(len(mail.outbox), 1, "An email should have been sent")
        self.assertIn('to@to.com', mail.outbox[0].to)
        self.assertEqual('html_content', mail.outbox[0].body)
