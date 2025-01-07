# image_scraper/urls.py
from django.urls import path
from . import views

app_name = 'image_scraper'

urlpatterns = [
    path('', views.home, name='home'),
    path('scrape/', views.scrape_images_view, name='scrape_images'),
    path('products/', views.product_list_view, name='product_list'),
    path('progress/', views.get_progress, name='get_progress'),
    path('start-scraping/', views.start_scraping, name='start_scraping'),
]