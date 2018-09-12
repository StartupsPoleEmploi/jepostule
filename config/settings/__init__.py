import os
import sys

if 'test' in sys.argv and os.environ['DJANGO_SETTINGS_MODULE'] != 'config.settings.test':
    sys.stderr.write(
        "Running tests with settings {}. You most probably don't want to do that.\n".format(
            os.environ['DJANGO_SETTINGS_MODULE']
        )
    )
    sys.exit(1)
