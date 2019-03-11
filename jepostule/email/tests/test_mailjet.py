from django.test import TestCase
from unittest import mock

from jepostule.email.backends import mailjet


class MailjetTests(TestCase):

    def test_send_success(self):
        with mock.patch.object(mailjet, "post_api", return_value={
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
        }):
            message_id = mailjet.send(
                "hello from earth", "大家好！", "earthling@wudaokou.cn", ["angry@bird.com"],
                reply_to=None, attachments=None
            )

        self.assertEqual([456], message_id)

    def test_send_error(self):
        with mock.patch.object(mailjet.requests, "post", return_value=mock.Mock(status_code=400)):
            self.assertRaises(
                mailjet.MailjetAPIError,
                mailjet.send, "hello from earth", "大家好！", "earthling@wudaokou.cn", ["angry@bird.com"]
            )

    def test_parse_contact(self):
        self.assertEqual(("La Bonne Boite", "lbb@pe.fr"), mailjet.parse_contact("La Bonne Boite <lbb@pe.fr>"))
        self.assertEqual(("", "lbb@pe.fr"), mailjet.parse_contact("lbb@pe.fr"))

    def test_send_with_attachment(self):
        with mock.patch.object(mailjet, "post_api", return_value={
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
        }) as mock_post_api:
            mailjet.send(
                "hello from earth", "大家好！", "Earthling <earthling@wudaokou.cn>", ["angry@bird.com"],
                attachments=[('test.txt', b'This is your attached file!!!\n', None)]
            )
            mock_post_api.assert_called_with(
                "/send",
                {
                    "Messages": [
                        {
                            "From": {
                                "Name": "Earthling",
                                "Email": "earthling@wudaokou.cn",
                            },
                            "To": [{
                                "Name": "",
                                "Email": "angry@bird.com",
                            }],
                            "Subject": "hello from earth",
                            "HTMLPart": "大家好！",
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
        self.assertEqual('text/plain', mailjet.mimetype('test.txt'))
        self.assertEqual('image/png', mailjet.mimetype('logo.png'))
        self.assertEqual('application/octet-stream', mailjet.mimetype('nothing'))
