import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from pathlib import Path
from .scraper import RobustWebScraper
from django.http import JsonResponse
import json
from threading import Thread, Lock
import queue
from django.conf import settings
import re
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.core.cache import cache

# Global variables for tracking progress
scraping_progress = queue.Queue()
current_progress = {'total': 0, 'current': 0}
scraper_lock = Lock()
active_scraper = None

@ensure_csrf_cookie
def home(request):
    return render(request, 'home.html')

@require_http_methods(["POST"])
def start_scraping(request):
    if cache.get('scraping_in_progress'):
        return JsonResponse({'status': 'error', 'message': 'Scraping already in progress'})
    
    cache.set('scraping_in_progress', True, timeout=3600)  # 1 hour timeout
    
    global active_scraper
    
    def scrape_task():
        global active_scraper
        try:
            with scraper_lock:
                if active_scraper is None:
                    active_scraper = RobustWebScraper(progress_callback=update_progress)
                total_downloads = active_scraper.scrape_images()
                scraping_progress.put(('complete', total_downloads))
        except Exception as e:
            scraping_progress.put(('error', str(e)))
        finally:
            with scraper_lock:
                if active_scraper:
                    try:
                        active_scraper.driver.quit()
                    except:
                        pass
                    active_scraper = None
    
    # Reset progress
    current_progress['total'] = 0
    current_progress['current'] = 0
    
    Thread(target=scrape_task).start()
    return JsonResponse({'status': 'started'})

def update_progress(current, total):
    current_progress['current'] = current
    current_progress['total'] = total

def get_progress(request):
    try:
        status, data = scraping_progress.get_nowait()
        if status == 'complete':
            cache.delete('scraping_in_progress')
        return JsonResponse({'status': status, 'data': data})
    except queue.Empty:
        if current_progress['total'] > 0:
            percentage = int((current_progress['current'] / current_progress['total']) * 100)
            return JsonResponse({
                'status': 'in_progress',
                'progress': percentage,
                'current': current_progress['current'],
                'total': current_progress['total']
            })
        return JsonResponse({'status': 'in_progress', 'progress': 0})

@require_http_methods(["GET"])
def scrape_images_view(request):
    # Redirect to start_scraping instead of creating a new scraper instance
    return redirect('image_scraper:start_scraping')

def format_title(filename):
    # Remove the page and number information (e.g., "page1_41")
    clean_name = re.sub(r'_page\d+_\d+$', '', filename)
    # Replace underscores with spaces and capitalize each word
    return ' '.join(word.capitalize() for word in clean_name.split('_'))

def get_scraped_images():
    # Use MEDIA_ROOT from Django settings
    base_dir = Path(settings.MEDIA_ROOT) / 'images' / 'Dietetica' / 'Adelgazar'
    images = []
    
    if base_dir.exists():
        for category in base_dir.iterdir():
            if category.is_dir():
                for image_path in category.glob('**/*'):
                    if image_path.is_file() and image_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        # Create URL-friendly path relative to MEDIA_ROOT
                        relative_path = image_path.relative_to(Path(settings.MEDIA_ROOT))
                        images.append({
                            'path': str(relative_path).replace('\\', '/'),
                            'category': category.name,
                            'name': format_title(image_path.stem)
                        })
    
    return images

def product_list_view(request):
    images = get_scraped_images()
    search_query = request.GET.get('search', '').lower()
    image_data = {}
    
    # Filter and organize images by category
    for image in images:
        category = image['category']
        
        # Only process if we have valid string paths
        if isinstance(image['path'], str):
            # If there's a search query, only include matching items
            if search_query:
                if (search_query in image['name'].lower() or 
                    search_query in category.lower()):
                    if category not in image_data:
                        image_data[category] = []
                    image_data[category].append({
                        'path': image['path'],
                        'title': image['name']
                    })
            else:
                # No search query, include all items
                if category not in image_data:
                    image_data[category] = []
                image_data[category].append({
                    'path': image['path'],
                    'title': image['name']
                })
    
    return render(request, 'image_scraper/product_list.html', {
        'image_data': image_data,
        'MEDIA_URL': settings.MEDIA_URL,
        'search_query': search_query
    })