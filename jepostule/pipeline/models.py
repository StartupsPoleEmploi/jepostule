import uuid

from django.conf import settings
from django.db import models

from jepostule.auth.models import ClientPlatform


class JobApplication(models.Model):
    """
    Store all application-related data, except for the attachments.
    """
    candidate_email = models.CharField(max_length=64, db_index=True)
    candidate_first_name = models.CharField(max_length=64)
    candidate_last_name = models.CharField(max_length=64)
    candidate_phone = models.CharField(max_length=32)
    candidate_address = models.CharField(max_length=256)
    candidate_peid = models.CharField(max_length=64, db_index=True)
    employer_email = models.CharField(max_length=64, db_index=True)
    employer_description = models.CharField(max_length=256)
    message = models.TextField(max_length=4000)
    job = models.CharField(max_length=128)
    siret = models.CharField(max_length=14, db_index=True)
    answer_uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    client_platform = models.ForeignKey(ClientPlatform, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    @property
    def candidate_name(self):
        return "{} {}".format(self.candidate_first_name, self.candidate_last_name)

    @property
    def answer_types(self):
        return Answer.Types

    DEFAULT_PLATFORM_ATTRIBUTES = {
        'contact_email': settings.JEPOSTULE_NO_REPLY,
        'name': 'La Bonne Boite',
    }

    def platform_attribute(self, key):
        """
        Attributes are platform-specific key/values set in the django settings.
        This is a quick'n dirty way to have different templates and values for
        different platforms. In the future, we should probably store these
        values in the database.
        """
        default = self.DEFAULT_PLATFORM_ATTRIBUTES[key]  # Fail early if key does not exist
        try:
            return settings.PLATFORM_ATTRIBUTES.get(self.client_platform.client_id, {})[key]
        except (ClientPlatform.DoesNotExist, KeyError):
            return default


class JobApplicationEvent(models.Model):
    """
    All events associated to a specific application. Events are created every
    time an action related to the application is performed.
    """
    SENT_TO_EMPLOYER = 'sent'
    CONFIRMED_TO_CANDIDATE = 'confirmed'
    ANSWERED = 'answered'
    NAMES = (
        (SENT_TO_EMPLOYER, "Envoyé à l'employeur"),
        (CONFIRMED_TO_CANDIDATE, "Confirmation envoyée au candidat"),
        (ANSWERED, "Réponse envoyée au candidat"),
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
    application, the corresponding detailed answer can be accessed with:

        job_application.answer.answersomething

    Or:

        job_application.answer.get_details()
    """
    class Types:
        REJECTION = 0
        REQUEST_INFO = 1
        INTERVIEW = 2
        ALL = {
            REJECTION: 'Rejection',
            REQUEST_INFO: 'Request info',
            INTERVIEW: 'Interview',
        }

    job_application = models.OneToOneField(JobApplication, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_details(self):
        """
        Return the child answer object.

        Unfortunately, the chosen model representation does not prevent the
        user from creating both an AnswerInterview and an AnswerRejection (for
        example) for the same job application. But it's the only way to do it
        (AFAIK) with separate tables. That means that this method returns only
        the first child object found. But in practice, we make sure that no
        Answer object exists when we create a new child object.
        """
        attributes = ['answerrejection', 'answerrequestinfo', 'answerinterview']
        for attribute in attributes:
            if hasattr(self, attribute):
                return getattr(self, attribute)
        raise AttributeError('details')


class DetailedAnswerMixin:

    @property
    def type_name(self):
        return self.Types.ALL[self.answer_type]


class AnswerRejection(Answer, DetailedAnswerMixin):
    answer_type = Answer.Types.REJECTION

    REASON_UNKNOWN = 'unknown'
    REASON_NO_VACANCY = 'novacancy'
    REASON_EXPERIENCE = 'experience'
    REASON_SKILLS = 'skills'
    REASON_EDUCATION = 'education'
    REASONS = [
        (REASON_UNKNOWN, "Je préfère ne pas expliciter"),
        (REASON_NO_VACANCY, "Pas de poste de ce type disponible pour le moment"),
        (REASON_EXPERIENCE, "Expérience non adaptée au poste au sein de notre entreprise"),
        (REASON_SKILLS, "Compétences non adaptées au poste au sein de notre entreprise"),
        (REASON_EDUCATION, "Formations/Qualifications insuffisantes/inadaptées au poste au sein de notre entreprise"),
    ]
    reason = models.CharField(
        max_length=16, blank=False,
        choices=REASONS,
        default=REASON_UNKNOWN,
    )
    message = models.TextField(blank=True)

    @property
    def reason_verbose(self):
        return dict(self.REASONS)[self.reason]


class AnswerEmployerInfo(Answer):
    employer_name = models.CharField(max_length=128, blank=False)
    employer_email = models.EmailField(max_length=128, blank=False)
    employer_phone = models.CharField(max_length=32, blank=False)
    employer_address = models.CharField(max_length=256, blank=False)
    message = models.TextField(blank=False)

    class Meta:
        abstract = True


class AnswerRequestInfo(AnswerEmployerInfo, DetailedAnswerMixin):
    answer_type = Answer.Types.REQUEST_INFO


class AnswerInterview(AnswerEmployerInfo, DetailedAnswerMixin):
    answer_type = Answer.Types.INTERVIEW

    LOCATION_ONSITE = 'onsite'
    LOCATION_PHONE = 'phone'
    LOCATION_VIDEO = 'video'
    LOCATIONS = dict((
        (LOCATION_ONSITE, "dans l'entreprise"),
        (LOCATION_PHONE, "par téléphone"),
        (LOCATION_VIDEO, "en visio conférence"),
    ))

    datetime = models.DateTimeField(blank=False)
    location = models.CharField(
        max_length=16, blank=False,
        choices=LOCATIONS.items(),
        default=LOCATION_ONSITE,
    )

    @property
    def location_verbose(self):
        return self.LOCATIONS[self.location]
