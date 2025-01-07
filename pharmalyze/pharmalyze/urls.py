# pharmalyze/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from image_scraper import views as image_scraper_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', image_scraper_views.home, name='global_home'),
    path('image_scraper/', include('image_scraper.urls')),
    path('search/', include('product_search.urls', namespace='product_search')),
    path('stock/', include('stock.urls', namespace='stock')),
    path('prescription/', include('prescription.urls', namespace='prescription')),
    path('staffing/', include('staffing.urls', namespace='staffing')),
    path('kpi/', include('kpi.urls', namespace='kpi')),
    # URL patterns for authentication
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)