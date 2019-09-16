"""
Recruiters should be able to ask for more information if they need it.
This is done when they receive the application email:
they can click on the "ask for more information" button. When they do it,
they arrive on a web page asking for more details. They fill out the form and submit it.
Then, a mail is sent to the job seeker.

This test makes sure asking for more information is possible.
"""

import time

from django.conf import settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jepostule.crypto import encrypt
from jepostule.pipeline.models import JobApplication, Answer
from .base import EndToEndTestBase


class TestRecruiterNeedsFurtherInformation(EndToEndTestBase):


    def test_recruiter_needs_further_information(self):
        driver = self.driver

        job_application_kwargs = {
            'client_platform_id': self.client_platform.id,
            'candidate_email': settings.BACKDOOR_CANDIDATE_EMAIL,
            'candidate_first_name': 'Jean',
            'candidate_last_name': 'Gabin',
            'employer_email': settings.BACKDOOR_EMPLOYER_EMAIL,
            'job': 'Acteur',
            'candidate_rome_code': 'L1203',
            'candidate_peam_access_token': encrypt("01234567890abcdef01234567890abcdef"),
            'siret': '34326262220717',
        }

        # Create an Application object in DB
        application = JobApplication.objects.create(
            **job_application_kwargs
        )

        with self.settings(JEPOSTULE_BASE_URL=self.live_server_url):
            url = application.get_answer_url(answer_type=Answer.Types.REQUEST_INFO)

        # Go to the demo page
        driver.get(url)

        message = """
            Bonjour Monsieur,
            Pourriez-vous nous envoyer une bande démo ?
        """
        employer_name = "Marcel Carné"
        phone_number = "0612345667"
        office_address = "102 Quai de Jemmapes, 75010 Paris"

        driver.find_element_by_id('id_message').send_keys(message)

        driver.find_element_by_id('id_employer_name').send_keys(employer_name)

        driver.find_element_by_id('id_employer_phone').send_keys(phone_number)

        driver.find_element_by_id('id_employer_address').send_keys(office_address)

        driver.find_element_by_css_selector('button[type="submit"]').click()

        WebDriverWait(driver, 4000)\
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'h1'))
            )

        raw_content = driver.find_element_by_css_selector('.content').text
        content = raw_content.replace('\n', ' ')

        self.assertIn(" ".join(message.split()), content)
        self.assertIn(employer_name, content)
        self.assertIn(phone_number, content)
        self.assertIn(office_address, content)

        driver.find_element_by_css_selector('button[type="submit"]').click()

        title = driver.find_element_by_css_selector('h1').text
        self.assertEqual(title, 'Demander des informations complémentaires')

        confirmation_message = driver.find_element_by_css_selector('h2').text
        self.assertEqual(confirmation_message, 'Votre réponse a été envoyée avec succès')

        # Wait so that Kafka can consume messages
        # and send emails.
        time.sleep(10)
