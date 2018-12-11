import csv
from django.core.management.base import BaseCommand

from jepostule.pipeline import models


class Command(BaseCommand):
    help = """
Dump answer information with related job application to CSV.
"""

    def add_arguments(self, parser):
        parser.add_argument(
            'client_id',
            help="Platform client ID of the platform (e.g: 'lbb')",
        )
        parser.add_argument(
            'dst',
            help="Destination csv file path",
        )

    def handle(self, *args, **options):
        with open(options['dst'], 'w') as f:
            write_csv(f, options['client_id'])


def write_csv(file_obj, client_id):
    writer = csv.writer(file_obj)
    writer.writerow((
        'Job application id',
        'Job application created at',
        'Employer name',
        'Employer email',
        'Employer siret',
        'Candidate first name',
        'Candidate last name',
        'Candidate email',
        'Candidate phone',
        'Candidate address',
        'Job',
        'Answer created at',
        'Answer type',
    ))
    query = models.Answer.objects.filter(job_application__client_platform__client_id=client_id).select_related(
        'job_application',
        'answerinterview',
        'answerrejection',
        'answerrequestinfo',
    ).order_by('-job_application__id').all()
    for answer in query:
        answer_details = answer.get_details()
        writer.writerow((
            answer.job_application.id,
            answer.job_application.created_at,
            answer.job_application.employer_description,
            answer.job_application.employer_email,
            answer.job_application.siret,
            answer.job_application.candidate_first_name,
            answer.job_application.candidate_last_name,
            answer.job_application.candidate_email,
            answer.job_application.candidate_phone,
            answer.job_application.candidate_address,
            answer.job_application.job,
            answer.created_at,
            answer_details.type_name,
        ))
