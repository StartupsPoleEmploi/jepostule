from django.db import models


class JobApplication(models.Model):
    """
    Store all application-related data, except for the attachments.
    """
    candidate_email = models.CharField(max_length=64, db_index=True)
    employer_email = models.CharField(max_length=64, db_index=True)
    job = models.CharField(max_length=256)
    message = models.TextField(max_length=4000)
    coordinates = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']


class JobApplicationEvent(models.Model):
    """
    All events associated to a specific application. Events are created every
    time an action related to the application is performed.
    """
    NAME_SENT_TO_EMPLOYER = 'sent'
    NAME_CONFIRMED_TO_CANDIDATE = 'confirmed'
    NAMES = (
        (NAME_SENT_TO_EMPLOYER, 'Sent to employer'),
        (NAME_CONFIRMED_TO_CANDIDATE, 'Confirmed to candidate'),
    )

    job_application = models.ForeignKey(
        JobApplication, on_delete=models.CASCADE, related_name='events'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    name = models.CharField(choices=NAMES, max_length=32, db_index=True, blank=False)
    value = models.CharField(max_length=256, blank=True)

    class Meta:
        ordering = ['created_at']
