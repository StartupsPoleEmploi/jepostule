"""
Custom runners used to perform tests with Django.
"""

import time

from django.test.runner import DiscoverRunner

from jepostule.kvstore import redis


class JePostuleRunner(DiscoverRunner):
    """
    A test runner that takes care of clearing redis at every run. Be careful, redis is not cleared for every test, though.
    """

    def setup_test_environment(self, **kwargs):
        redis().flushall()
        return super().setup_test_environment(**kwargs)


class NoDbRunner(DiscoverRunner):
    """
    A runner that does not create nor destroys the test database
    between runs.
    """

    def setup_databases(self, **kwargs):
        """
        For an unknown reason, we just need to wait here.
        Otherwise, Kafka does not send emails related to the `send-application` topic
        in end-to-end tests (see Makefile > test-e2e-*).
        ¯\_(ツ)_/¯
        """
        time.sleep(10)


    def teardown_databases(self, old_config, **kwargs):
        pass
