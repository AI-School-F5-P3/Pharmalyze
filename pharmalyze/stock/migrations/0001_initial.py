# Generated by Django 5.1.4 on 2024-12-23 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_articu', models.IntegerField(unique=True)),
                ('descripcion', models.CharField(max_length=255)),
                ('min_farmacia', models.IntegerField(default=0)),
                ('max_farmacia', models.IntegerField(default=0)),
                ('stock_actual', models.IntegerField(default=0)),
                ('pvp', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sales_jan', models.IntegerField(default=0)),
                ('sales_feb', models.IntegerField(default=0)),
                ('sales_mar', models.IntegerField(default=0)),
                ('sales_apr', models.IntegerField(default=0)),
                ('sales_may', models.IntegerField(default=0)),
                ('sales_jun', models.IntegerField(default=0)),
                ('sales_jul', models.IntegerField(default=0)),
                ('sales_aug', models.IntegerField(default=0)),
                ('sales_sep', models.IntegerField(default=0)),
                ('sales_oct', models.IntegerField(default=0)),
                ('sales_nov', models.IntegerField(default=0)),
                ('sales_dec', models.IntegerField(default=0)),
                ('category', models.CharField(choices=[('AA', 'Rotación máxima'), ('A', 'Rotación muy alta'), ('BB', 'Rotación alta'), ('B', 'Rotación alta/media'), ('CC', 'Rotación media'), ('C', 'Rotación media/baja'), ('DD', 'Rotación muy baja'), ('D', 'Rotación nula')], max_length=2)),
                ('daily_sales', models.DecimalField(decimal_places=2, max_digits=10)),
                ('min_stock', models.IntegerField()),
                ('max_stock', models.IntegerField()),
                ('optimal_stock', models.IntegerField()),
                ('stock_value', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='StockConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pharmacy_type', models.CharField(choices=[('normal', 'Normal (300 días)'), ('24h', '24 Horas (365 días)'), ('libre', 'Libre')], default='normal', max_length=10)),
                ('custom_days', models.IntegerField(blank=True, null=True)),
                ('min_coverage_days', models.IntegerField(default=10)),
                ('max_coverage_days', models.IntegerField(default=40)),
                ('optimal_coverage_days', models.IntegerField(default=22)),
            ],
        ),
    ]
