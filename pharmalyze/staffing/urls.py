# staffing/urls.py
from django.urls import path
from . import views

app_name = 'staffing'

urlpatterns = [
    path('', views.staff_dashboard, name='dashboard'),
    path('schedule/', views.schedule, name='schedule'),
]