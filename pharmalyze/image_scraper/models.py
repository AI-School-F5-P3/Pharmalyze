# image_scraper/models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
    category = models.CharField(max_length=100)
    image_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProductInfo(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    description = models.TextField()
    usage = models.TextField()
    composition = models.TextField()
    price_per_unit = models.CharField(max_length=50)
    expert_advice = models.TextField()
    expert_info = models.JSONField(default=dict)
    raw_data = models.JSONField(default=dict)

    def __str__(self):
        return f"Info for {self.product.name}"