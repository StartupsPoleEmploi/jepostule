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
