from time import time
import hashlib

from django.conf import settings

from . import exceptions
from . import models


# Duration during which a token is valid, in seconds. This value should be
# greater than the time required to upload documents.
TOKEN_VALIDITY_SECONDS = 30*60


def make_new_application_token(client_id, candidate_email, employer_email):
    timestamp = int(time())
    return make_application_token(client_id, candidate_email, employer_email, timestamp), timestamp


def make_application_token(client_id, candidate_email, employer_email, timestamp):
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
    client_secret = get_client_secret(client_id)
    string = settings.SECRET_KEY + client_secret
    string += candidate_email.lower() + employer_email.lower()
    string += str(int(timestamp))
    return hashlib.sha256(string.encode()).hexdigest()


def verify_application_token(token, client_id, candidate_email, employer_email, timestamp):
    try:
        timestamp = int(float(timestamp))
    except (ValueError, TypeError):
        raise exceptions.InvalidTimestamp
    if timestamp + TOKEN_VALIDITY_SECONDS < time():
        raise exceptions.TokenExpiredError
    if not token or token != make_application_token(client_id, candidate_email, employer_email, timestamp):
        raise exceptions.InvalidToken


def verify_client_secret(client_id, client_secret):
    if not client_secret or get_client_secret(client_id) != client_secret:
        raise exceptions.InvalidCredentials


def get_client_secret(client_id):
    try:
        return models.ClientPlatform.objects.get(client_id=client_id).client_secret
    except models.ClientPlatform.DoesNotExist:
        raise exceptions.InvalidCredentials
