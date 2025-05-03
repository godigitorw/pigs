# pigfarm/views.py
from django.shortcuts import render, redirect
from farm.models import Sow, Piglet, FeedingRecord, BreedingRecord, SoldPig, FeedStock
from django.utils.timezone import now, timedelta
from collections import OrderedDict
from django.db.models.functions import TruncDate
from django.db.models import Sum
from django.db.models import Max
from health.models import WeightRecord
from collections import defaultdict
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from health.models import WeightRecord, HealthRecord, VaccinationRecord
from decimal import Decimal
from farm.models import IncomeRecord
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import F



@login_required
def dashboard_view(request):
    total_sows = total_sows = Sow.objects.filter(status='active').count()
    total_piglets = Piglet.objects.filter(status='active').count()
    total_pigs = total_sows + total_piglets

    filter_type = request.GET.get('filter', 'week')
    today = now().date()

    if filter_type == 'month':
        start_date = today.replace(day=1)
    else:
        start_date = today - timedelta(days=today.weekday())  # Monday

    # Group feed records by date
    feed_records = (
        FeedingRecord.objects
        .filter(recorded_at__date__gte=start_date, recorded_at__date__lte=today)
        .annotate(date=TruncDate('recorded_at'))
        .values('date')
        .annotate(
            total_cost=Sum('total_cost'),
            total_quantity=Sum('quantity_used')
        )
        .order_by('date')
    )

    labels, cost_data, quantity_data = [], [], []
    for record in feed_records:
        labels.append(record['date'].strftime('%b %d'))  # e.g. "Apr 08"
        cost_data.append(float(record['total_cost']))
        quantity_data.append(float(record['total_quantity']))
        total_feed_cost = sum(cost_data)

    
    category_details = {
        'Blue': {'label': 'Underweight (<12kg)', 'color': '#0564FE'},
        'Yellow': {'label': 'Light (12–25kg)', 'color': '#F7C948'},
        'Purple': {'label': 'Medium (25–60kg)', 'color': '#9F7AEA'},
        'Green': {'label': 'Heavy (>60kg)', 'color': '#38A169'},
    }

    # Get latest weight records grouped by target_type and ID
    latest_records = []

    for target_type in ['sow', 'piglet']:
        latest = (
            WeightRecord.objects
            .filter(target_type=target_type)
            .values(f'{target_type}_id')
            .annotate(latest_date=Max('recorded_date'))
        )

        for entry in latest:
            record = WeightRecord.objects.filter(
                target_type=target_type,
                recorded_date=entry['latest_date'],
                **{f'{target_type}_id': entry[f'{target_type}_id']}
            ).first()
            if record:
                latest_records.append(record)

    # Categorize weights
    categorized = defaultdict(lambda: {'Sow': 0, 'Piglet': 0})

    for record in latest_records:
        category = record.weight_category()
        if category in category_details:
            pig_type = 'Sow' if record.target_type == 'sow' else 'Piglet'
            categorized[category][pig_type] += 1

    # Build final table structure
    pig_category_table = []
    for cat_key, counts in categorized.items():
        detail = category_details.get(cat_key, {})
        pig_category_table.append({
            'color': detail.get('color', '#000'),
            'label': detail.get('label', cat_key),
            'sow_count': counts['Sow'],
            'piglet_count': counts['Piglet'],
        })

    total_feed_cost = Decimal(sum(cost_data))


    total_health_records = HealthRecord.objects.count()
    total_health_cost = HealthRecord.objects.aggregate(total=Sum('cost'))['total'] or 0


    total_vaccination_cost = VaccinationRecord.objects.aggregate(total=Sum('cost'))['total'] or 0

    total_breeding_cost = BreedingRecord.objects.aggregate(total=Sum('cost'))['total'] or 0


    total_farm_cost = ( total_feed_cost + total_health_cost + total_vaccination_cost + total_breeding_cost)
    total_income = IncomeRecord.objects.aggregate(total=Sum('amount'))['total'] or Decimal(0)

    # Total sales from sold pigs
    total_sales = SoldPig.objects.aggregate(total=Sum('sold_price'))['total'] or Decimal(0)

    # Total cost of all sold pigs
    total_spent_on_sold = SoldPig.objects.aggregate(total=Sum('total_cost'))['total'] or Decimal(0)

    total_sow_initial_cost = Sow.objects.aggregate(total=Sum('initial_cost'))['total'] or Decimal(0)
   

    # Profit or loss
    net_profit = total_sales - total_spent_on_sold

    total_farm_cost = (
        Decimal(total_feed_cost) +
        Decimal(total_health_cost) +
        Decimal(total_vaccination_cost) +
        Decimal(total_breeding_cost) +
        Decimal(total_sow_initial_cost)
    )

    net_balance = total_sales - total_farm_cost
    is_farm_profitable = net_balance >= 0

    ongoing_health_records = HealthRecord.objects.filter(status='ongoing')

    today = now().date()
    upcoming_vaccinations = VaccinationRecord.objects.filter(
        next_vaccination_date__lte=today + timedelta(days=30),
        next_vaccination_date__gte=today
    ).order_by('next_vaccination_date')


    low_stock_feeds = FeedStock.objects.filter(
    initial_quantity__gt=0,  # To avoid division by zero
    stock_quantity__lt=F('initial_quantity') * Decimal('0.20')
)

    


    

    context = {
        'total_sows': total_sows,
        'total_piglets': total_piglets,
        'total_pigs': total_pigs,
        'cost_chart_labels': labels,
        'cost_chart_values': cost_data,
        'quantity_chart_values': quantity_data,
        'filter_type': filter_type,
        'total_feed_cost': sum(cost_data),
        'total_feed_consumed': sum(quantity_data),
        'pig_category_table': pig_category_table,
        'total_health_records': total_health_records,
        'total_health_cost': total_health_cost,
        'total_vaccination_cost': total_vaccination_cost,
        'total_breeding_cost': total_breeding_cost,
        'total_farm_cost': total_farm_cost,
        'total_income': total_income,
        'total_sales': total_sales,
        'total_spent_on_sold': total_spent_on_sold,
        'net_profit': net_profit,
        'is_profit': net_profit >= 0,
        'total_farm_cost': total_farm_cost,
        'net_balance': net_balance,
        'is_farm_profitable': is_farm_profitable,
        'total_sow_initial_cost': total_sow_initial_cost,
        'ongoing_health_records': ongoing_health_records,
        'upcoming_vaccinations': upcoming_vaccinations,
        'low_stock_feeds': low_stock_feeds,
    }

    return render(request, 'dashboard.html', context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')  # change this to your dashboard route
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


