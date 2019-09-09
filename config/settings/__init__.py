import os
import re
import sys

settings_match_test_files = re.match(r'config\.settings\.test.*', os.environ['DJANGO_SETTINGS_MODULE'])

if 'test' in sys.argv and not settings_match_test_files:
    sys.stderr.write(
        "Running tests with settings {}. You most probably don't want to do that.\n".format(
            os.environ['DJANGO_SETTINGS_MODULE']
        )
    )
    sys.exit(1)
