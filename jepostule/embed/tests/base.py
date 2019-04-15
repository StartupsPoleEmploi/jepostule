from time import time

from jepostule.auth.models import ClientPlatform
from jepostule.tests.base import CacheTestCase


class JobApplicationFormTestCase(CacheTestCase):

    def setUp(self):
        super().setUp()
        self.client_platform = ClientPlatform.objects.create(client_id="id")

    def form_data(self, **kwargs):
        data = {
            'client_id': self.client_platform.client_id,
            'token': 'apptoken',
            'timestamp': time(),
            'candidate_email': 'candidate@pe.fr',
            'candidate_first_name': 'John',
            'candidate_last_name': 'Doe',
            'candidate_phone': '0612345678',
            'candidate_address': "Dernier café avant la fin du monde",
            'candidate_peid': "123456789",
            'candidate_rome_code': "A1101",
            'employer_email': 'boss@bigco.fr',
            'employer_description': "ACME BigCo Commerce de gros",
            'message': "Bonjour !" * 20,
            'siret': "73334567800012",
            'job': "Ouvrier charpentier",
            'send_confirmation': "true",
        }
        for key, value in kwargs.items():
            data[key] = value
        return data
