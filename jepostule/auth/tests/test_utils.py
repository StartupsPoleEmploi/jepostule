from unittest import mock
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
        token1 = utils.make_application_token('id1', 'from1', 'to1', 0)
        token2 = utils.make_application_token('id1', 'from1', 'to2', 0)
        token3 = utils.make_application_token('id1', 'from2', 'to1', 0)
        token4 = utils.make_application_token('id2', 'from1', 'to1', 0)
        token5 = utils.make_application_token('id3', 'from1', 'to1', 0)
        token6 = utils.make_application_token('id1', 'from1', 'to1', 1)

        self.assertEqual(
            '3b097974abbee5f9b0d463ea7bb591f2f03dead4a4c216203823de507386c378',
            token1
        )
        self.assertNotEqual(token1, token2)
        self.assertNotEqual(token1, token3)
        self.assertNotEqual(token1, token4)
        self.assertEqual(token1, token5)
        self.assertNotEqual(token1, token6)

    @override_settings(JEPOSTULE_CLIENTS={'id1': 'secret1'})
    def test_make_application_token_raises_on_invalid_client_id(self):
        self.assertRaises(exceptions.InvalidCredentials, utils.make_application_token, 'id2', 'from', 'to', 0)

    @override_settings(JEPOSTULE_CLIENTS={'id': 'secret'})
    def test_application_token_case_invariant(self):
        token1 = utils.make_application_token('id', 'from', 'to', 0)
        token2 = utils.make_application_token('id', 'FROM', 'TO', 0)
        self.assertEqual(token1, token2)

    @override_settings(
        SECRET_KEY='secret',
        JEPOSTULE_CLIENTS={
            'id1': 'secret1',
        }
    )
    def test_verify_application_token(self):
        token = utils.make_application_token('id1', 'from', 'to', 0)
        with mock.patch.object(utils, 'time', return_value=9):
            with mock.patch.object(utils, 'TOKEN_VALIDITY_SECONDS', 9):
                utils.verify_application_token(token, 'id1', 'from', 'to', 0)

    @override_settings(
        SECRET_KEY='secret',
        JEPOSTULE_CLIENTS={
            'id1': 'secret1',
        }
    )
    def test_verify_expired_application_token(self):
        token = utils.make_application_token('id1', 'from', 'to', 0)
        with mock.patch.object(utils, 'time', return_value=11):
            with mock.patch.object(utils, 'TOKEN_VALIDITY_SECONDS', 9):
                self.assertRaises(exceptions.TokenExpiredError, utils.verify_application_token, token, 'id1', 'from', 'to', 0)

    @override_settings(
        JEPOSTULE_CLIENTS={
            'id1': 'secret1',
        }
    )
    def test_verify_application_token_with_invalid_timestamp(self):
        self.assertRaises(exceptions.InvalidTimestamp, utils.verify_application_token, 'token', 'id1', 'from', 'to', 'should be integer')
        self.assertRaises(exceptions.InvalidTimestamp, utils.verify_application_token, 'token', 'id1', 'from', 'to', None)
