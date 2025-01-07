# stock/models.py
from django.db import models

class StockConfig(models.Model):
    PHARMACY_TYPES = [
        ('normal', 'Normal (300 días)'),
        ('24h', '24 Horas (365 días)'),
        ('libre', 'Libre'),
    ]
    
    pharmacy_type = models.CharField(max_length=10, choices=PHARMACY_TYPES, default='normal')
    custom_days = models.IntegerField(null=True, blank=True)
    min_coverage_days = models.IntegerField(default=10)
    max_coverage_days = models.IntegerField(default=40)
    optimal_coverage_days = models.IntegerField(default=22)
    
    def get_open_days(self):
        if self.pharmacy_type == 'normal':
            return 300
        elif self.pharmacy_type == '24h':
            return 365
        else:
            return self.custom_days or 279

class Product(models.Model):
    CATEGORIES = [
        ('AA', 'Rotación máxima'),
        ('A', 'Rotación muy alta'),
        ('BB', 'Rotación alta'),
        ('B', 'Rotación alta/media'),
        ('CC', 'Rotación media'),
        ('C', 'Rotación media/baja'),
        ('DD', 'Rotación muy baja'),
        ('D', 'Rotación nula'),
    ]
    
    id_articu = models.IntegerField(unique=True)
    descripcion = models.CharField(max_length=255)
    min_farmacia = models.IntegerField(default=0)
    max_farmacia = models.IntegerField(default=0)
    stock_actual = models.IntegerField(default=0)
    pvp = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Monthly sales fields
    sales_jan = models.IntegerField(default=0)
    sales_feb = models.IntegerField(default=0)
    sales_mar = models.IntegerField(default=0)
    sales_apr = models.IntegerField(default=0)
    sales_may = models.IntegerField(default=0)
    sales_jun = models.IntegerField(default=0)
    sales_jul = models.IntegerField(default=0)
    sales_aug = models.IntegerField(default=0)
    sales_sep = models.IntegerField(default=0)
    sales_oct = models.IntegerField(default=0)
    sales_nov = models.IntegerField(default=0)
    sales_dec = models.IntegerField(default=0)
    
    # Calculated fields
    category = models.CharField(max_length=2, choices=CATEGORIES)
    daily_sales = models.DecimalField(max_digits=10, decimal_places=2)
    min_stock = models.IntegerField()
    max_stock = models.IntegerField()
    optimal_stock = models.IntegerField()
    stock_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    def calculate_total_sales(self):
        total = 0
        for field in self.__dict__.keys():
            if field.startswith('sales_'):
                total += getattr(self, field, 0)
        return total
    
    def calculate_category(self, annual_sales):
        if annual_sales > 300:
            return 'AA'
        elif annual_sales >= 150:
            return 'A'
        elif annual_sales >= 95:
            return 'BB'
        elif annual_sales >= 50:
            return 'B'
        elif annual_sales >= 30:
            return 'CC'
        elif annual_sales >= 3:
            return 'C'
        elif annual_sales > 1:
            return 'DD'
        return 'D'
    
    def calculate_daily_sales(self, open_days):
        total_sales = self.calculate_total_sales()
        return total_sales / open_days if open_days else 0
    
    def calculate_min_stock(self, daily_sales, category, min_coverage_days):
        if category in ['AA', 'A', 'BB', 'B']:
            return daily_sales * min_coverage_days
        elif category == 'CC':
            return 1
        elif category == 'C':
            return 0
        return 0
    
    def calculate_max_stock(self, daily_sales, category, max_coverage_days):
        if category in ['AA', 'A', 'BB', 'B']:
            return daily_sales * max_coverage_days
        elif category == 'CC':
            return 2
        elif category == 'C':
            return 1
        return 0
    
    def calculate_optimal_stock(self, daily_sales, category, optimal_days):
        if category in ['AA', 'A', 'BB', 'B']:
            return daily_sales * optimal_days
        elif category in ['CC', 'C']:
            return 2 if category == 'CC' else 1
        return 0
    
    def update_calculated_fields(self, config):
        open_days = config.get_open_days()
        self.daily_sales = self.calculate_daily_sales(open_days)
        annual_sales = self.daily_sales * open_days
        self.category = self.calculate_category(annual_sales)
        
        self.min_stock = self.calculate_min_stock(
            self.daily_sales, self.category, config.min_coverage_days)
        self.max_stock = self.calculate_max_stock(
            self.daily_sales, self.category, config.max_coverage_days)
        self.optimal_stock = self.calculate_optimal_stock(
            self.daily_sales, self.category, config.optimal_coverage_days)
        
        self.stock_value = self.stock_actual * self.pvp
        
    def get_monthly_sales(self):
        """Return a list of monthly sales values in order"""
        sales = []
        for field in sorted(self.__dict__.keys()):
            if field.startswith('sales_'):
                sales.append(getattr(self, field))
        return sales