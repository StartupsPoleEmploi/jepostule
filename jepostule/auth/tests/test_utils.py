from unittest import mock
from django.test import TestCase, override_settings

from jepostule.auth import exceptions
from jepostule.auth import models
from jepostule.auth import utils


class UtilsTests(TestCase):

    def token_params(self, **kwargs):
        params = {
            'client_id': 'id1',
            'candidate_email': 'from1',
            'candidate_peid': '12345678',
            'employer_email': 'to1',
            'timestamp': 0,
        }
        for k, v in kwargs.items():
            params[k] = v
        return params

    @override_settings(SECRET_KEY='secret')
    def test_make_application_token(self):
        models.ClientPlatform.objects.create(client_id='id1', client_secret='secret1')
        models.ClientPlatform.objects.create(client_id='id2', client_secret='secret2')
        models.ClientPlatform.objects.create(client_id='id3', client_secret='secret1')

        token1 = utils.make_application_token(**self.token_params())
        token2 = utils.make_application_token(**self.token_params(employer_email='to2'))
        token3 = utils.make_application_token(**self.token_params(candidate_email='from2'))
        token4 = utils.make_application_token(**self.token_params(client_id='id2'))
        token5 = utils.make_application_token(**self.token_params(client_id='id3'))
        token6 = utils.make_application_token(**self.token_params(timestamp=1))

        self.assertNotEqual(token1, token2)
        self.assertNotEqual(token1, token3)
        self.assertNotEqual(token1, token4)
        self.assertEqual(token1, token5)
        self.assertNotEqual(token1, token6)

    def test_make_application_token_raises_on_invalid_client_id(self):
        models.ClientPlatform.objects.create(client_id='id1', client_secret='secret1')
        self.assertRaises(exceptions.InvalidCredentials, utils.make_application_token, **self.token_params(client_id='id2'))

    def test_application_token_case_invariant(self):
        models.ClientPlatform.objects.create(client_id='id1', client_secret='secret')
        token1 = utils.make_application_token(**self.token_params(candidate_email='from'))
        token2 = utils.make_application_token(**self.token_params(candidate_email='FROM'))
        self.assertEqual(token1, token2)

    @override_settings(SECRET_KEY='secret')
    def test_verify_application_token(self):
        models.ClientPlatform.objects.create(client_id='id1', client_secret='secret1')
        token = utils.make_application_token(**self.token_params())
        with mock.patch.object(utils, 'time', return_value=9):
            with mock.patch.object(utils, 'TOKEN_VALIDITY_SECONDS', 9):
                utils.verify_application_token(token=token, **self.token_params())

    @override_settings(SECRET_KEY='secret')
    def test_verify_expired_application_token(self):
        models.ClientPlatform.objects.create(client_id='id1', client_secret='secret1')
        token = utils.make_application_token(**self.token_params())
        with mock.patch.object(utils, 'time', return_value=11):
            with mock.patch.object(utils, 'TOKEN_VALIDITY_SECONDS', 9):
                self.assertRaises(exceptions.TokenExpiredError, utils.verify_application_token, token=token, **self.token_params())

    def test_verify_application_token_with_invalid_timestamp(self):
        models.ClientPlatform.objects.create(client_id='id1', client_secret='secret1')
        self.assertRaises(exceptions.InvalidTimestamp, utils.verify_application_token, token='token', **self.token_params(timestamp='should be integer'))
        self.assertRaises(exceptions.InvalidTimestamp, utils.verify_application_token, token='token', **self.token_params(timestamp=None))
