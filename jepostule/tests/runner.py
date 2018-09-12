from django.test.runner import DiscoverRunner

from jepostule.kvstore import redis


class JePostuleRunner(DiscoverRunner):
    """
    A test runner that takes care of clearing redis at every run. Be careful, redis is not cleared for every test, though.
    """

    def setup_test_environment(self, **kwargs):
        redis().flushall()
        return super().setup_test_environment(**kwargs)
