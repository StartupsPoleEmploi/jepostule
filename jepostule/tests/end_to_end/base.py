"""
Base test class to run end to end tests with Selenium.
"""

from unittest import skipUnless

from django.conf import settings
from django.test import LiveServerTestCase
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options

from jepostule.auth.models import ClientPlatform


@skipUnless(
    condition=("test_e2e" in str(settings)),
    reason="Run only with end_to_end settings"
)
class EndToEndTestBase(LiveServerTestCase):


    @classmethod
    def setUpClass(cls):
        """
        Method ran before each test class.
        """

        # Perform Django pre-tests checks and cleanings.
        super().setUpClass()

        chrome_options = Options()

        if settings.RUN_HEADLESS:
            chrome_options.add_argument("--headless")

        cls.driver = WebDriver(options=chrome_options)

        ClientPlatform.objects.create(client_id='test')
        cls.client_platform = ClientPlatform.objects.get(client_id='test')


    @classmethod
    def tearDownClass(cls):
        """
        Method ran after each test class.
        """

        # Close the browser.
        cls.driver.quit()

        # Perform Django post-tests cleanings.
        super().tearDownClass()
