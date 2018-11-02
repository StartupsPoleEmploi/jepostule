from django.contrib import admin

from .models import ClientPlatform


@admin.register(ClientPlatform)
class ClientPlatformAdmin(admin.ModelAdmin):
    list_display = ('client_id',)
    search_fields = ('client_id',)
    sortable_by = ('client_id',)
