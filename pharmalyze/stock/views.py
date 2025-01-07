# pharmalyze/stock/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import HttpResponse
from .models import StockConfig, Product
import pandas as pd
from datetime import datetime
import re

class StockManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'stock/stock.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config'] = StockConfig.objects.first()
        products = Product.objects.all().order_by('id_articu')
        context['products'] = products
        
        if products.exists():
            sales_columns = []
            for field in products.first().__dict__.keys():
                if field.startswith('sales_'):
                    month_name = field.replace('sales_', '').title()
                    sales_columns.append(month_name)
            context['sales_months'] = sales_columns
            
        return context

    def handle_excel_upload(self, request):
        excel_file = request.FILES['excel_file']
        
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            raise ValueError("Invalid file format. Please upload an Excel file (.xlsx or .xls)")
        
        try:
            df = pd.read_excel(excel_file)
            required_columns = ['IdArticu', 'Descripcion', 'Stock Actual', 'PVP']
            
            # Validate required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            config = StockConfig.objects.first() or StockConfig()
            
            # Clear existing products
            Product.objects.all().delete()
            
            # Identify sales columns (any column that contains numbers)
            sales_columns = []
            for col in df.columns:
                # Convert column name to string if it's a datetime
                col_str = str(col).lower() if isinstance(col, datetime) else str(col)
                if any(char.isdigit() for char in col_str):
                    sales_columns.append(col)
            
            # Process each row
            for _, row in df.iterrows():
                try:
                    product = Product(
                        id_articu=int(row['IdArticu']),
                        descripcion=str(row['Descripcion']),
                        min_farmacia=int(row.get('Min Farmacia', 0)),
                        max_farmacia=int(row.get('Max Farmacia', 0)),
                        stock_actual=int(row['Stock Actual']),
                        pvp=float(row['PVP'])
                    )
                    
                    # Process sales data dynamically
                    for col in sales_columns:
                        # Convert column name to string if it's a datetime
                        col_str = str(col).lower() if isinstance(col, datetime) else str(col).lower()
                        # Extract month from column name
                        month_match = re.search(r'(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)', col_str)
                        if month_match:
                            month = month_match.group(1)
                            month_map = {
                                'ene': 'jan', 'feb': 'feb', 'mar': 'mar', 'abr': 'apr',
                                'may': 'may', 'jun': 'jun', 'jul': 'jul', 'ago': 'aug',
                                'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dic': 'dec'
                            }
                            field_name = f'sales_{month_map[month]}'
                            setattr(product, field_name, int(row.get(col, 0)))
                    
                    product.update_calculated_fields(config)
                    product.save()
                    
                except Exception as e:
                    raise ValueError(f"Error processing row {row['IdArticu']}: {str(e)}")
                    
        except pd.errors.EmptyDataError:
            raise ValueError("The uploaded file is empty")
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")
    
    def post(self, request, *args, **kwargs):
        try:
            if 'config_form' in request.POST:
                config = StockConfig.objects.first() or StockConfig()
                config.pharmacy_type = request.POST.get('pharmacy_type')
                config.custom_days = int(request.POST.get('custom_days')) if request.POST.get('custom_days') else None
                config.min_coverage_days = int(request.POST.get('min_coverage_days'))
                config.max_coverage_days = int(request.POST.get('max_coverage_days'))
                config.optimal_coverage_days = int(request.POST.get('optimal_coverage_days'))
                config.save()
                messages.success(request, 'Configuración actualizada correctamente.')
                
            elif 'excel_file' in request.FILES:
                self.handle_excel_upload(request)
                messages.success(request, 'Archivo procesado correctamente.')
                
            return redirect('stock:stock_management')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('stock:stock_management')

def download_excel(request):
    """Generate and download Excel report with calculated fields"""
    try:
        # Get all products
        products = Product.objects.all().order_by('id_articu')
        
        # Create DataFrame
        data = []
        for product in products:
            row = {
                'Código Nacional': product.id_articu,
                'Descripción': product.descripcion,
                'Stock Actual': product.stock_actual,
                'Min Calculado': product.min_stock,
                'Min Configurado': product.min_farmacia,
                'Max Calculado': product.max_stock,
                'Max Configurado': product.max_farmacia,
                'Stock Óptimo': product.optimal_stock,
                'Ventas Diarias': round(float(product.daily_sales), 1),
                'Categoría': product.category,
                'Valor Stock': float(product.stock_value),
                'PVP': float(product.pvp)
            }
            
            # Add monthly sales dynamically
            for field in product.__dict__.keys():
                if field.startswith('sales_'):
                    month_name = field.replace('sales_', '').title()
                    row[f'Ventas {month_name}'] = getattr(product, field)
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Create response
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename=stock_report_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        
        # Write to Excel
        df.to_excel(response, index=False, engine='openpyxl')
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating Excel file: {str(e)}')
        return redirect('stock:stock_management')
    
def clear_products(request):
    if request.method == 'POST':
        Product.objects.all().delete()
        messages.success(request, 'Todos los productos han sido eliminados.')
    return redirect('stock:stock_management')