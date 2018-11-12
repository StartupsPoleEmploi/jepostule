import os

from django.core import mail


# pylint: disable=too-many-arguments
def send_mail(subject, html_content, from_email, recipient_list,
              reply_to=None, attachments=None):
    """
    We don't rely on django.core.mail.send_mail function, because it does not
    let us override the 'reply-to' field.

    Note that `reply_to` must be a list or tuple.

    As long as the async tasks trigger only one email each, it is not necessary
    to run the send_mail function asynchronously.
    """
    if attachments:
        attachments = [
            (os.path.basename(f.name), f.content, None) for f in attachments
        ]
    if reply_to is not None and not isinstance(reply_to, tuple) and not isinstance(reply_to, list):
        raise ValueError("'reply_to' is of invalid type {}".format(reply_to.__class__))
    connection = mail.get_connection()
    message = mail.EmailMultiAlternatives(
        subject, html_content, from_email, recipient_list,
        connection=connection,
        reply_to=reply_to,
        attachments=attachments,
    )
    message.attach_alternative(html_content, 'text/html')

    return message.send()
