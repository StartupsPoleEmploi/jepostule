from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from jepostule.pipeline.models import JobApplication


class ViewsTests(TestCase):

    def setUp(self):
        user = User.objects.create(username='john')
        user.set_password('password')
        user.save()
        self.assertTrue(self.client.login(username='john', password='password'))

    def test_email_application(self):
        job_application = JobApplication.objects.create()
        response = self.client.get(reverse(
            'pipeline:email_application',
            kwargs={'job_application_id': job_application.id}
        ))
        self.assertEqual(200, response.status_code)

    def test_email_confirmation(self):
        job_application = JobApplication.objects.create()
        response = self.client.get(reverse(
            'pipeline:email_confirmation',
            kwargs={'job_application_id': job_application.id}
        ))
        self.assertEqual(200, response.status_code)
