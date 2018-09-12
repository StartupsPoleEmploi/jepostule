from django.contrib import admin

from .models import JobApplication, JobApplicationEvent


class JobApplicationEventInlineAdmin(admin.TabularInline):
    model = JobApplicationEvent
    readonly_fields = ('created_at', 'name', 'value',)
    extra = 0


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('id', 'candidate_email', 'employer_email',)
    list_display_links = ('id', 'candidate_email', 'employer_email',)
    ordering = ('-created_at',)
    search_fields = ('created_at', 'candidate_email', 'employer_email', 'job', 'coordinates',)
    sortable_by = ('created_at', 'candidate_email', 'employer_email',)
    inlines = (JobApplicationEventInlineAdmin,)


@admin.register(JobApplicationEvent)
class JobApplicationEventAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('id', 'name', 'value', 'candidate_email', 'employer_email',)
    list_display_links = ('id', 'name', 'value',)
    ordering = ('-created_at',)
    search_fields = ('created_at', 'job_application', 'name',)
    sortable_by = ('created_at', 'job_application', 'name',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('job_application')

    def candidate_email(self, obj):
        return obj.job_application.candidate_email

    def employer_email(self, obj):
        return obj.job_application.employer_email
