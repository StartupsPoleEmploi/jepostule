from django.core.management.base import BaseCommand

from jepostule.security import blacklist


class Command(BaseCommand):
    help = """
    Manage blacklisted email addresses.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--remove',
            action="store_true",
            help="Remove email addresses from the blacklist. By default, addresses are added.",
        )
        parser.add_argument(
            '--reason',
            default="spam",
            help="Blacklisting reason to store",
        )
        parser.add_argument(
            'email',
            nargs='+',
            help="Email address to add or remove",
        )

    def handle(self, *args, **options):
        for email in options['email']:
            if options['remove']:
                blacklist.remove(email)
            else:
                blacklist.add(email, options["reason"])
