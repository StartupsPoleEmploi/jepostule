import re

from django.conf import settings
import requests


def send(subject, html_content, from_email, recipients, reply_to=None, attachments=None):
    from_name, from_email = parse_contact(from_email)
    to_names_emails = [parse_contact(recipient) for recipient in recipients]
    response = post_api(
        "/send",
        {
            "Messages": [
                {
                    "From": {
                        "Name": from_name,
                        "Email": from_email,
                    },
                    "To": [{
                        "Name": recipient[0],
                        "Email": recipient[1],
                    } for recipient in to_names_emails],
                    "Subject": subject,
                    "HTMLPart": html_content,
                }
            ]
        }
    )
    return [message["MessageID"] for message in response["Messages"][0]["To"]]


def parse_contact(contact):
    """
    Args:
        contact (str): e.g "John Doe <john@doe.com>"
    Return:
        name (str): e.g "John Doe"
        email address (str): e.g "john@doe.com"
    """
    match = re.match(r'^(?P<name>[^<@]+) <(?P<email>.+@.+)>$', contact)
    if match:
        return match['name'], match['email']
    return "", contact

def post_api(endpoint, data):
    url = settings.MAILJET_API_BASE_URL + endpoint
    response = requests.post(
        url, json=data,
        auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET)
    )
    # In case of error, we just crash: it's important that the task queue
    # crashes, too, so failed messages can be tried again.
    if response.status_code >= 400:
        raise MailjetAPIError(response.status_code, response.content)
    return response.json()

class MailjetAPIError(Exception):
    pass
