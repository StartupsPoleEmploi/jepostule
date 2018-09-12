from unittest import mock

from django.test import TestCase

from jepostule.queue import serialize


class SerializeTest(TestCase):

    def test_encode_exception(self):
        with mock.patch.object(serialize.pickle, 'dumps', side_effect=serialize.pickle.PicklingError):
            self.assertRaises(serialize.EncodeError, serialize.dumps, '')

    def test_decode_exception(self):
        with mock.patch.object(serialize.pickle, 'loads', side_effect=serialize.pickle.UnpicklingError):
            self.assertRaises(serialize.DecodeError, serialize.loads, '')
