import logging

from jepostule.queue import topics
from jepostule.security import blacklist
from . import models


# Special care should be taken about the destination of this logger: event logs
# are precious for analysis.
logger = logging.getLogger(__name__)

def receive(event):
    logger.info(event)
    process.run_async(event)

@topics.subscribe('process-email-event')
def process(event):
    email_status = {
        "sent": models.Email.SENT,
        "open": models.Email.OPENED,
        "spam": models.Email.SPAM,
        "blocked": models.Email.BLOCKED,
    }.get(event.get("event"))

    update_email_status(event.get("MessageID"), email_status)
    if email_status in [models.Email.SPAM, models.Email.BLOCKED]:
        process_refused(event, email_status)

def process_refused(event, email_status):
    email = event.get("email")
    if email:
        try:
            timestamp = int(event.get("time"))
        except (TypeError, ValueError):
            # Even if the timestamp is incorrect, we still need to blacklist the
            # email address
            timestamp = None
        blacklist.add(email, email_status, timestamp=timestamp)

def update_email_status(message_id, email_status):
    try:
        message_id = int(message_id)
    except (TypeError, ValueError):
        return
    if email_status not in dict(models.Email.STATUSES):
        return
    models.Email.objects.filter(message_id=message_id).update(status=email_status)
