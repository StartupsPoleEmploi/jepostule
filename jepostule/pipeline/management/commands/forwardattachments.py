from django.conf import settings
from django.core.management.base import BaseCommand

import kafka

from jepostule.queue.serialize import loads
from jepostule.pipeline.utils import send_mail


class Command(BaseCommand):
    help = """
Find a specific job application and forward attachments for debugging purposes.
Note that the attachments may not be found if they were removed from the Kafka
queue."""

    def add_arguments(self, parser):
        parser.add_argument(
            'job_application_id', type=int,
            help="Job application to find"
        )
        parser.add_argument(
            'emails', nargs='+',
            help="Email addresses to send attachments to"
        )

    def handle(self, *args, **options):
        consumer = kafka.KafkaConsumer(
            'send-application',
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            consumer_timeout_ms=5000,
            auto_offset_reset='earliest',
        )

        job_application_id = options['job_application_id']
        for message in consumer:
            args, kwargs = loads(message.value)
            if args == (job_application_id,):
                attachments = kwargs.get("attachments", [])
                print("Attachments found: {}".format(len(attachments)))
                if attachments:
                    for attachment in attachments:
                        print(attachment.name)
                    send_mail(
                        "job application {}".format(job_application_id),
                        "", settings.JEPOSTULE_NO_REPLY,
                        options['emails'],
                        attachments=attachments,
                    )
                return
        print("Job application #{} was not found".format(job_application_id))
