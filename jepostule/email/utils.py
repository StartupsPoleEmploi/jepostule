import importlib
import os

from django.conf import settings


# pylint: disable=too-many-arguments
def send_mail(subject, html_content, from_email, recipient_list,
              from_name=None, reply_to=None, attachments=None):
    """
    We don't rely on django.core.mail.send_mail function, because it does not
    let us override the 'reply-to' field.

    Note that `reply_to` must be a list or a tuple.

    As long as the async tasks trigger only one email each, it is not necessary
    to run the send_mail function asynchronously.

    Returns:
        message IDs (int/None list): the list of message ID associated to each
        recipient. This list has the same size as the recipient list. When no
        message ID is available, it is None.
    """
    if attachments:
        attachments = [
            (os.path.basename(f.name), f.content, None) for f in attachments
        ]
    if reply_to and not isinstance(reply_to, (tuple, list)):
        raise ValueError("'reply_to' is of invalid type {}".format(reply_to.__class__))

    return importlib.import_module(settings.EMAIL_SENDING_MODULE).send(
        subject, html_content, from_email, recipient_list,
        from_name=from_name, reply_to=reply_to, attachments=attachments
    )
