import datetime
import hmac
import json
import logging
import pytz
import urllib.parse
import requests
from collections import OrderedDict
from django.conf import settings
from requests.exceptions import ConnectionError, ReadTimeout
from . import models


MEMO_API_USER = 'jepostule'
MEMO_API_TIMEOUT_SECONDS = 10
MEMO_API_JOB_APPLICATION_ENDPOINT_URL = '{}/candidature'.format(settings.MEMO_API_URL)


logger = logging.getLogger(__name__)


class TooManyRequests(Exception):
    pass


class RequestFailed(Exception):
    pass


def forward_job_application(job_application_id):
    job_application = models.JobApplication.objects.get(id=job_application_id)

    data = {
        "nomUtilisateur": job_application.candidate_last_name,
        "prenomUtilisateur": job_application.candidate_first_name,
        "emailUtilisateur": job_application.candidate_email,
        "telUtilisateur": job_application.candidate_phone,
        "adresseUtilisateur": job_application.candidate_address,
        "peId": job_application.candidate_peid,
        "romeRecherche": job_application.candidate_rome_code,
        "lettreMotivation": job_application.message,
        "numSiret": job_application.siret,
    }

    timestamp = make_timestamp()
    signature = make_signature(timestamp, user=MEMO_API_USER)

    url = MEMO_API_JOB_APPLICATION_ENDPOINT_URL
    params = OrderedDict([
        ('user', MEMO_API_USER),
        ('timestamp', timestamp),
        ('signature', signature),
    ])

    response = get_response(url, params, data)
    duplicate_msg = "Candidature has already saved"

    if response["result"] == "ok":
        return
    elif response["result"] == "error" and response["msg"] == duplicate_msg:
        # Memo chose to store only one job application per person and siret,
        # thus we silently ignore duplicates.
        return
    else:
        raise RequestFailed("response={}".format(response))


def make_timestamp():
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    return timestamp


def make_signature(timestamp, user):
    msg = "user={}&timestamp={}".format(user, timestamp)
    return hmac.new(settings.MEMO_API_SECRET.encode(), msg.encode()).hexdigest()


def get_response(url, params, data):
    """
    Generic method fetching the response for a POST request to a given
    url with a given data object.
    """
    headers = {
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(
            url=url,
            params=params,
            data=json.dumps(data),
            headers=headers,
            timeout=MEMO_API_TIMEOUT_SECONDS,
            verify=settings.MEMO_API_VERIFY_SSL,
        )
    except (ConnectionError, ReadTimeout) as e:
        logger.exception(e)
        raise e

    http_too_many_requests = 429
    if response.status_code == http_too_many_requests:
        raise TooManyRequests
    elif response.status_code >= 400:
        error = '{} responded with a {} error: {}'.format(
            url,
            response.status_code,
            response.content,
        )
        log_level = logging.WARNING if response.status_code >= 500 else logging.ERROR
        logger.log(log_level, error)
        raise RequestFailed("response={}".format(response))

    return response.json()
