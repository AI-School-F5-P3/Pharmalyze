# kpi/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def kpi_dashboard(request):
    context = {
        'total_sales': 0,  # Replace with actual data
        'total_products': 0,
        'average_order_value': 0,
    }
    return render(request, 'kpi/dashboard.html', context)

@login_required
def metrics(request):
    context = {
        'daily_metrics': {},  # Replace with actual metrics
        'monthly_metrics': {},
    }
    return render(request, 'kpi/metrics.html', context)