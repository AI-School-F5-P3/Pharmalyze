# stock/urls.py
from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('', views.StockManagementView.as_view(), name='stock_management'),
    path('download/', views.download_excel, name='download_excel'),
    path('clear/', views.clear_products, name='clear_products'),
]