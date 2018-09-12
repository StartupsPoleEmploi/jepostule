from django.core.management.base import BaseCommand

from jepostule.queue import threads
from jepostule.queue.topics import all_topics


class Command(BaseCommand):
    help = "Consume topic messages and trigger asynchronous tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            'topics', nargs='+',
            help="Topics to process. Specify 'all' to consume all existing topics."
        )

    def handle(self, *args, **options):
        topics = options['topics']
        if topics == ['all']:
            topics = all_topics()

        self.stdout.write("Processing topics {}...\n".format(", ".join(topics)))
        threads.consume(*topics)
