import random
import string

from django.db import models


def generate_secret_key():
    return ''.join([random.choice(string.ascii_lowercase + string.digits) for _ in range(32)])


class ClientPlatform(models.Model):
    # A client with this id should NOT be created on a production platform
    DEMO_CLIENT_ID = 'demo'

    client_id = models.CharField(max_length=32, unique=True)
    client_secret = models.CharField(
        max_length=32,
        default=generate_secret_key,
    )
