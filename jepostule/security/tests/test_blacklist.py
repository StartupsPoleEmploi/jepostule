from django.conf import settings

from jepostule.security import blacklist
from jepostule.tests.base import CacheTestCase


class BlacklistTests(CacheTestCase):

    def test_blacklisted_email(self):
        blacklist.add("user@spam.co")
        self.assertTrue(blacklist.is_blacklisted("user@spam.co"))

    def test_blacklisted_details(self):
        blacklist.add("user@spam.co", "SPAM")
        details = blacklist.details("user@spam.co")

        self.assertTrue(details.is_blacklisted)
        self.assertEqual("SPAM", details.reason)
        self.assertLess(settings.BLACKLIST_DURATION_SECONDS - 5, details.expire_in())
        self.assertGreaterEqual(settings.BLACKLIST_DURATION_SECONDS, details.expire_in())

    def test_add_remove(self):
        blacklist.add("user@spam.co")
        self.assertTrue(blacklist.is_blacklisted("user@spam.co"))
        blacklist.remove("user@spam.co")
        self.assertFalse(blacklist.is_blacklisted("user@spam.co"))
