"""
Candidates should be able to send an application.
This test imitates how a candidate would fill out our form and send it.
"""

import time
from pathlib import Path

from django.urls import reverse
from django.conf import settings
from django.utils.http import urlencode
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import EndToEndTestBase


class TestCandidateCanApply(EndToEndTestBase):


    def test_candidate_can_apply(self):
        driver = self.driver

        demo_page_params = {
            'client_id': self.client_platform.client_id,
            'client_secret': self.client_platform.client_secret,
            'candidate_email': settings.BACKDOOR_CANDIDATE_EMAIL,
            'employer_email': settings.BACKDOOR_EMPLOYER_EMAIL,
        }

        demo_page_url = self.live_server_url \
            + reverse('embed:demo') \
            + '?' \
            + urlencode(demo_page_params)

        # Go to the demo page
        driver.get(demo_page_url)

        driver.switch_to.frame('jepostule')

        form_fields = {
            'job': {
                'value': 'Acteur',
                'type': 'input',
            },
            'candidate_phone': {
                'value': '0612345678',
                'type': 'input',
            },
            'candidate_address': {
                'value': 'Charcé-Saint-Ellier, 49320 Brissac Loire Aubance',
                'type': 'input',
            },
            'message': {
                'value': 'Le but de ma vie ? Travailler avec vous.',
                'type': 'textarea',
            },
        }

        resume_filename = 'resume.png'

        # Get the resume path to upload it later.
        attached_file_path = str(Path(__file__).resolve().parent / resume_filename)

        # Click on "C'est parti !"
        # FIXME 4000s o_O
        # FIXME try this test alone
        go = WebDriverWait(driver, 4000)\
            .until(
                EC.visibility_of_element_located((By.LINK_TEXT, "C'est parti !"))
            )
        go.click()

        for key in form_fields:
            html_tag = form_fields[key]['type']
            value = form_fields[key]['value']
            element = driver.find_element_by_css_selector(f'{html_tag}[name="{key}"]')
            element.clear()
            element.send_keys(value)

        # Click on "Je continue"
        continue_button = driver\
            .find_element_by_css_selector('div[data-step="infos"]')\
            .find_element_by_link_text("Je continue")

        # Scroll to the "Continuer" button,
        # otherwise clicking on it is not possible.
        height = continue_button.location_once_scrolled_into_view['y']
        driver.execute_script(f"window.scrollTo(0, {height});")

        continue_button.click()

        # Attach a resume to the application.
        driver\
            .find_element_by_css_selector('input[type="file"][name="attachments"]')\
            .send_keys(attached_file_path)

        # Click on "Je continue"
        driver\
            .find_element_by_css_selector('div[data-step="documents"]')\
            .find_element_by_id("attachments-continue").click()

        for key in form_fields:
            html_tag = form_fields[key]['type']
            value = form_fields[key]['value']

            # Get confirmation page form elements
            final_value = driver\
                .find_element_by_css_selector(f'{html_tag}[name="{key}"]')\
                .get_attribute('value')

            # Make sure the confirmation page shows the information
            # previously filled in by the user.
            self.assertEqual(value, final_value)

        final_attached_file = driver\
            .find_element_by_css_selector('.attachments-list')\
            .get_attribute('outerHTML')

        self.assertIn(resume_filename, final_attached_file)

        submit_button = driver.find_element_by_css_selector('button[type="submit"]')

        # Scroll down to the submit button
        height = submit_button.location_once_scrolled_into_view['y']
        driver.execute_script(f"window.scrollTo(0, {height});")

        # Click on "Je souhaite recevoir une confirmation de ma candidature sur ma boite mail."
        driver.find_element_by_css_selector('input[name="send_confirmation"]').click()

        submit_button.click()

        # Waiting for the title element to be displayed does not always work,
        # so we need to use the good old method!
        time.sleep(5)

        title_element = WebDriverWait(driver, 4000)\
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-step="fin"] h1'))
            )

        title = title_element.text
        self.assertEqual('Candidature envoyée', title)

        # Wait so that Kafka can consume messages
        # and send emails.
        time.sleep(10)
