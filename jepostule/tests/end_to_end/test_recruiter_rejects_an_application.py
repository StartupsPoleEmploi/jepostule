"""
Recruiters should be able to refuse an application.
This is done when they receive the application email:
they can click on the "refuse the application" button. When they do it,
they arrive on a web page asking for more details. They fill out the form and submit it.
Then, a mail is sent to the job seeker.

This test makes sure refusing an interview is possible.
"""

import time

from django.conf import settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jepostule.crypto import encrypt
from jepostule.pipeline.models import JobApplication, Answer
from .base import EndToEndTestBase


class TestRecruiterRejectsAnApplication(EndToEndTestBase):


    def test_recruiter_rejects_an_application(self):
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
            url = application.get_answer_url(answer_type=Answer.Types.REJECTION)

        # Go to the demo page
        driver.get(url)

        # Select a reason to refuse the application.
        driver.find_element_by_css_selector('form input[value="novacancy"]').click()

        driver.find_element_by_css_selector('button[type="submit"]').click()

        WebDriverWait(driver, 4000)\
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'h1'))
            )

        driver.find_element_by_css_selector('button[type="submit"]').click()

        title = driver.find_element_by_css_selector('h1').text
        self.assertEqual(title, 'Refuser la candidature')

        confirmation_message = driver.find_element_by_css_selector('h2').text
        self.assertEqual(confirmation_message, 'Votre réponse a été envoyée avec succès')

        # Wait so that Kafka can consume messages
        # and send emails.
        time.sleep(10)
