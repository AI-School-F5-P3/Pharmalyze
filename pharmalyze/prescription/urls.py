# prescription/urls.py
from django.urls import path
from . import views

app_name = 'prescription'

urlpatterns = [
    path('', views.prescription_upload, name='upload'),
    path('analyze/<int:prescription_id>/', views.analyze_prescription, name='analyze'),
    path('results/<int:prescription_id>/', views.prescription_results, name='results'),
    path('history/', views.prescription_history, name='history'),
]