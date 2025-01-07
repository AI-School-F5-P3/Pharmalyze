# product_search/models.py
from django.db import models
from django.core.files.storage import default_storage

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    image_path = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict)
    embedding = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_image_url(self):
        if self.image_path and default_storage.exists(self.image_path):
            return default_storage.url(self.image_path)
        return None

class KnowledgeBase(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=100)
    source_type = models.CharField(max_length=50)  # 'pdf', 'text', etc.
    source_path = models.CharField(max_length=255, null=True)
    metadata = models.JSONField(default=dict)
    embedding = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['source_type']),
        ]
    
    def __str__(self):
        return self.title