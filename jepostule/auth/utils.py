from time import time
import hashlib

from django.conf import settings

from . import exceptions
from . import models


# Duration during which a token is valid, in seconds. This value should be
# greater than the time required to upload documents.
TOKEN_VALIDITY_SECONDS = 30*60


def make_new_application_token(**params):
    params['timestamp'] = int(time())
    return make_application_token(**params), params['timestamp']


def make_application_token(**params):
    """
    Create an application token that cannot be reverse computed such that
    candidates cannot apply from or send to any email address.

    Generated tokens have an expiration date: this is necessary because we
    don't want stolen tokens to be re-used to generate fake applications.
    Since job applications can take a long time to create, we will have to
    refresh the token frequently.

    Note that application tokens are case-invariant with respect to candidate
    and employer email addresses.

    Args:
        timestamp (float): along with the duration parameter, this will
        determine the expiration date of the token. Note that this parameter
        will be rounded to an integer value, to simplify parsing. For all
        intents, timestamps can thus be floats.

    Return:
        token (str)
    """
    required_keys = sorted([
        'candidate_email',
        'candidate_peid',
        'employer_email',
        'timestamp',
    ])
    client_id = params.get('client_id')
    client_secret = get_client_secret(client_id)
    decoded = settings.SECRET_KEY + client_secret
    params['timestamp'] = str(get_timestamp(**params))

    for key in required_keys:
        try:
            decoded += params[key].lower()
        except KeyError:
            raise exceptions.MissingParameter(key)

    return hashlib.sha256(decoded.encode()).hexdigest()


def verify_application_token(**params):
    if get_timestamp(**params) + TOKEN_VALIDITY_SECONDS < time():
        raise exceptions.TokenExpiredError

    token = params.get('token')
    if not token or token != make_application_token(**params):
        raise exceptions.InvalidToken

def get_timestamp(**params):
    try:
        return int(float(params['timestamp']))
    except KeyError:
        raise exceptions.MissingParameter('timestamp')
    except (ValueError, TypeError):
        raise exceptions.InvalidTimestamp

def verify_client_secret(client_id, client_secret):
    if not client_secret or not client_id or get_client_secret(client_id) != client_secret:
        raise exceptions.InvalidCredentials


def get_client_secret(client_id):
    try:
        return models.ClientPlatform.objects.get(client_id=client_id).client_secret
    except models.ClientPlatform.DoesNotExist:
        raise exceptions.InvalidCredentials
