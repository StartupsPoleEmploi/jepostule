"""
Recruiters should be able to accept an application
and propose an interview. This is done when they receive the application email:
they can click on the "plan an interview" button. When they do it,
they arrive on a web page asking for more details. They fill out the form and submit it.
Then, a mail is sent to the job seeker with details for the interview.

This test makes sure proposing an interview is possible.
"""

import time
import datetime as dt
import locale

from django.conf import settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jepostule.pipeline.models import JobApplication, Answer
from .base import EndToEndTestBase


class TestRecruiterProposesAnInterview(EndToEndTestBase):


    def test_recruiter_proposes_an_interview(self):
        driver = self.driver

        job_application_kwargs = {
            'client_platform_id': self.client_platform.id,
            'candidate_email': settings.BACKDOOR_CANDIDATE_EMAIL,
            'candidate_first_name': 'Jean',
            'candidate_last_name': 'Gabin',
            'employer_email': settings.BACKDOOR_EMPLOYER_EMAIL,
            'job': 'Acteur',
            'candidate_rome_code': 'L1203',
            'siret': '34326262220717',
        }

        # Create an Application object in DB
        application = JobApplication.objects.create(
            **job_application_kwargs
        )

        with self.settings(JEPOSTULE_BASE_URL=self.live_server_url):
            url = application.get_answer_url(answer_type=Answer.Types.INTERVIEW)

        # Go to the demo page
        driver.get(url)

        # Propose an interview date
        now = dt.datetime.now()
        tomorrow = now + dt.timedelta(days=1)
        datepicker = WebDriverWait(driver, 4000)\
            .until(
                EC.visibility_of_element_located((By.ID, "id_datetime"))
            )
        datepicker.click()
        # It should open a datepicker box.

        # Select current month in Javascript as it's a nightmare with Selenium.
        script = f"$('.xdsoft_monthselect .xdsoft_option[data-value={tomorrow.month - 1}]').click()"
        driver.execute_script(script)
        time.sleep(1)

        # Click on tomorrow's date
        # FTR: January is O.
        date_selector = f"""
            .xdsoft_datepicker.active .xdsoft_calendar [data-date='{tomorrow.day}'][data-month='{tomorrow.month - 1}'] > div
        """
        driver.find_element_by_css_selector(date_selector).click()

        # It's not possible for the moment to test if selecting a time works
        # as the Javascript library we use to show the calendar
        # works pretty badly with Selenium.
        # driver.find_element_by_css_selector(f'.xdsoft_timepicker.active .xdsoft_time_box .xdsoft_time[data-hour="{interview_hour}"]').click()

        # Assert same month
        locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        datepicker_month = driver\
            .find_element_by_css_selector('.xdsoft_datepicker.active .xdsoft_month span')\
            .get_attribute('innerHTML')
        self.assertEqual(datepicker_month, now.strftime("%B").capitalize())

        # Assert same year
        datepicker_year = driver\
            .find_element_by_css_selector('.xdsoft_datepicker.active .xdsoft_year span')\
            .get_attribute('innerHTML')
        self.assertEqual(datepicker_year, str(now.year))

        # Recruiter name
        driver.find_element_by_id('id_employer_name').send_keys('Marcel Carné')

        # Phone
        driver.find_element_by_id('id_employer_phone').send_keys('0612345667')

        # Address
        address = '102 Quai de Jemmapes, 75010 Paris'
        driver.find_element_by_id('id_employer_address').send_keys(address)

        # Further information
        message = "Merci de nous attendre à l'accueil."
        driver.find_element_by_id('id_message').send_keys(message)

        # Send form
        driver.find_element_by_css_selector('button[type="submit"]').click()

        # 'Message review' page
        WebDriverWait(driver, 4000)\
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.title h1'))
            )
        driver.find_element_by_css_selector('button[type="submit"]').click()

        # 'Message confirmation' page
        WebDriverWait(driver, 4000)\
            .until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.content h2'))
            )

        thank_you_message = driver\
            .find_element_by_css_selector('.content h2')\
            .get_attribute('innerHTML')
        self.assertEqual(thank_you_message, "Votre proposition d'entretien a été envoyée avec succès")

        # Wait so that Kafka can consume messages
        # and send emails.
        time.sleep(10)
