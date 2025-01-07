# product_search/urls.py
from django.urls import path
from . import views

app_name = 'product_search'


urlpatterns = [
    path('', views.search_view, name='product_search'),
    path('search/', views.search_view, name='search_post'),
]