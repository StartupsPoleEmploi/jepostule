from django.test import TestCase, override_settings

from jepostule.auth import exceptions
from jepostule.auth import utils


class UtilsTests(TestCase):

    @override_settings(
        SECRET_KEY='secret',
        JEPOSTULE_CLIENTS={
            'id1': 'secret1',
            'id2': 'secret2',
            'id3': 'secret1',
        }
    )
    def test_make_application_token(self):
        token1 = utils.make_application_token('id1', 'from1', 'to1')
        token2 = utils.make_application_token('id1', 'from1', 'to2')
        token3 = utils.make_application_token('id1', 'from2', 'to1')
        token4 = utils.make_application_token('id2', 'from1', 'to1')
        token5 = utils.make_application_token('id3', 'from1', 'to1')
        self.assertEqual(
            '02818930257bce8cdd06c8223367aa2f8b27bd5a44320fe66738438c3814d29f',
            token1
        )
        self.assertNotEqual(token1, token2)
        self.assertNotEqual(token1, token3)
        self.assertNotEqual(token1, token4)
        self.assertEqual(token1, token5)

    @override_settings(
        JEPOSTULE_CLIENTS={
            'id1': 'secret1',
        }
    )
    def test_make_application_token_raises_on_invalid_client_id(self):
        self.assertRaises(exceptions.ApplicationAuthError, utils.make_application_token, 'id2', 'from', 'to')
