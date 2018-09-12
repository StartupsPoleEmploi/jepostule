import logging
from time import sleep

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from jepostule.queue.models import DelayedMessage
from jepostule.queue import topics


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Re-emit delayed messages"

    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--fail-delay', type=int, default=36000,
            help=(
                "In case a message fails be re-emitted, re-emit it with this delay (in seconds). "
                "Defaults to 10 minutes"
            )
        )

    def handle(self, *args, **options):
        fail_delay = options['fail_delay']
        while True:
            for message in DelayedMessage.objects.filter(until__lt=now()):
                logger.info("Dequeue delayed message id=%s from topic %s", message.id, message.topic)
                topics.dequeue(message, fail_delay=fail_delay)
            sleep(1)
