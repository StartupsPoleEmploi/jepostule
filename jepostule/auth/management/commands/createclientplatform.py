from django.core.management.base import BaseCommand

from jepostule.auth.models import ClientPlatform


class Command(BaseCommand):
    help = (
        "Create or update authentication credentials for integration with"
        "multiple client platforms"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'client_id',
            help="Client id: specify '{}' to create a demo".format(ClientPlatform.DEMO_CLIENT_ID)
        )
        parser.add_argument(
            '-s', '--secret',
            help="Client secret: if left blank, a random secret will be generated."
        )

    def handle(self, *args, **options):
        client_platform, _ = ClientPlatform.objects.get_or_create(client_id=options['client_id'])
        client_secret = options['secret']
        if client_secret is not None:
            client_platform.client_secret = client_secret
            client_platform.save()
        self.stdout.write("client_id={}\nclient_secret={}\n".format(
            client_platform.client_id,
            client_platform.client_secret,
        ))
