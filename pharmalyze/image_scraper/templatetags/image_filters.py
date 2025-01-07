# image_scraper/templatetags/image_filters.py
from django import template
import os
import re

register = template.Library()

@register.filter
def filename(value):
    """Returns the filename from a path."""
    return os.path.splitext(os.path.basename(value))[0]

@register.filter
def format_title(value):
    """Formats the filename into a clean title."""
    # Remove the page and number information
    clean_name = re.sub(r'_page\d+_\d+$', '', value)
    # Replace underscores with spaces and capitalize each word
    return ' '.join(word.capitalize() for word in clean_name.split('_'))