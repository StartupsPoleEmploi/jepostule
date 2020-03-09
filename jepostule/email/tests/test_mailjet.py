from unittest import mock

import requests
from django.conf import settings
from django.test import TestCase

from jepostule.email.services.mailjet import MailJetClient, MailjetAPIError


MAILJET_SUCCESS_RETURN_VALUE = {
    "Messages": [
        {
            "Status": "success",
            "To": [
                {
                    "Email": "angry@bird.com",
                    "MessageUUID": "123",
                    "MessageID": 456,
                    "MessageHref": "https://api.mailjet.com/v3/message/456"
                }
            ]
        }
    ]
}

class MailjetTests(TestCase):

    def setUp(self):
        self.client = MailJetClient('', '')

    def test_send_success(self):
        with mock.patch.object(self.client, "post_api", return_value=MAILJET_SUCCESS_RETURN_VALUE):
            message_id = self.client.send(
                "subject: hello from earth",
                "<p>html_content: 大家好！</p>",
                "earthling@wudaokou.cn",
                ["angry@bird.com"],
                attachments=None
            )
        self.assertEqual([456], message_id)

    def test_send_using_template_success(self):
        with mock.patch.object(self.client, "post_api", return_value=MAILJET_SUCCESS_RETURN_VALUE):
            message_id = self.client.send_using_template(
                "subject: hello from earth",
                settings.MAILJET_TEMPLATES['SEND_APPLICATION_TO_EMPLOYER'],
                {'template_data': 'foo'},
                "earthling@wudaokou.cn",
                ["angry@bird.com"],
                attachments=None
            )
        self.assertEqual([456], message_id)

    def test_send_error(self):
        # Patch `requests.post` since it's used by mailjet_rest's Client.
        with mock.patch.object(requests, "post", return_value=mock.Mock(status_code=400)):
            self.assertRaises(
                MailjetAPIError,
                self.client.send, "hello from earth", "大家好！", "earthling@wudaokou.cn", ["angry@bird.com"]
            )

    def test_send_with_attachment(self):
        with mock.patch.object(self.client, "post_api", return_value=MAILJET_SUCCESS_RETURN_VALUE) as mock_post_api:
            self.client.send(
                "subject: hello from earth",
                "<p>html_content: 大家好！</p>",
                "earthling@wudaokou.cn",
                ["angry@bird.com"],
                from_name="Earthling",
                attachments=[('test.txt', b'This is your attached file!!!\n', None)]
            )
            mock_post_api.assert_called_with(
                {
                    "Messages": [
                        {
                            "From": {
                                "Email": "earthling@wudaokou.cn",
                                "Name": "Earthling",
                            },
                            "To": [{
                                "Email": "angry@bird.com",
                            }],
                            "Subject": "subject: hello from earth",
                            "HTMLPart": "<p>html_content: 大家好！</p>",
                            "Attachments": [{
                                "ContentType": "text/plain",
                                "Filename": "test.txt",
                                "Base64Content": "VGhpcyBpcyB5b3VyIGF0dGFjaGVkIGZpbGUhISEK"
                            }]
                        }
                    ]
                }
            )

    def test_mimetype(self):
        self.assertEqual('text/plain', self.client.mimetype('test.txt'))
        self.assertEqual('image/png', self.client.mimetype('logo.png'))
        self.assertEqual('application/octet-stream', self.client.mimetype('nothing'))
