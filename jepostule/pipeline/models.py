import uuid

from django.db import models


class JobApplication(models.Model):
    """
    Store all application-related data, except for the attachments.
    """
    ANSWER_REJECTION = 0
    ANSWER_DETAILS = 1
    ANSWER_INTERVIEW = 2

    candidate_email = models.CharField(max_length=64, db_index=True)
    candidate_first_name = models.CharField(max_length=64)
    candidate_last_name = models.CharField(max_length=64)
    candidate_phone = models.CharField(max_length=32)
    candidate_address = models.CharField(max_length=256)
    employer_email = models.CharField(max_length=64, db_index=True)
    employer_description = models.CharField(max_length=256)
    message = models.TextField(max_length=4000)
    job = models.CharField(max_length=128)
    siret = models.CharField(max_length=14, db_index=True)
    answer_uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    @property
    def candidate_name(self):
        return "{} {}".format(self.candidate_first_name, self.candidate_last_name)


class JobApplicationEvent(models.Model):
    """
    All events associated to a specific application. Events are created every
    time an action related to the application is performed.
    """
    SENT_TO_EMPLOYER = 'sent'
    CONFIRMED_TO_CANDIDATE = 'confirmed'
    NAMES = (
        (SENT_TO_EMPLOYER, "Envoyé à l'employeur"),
        (CONFIRMED_TO_CANDIDATE, "Confirmation envoyée au candidat"),
    )

    job_application = models.ForeignKey(
        JobApplication, on_delete=models.CASCADE, related_name='events'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    name = models.CharField(choices=NAMES, max_length=32, db_index=True, blank=False)
    value = models.CharField(max_length=256, blank=True)

    class Meta:
        ordering = ['created_at']


class Answer(models.Model):
    """
    There exists multiple different answer types to job application. From a job
    application, the corresponding answer can be accessed with:

        job_application.answer.answerinterview
    """
    job_application = models.OneToOneField(JobApplication, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class AnswerInterview(Answer):
    LOCATION_ONSITE = 'onsite'
    LOCATION_PHONE = 'phone'
    LOCATION_VIDEO = 'video'

    datetime = models.DateTimeField(blank=True)
    location = models.CharField(
        max_length=16, blank=False,
        choices=(
            (LOCATION_ONSITE, "dans l'entreprise"),
            (LOCATION_PHONE, "par téléphone"),
            (LOCATION_VIDEO, "en visio conférence"),
        ),
        default=LOCATION_ONSITE,
    )
    employer_name = models.CharField(max_length=128, blank=True)
    employer_email = models.EmailField(max_length=128, blank=True)
    employer_phone = models.CharField(max_length=32, blank=True)
    employer_address = models.CharField(max_length=256, blank=True)
    message = models.TextField(blank=True)
