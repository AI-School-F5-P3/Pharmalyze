# prescription/forms.py
from django import forms
from .models import Prescription

class PrescriptionUploadForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['image']