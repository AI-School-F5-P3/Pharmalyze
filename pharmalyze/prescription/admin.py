# prescription/admin.py
from django.contrib import admin
from .models import Prescription

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_at', 'status')
    list_filter = ('status', 'uploaded_at')
    readonly_fields = ('processed_text',)