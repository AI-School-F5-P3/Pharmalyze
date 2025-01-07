# kpi/urls.py
from django.urls import path
from . import views

app_name = 'kpi'

urlpatterns = [
    path('', views.kpi_dashboard, name='dashboard'),
    path('metrics/', views.metrics, name='metrics'),
]