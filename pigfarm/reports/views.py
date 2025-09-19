from django.http import HttpResponse
import pandas as pd
from io import BytesIO
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_date
from farm.models import IncomeRecord, SoldPig, ExpenseRecord, FeedingRecord
from django.shortcuts import render
from farm.models import Piglet, Sow
from django.template.loader import render_to_string
from weasyprint import HTML
from health.models import WeightRecord
import datetime
import pdfkit



def finance_report(request):
    range_type = request.GET.get('range', 'week')
    finance_type = request.GET.get('finance_type', 'all')
    today = timezone.now().date()

    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    incomes = []
    expenses = []

    if start_date and end_date:
        if finance_type in ['all', 'income']:
            # IncomeRecord
            incomes_db = IncomeRecord.objects.filter(date__range=(start_date, end_date))
            income_data = [
                {
                    'date': i.date,
                    'category': i.get_source_display(),
                    'amount': i.amount,
                    'note': i.description,
                }
                for i in incomes_db
            ]

            # SoldPig
            sold_pigs = SoldPig.objects.filter(date_sold__range=(start_date, end_date))

            sold_sows_data = [
                {
                    'date': sp.date_sold,
                    'category': 'Sold Sow',
                    'amount': sp.sold_price,
                    'note': f"Sow: {sp.sow.name if sp.sow else 'Unknown'}"
                }
                for sp in sold_pigs
                if sp.pig_type == 'sow'
            ]

            sold_piglets_data = [
                {
                    'date': sp.date_sold,
                    'category': 'Sold Piglet',
                    'amount': sp.sold_price,
                    'note': f"Piglet: {sp.piglet.name if sp.piglet else 'Unknown'}"
                }
                for sp in sold_pigs
                if sp.pig_type == 'piglet'
            ]

            incomes = income_data + sold_sows_data + sold_piglets_data

        if finance_type in ['all', 'expense']:
            expenses_db = ExpenseRecord.objects.filter(date__range=(start_date, end_date))
            expenses = [
                {
                    'date': e.date,
                    'category': e.get_category_display(),
                    'amount': e.amount,
                    'note': e.description,
                }
                for e in expenses_db
            ]

    total_income = sum(item['amount'] for item in incomes)
    total_expense = sum(item['amount'] for item in expenses)
    net_balance = total_income - total_expense

    context = {
        'incomes': incomes,
        'expenses': expenses,
        'net_balance': net_balance,
        'range': range_type,
        'finance_type': finance_type,
        'start_date': start_date,
        'end_date': end_date,
        'total_income': total_income,
        'total_expense': total_expense,
    }

    return render(request, 'reports/finance_report.html', context)

def finance_report_export(request):
    range_type = request.GET.get('range', 'week')
    today = timezone.now().date()

    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    # Add fallback in case parsing failed
    if start_date is None or end_date is None:
        start_date = today - timedelta(days=30)
        end_date = today

    print("Start Date:", start_date)
    print("End Date:", end_date)

    # Fetch Incomes
    incomes = IncomeRecord.objects.filter(date__range=(start_date, end_date))
    income_data = []
    for i in incomes:
        income_data.append({
            'date': i.date,
            'category': i.get_source_display(),
            'amount': float(i.amount),
            'note': i.description,
        })

    # Fetch Sold Pigs
    sold_pigs = SoldPig.objects.filter(date_sold__range=(start_date, end_date))

    sold_sows_data = []
    for sp in sold_pigs.filter(pig_type='sow'):
        sold_sows_data.append({
            'date': sp.date_sold,
            'category': 'Sold Sow',
            'amount': float(sp.sold_price),
            'note': f"Sow: {sp.sow.name if sp.sow else 'Unknown'}"
        })

    sold_piglets_data = []
    for sp in sold_pigs.filter(pig_type='piglet'):
        sold_piglets_data.append({
            'date': sp.date_sold,
            'category': 'Sold Piglet',
            'amount': float(sp.sold_price),
            'note': f"Piglet: {sp.piglet.name if sp.piglet else 'Unknown'}"
        })

    all_income_data = income_data + sold_sows_data + sold_piglets_data

    # Fetch Expenses
    expenses = ExpenseRecord.objects.filter(date__range=(start_date, end_date))
    expense_data = []
    for e in expenses:
        expense_data.append({
            'date': e.date,
            'category': e.get_category_display(),
            'amount': float(e.amount),
            'note': e.description,
        })

    # Ensure DataFrames have headers even if empty
    income_df = pd.DataFrame(all_income_data)
    if income_df.empty:
        income_df = pd.DataFrame(columns=['date', 'category', 'amount', 'note'])

    expense_df = pd.DataFrame(expense_data)
    if expense_df.empty:
        expense_df = pd.DataFrame(columns=['date', 'category', 'amount', 'note'])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        income_df.to_excel(writer, sheet_name='Incomes', index=False)
        expense_df.to_excel(writer, sheet_name='Expenses', index=False)

    output.seek(0)
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="finance_report.xlsx"'
    return response


def finance_report_pdf(request):
    range_type = request.GET.get('range', 'week')
    finance_type = request.GET.get('finance_type', 'all')
    today = datetime.date.today()

    if range_type == 'week':
        start_date = today - datetime.timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            start_date = None
            end_date = None
    else:
        start_date = None
        end_date = None

    incomes = []
    expenses = []

    if start_date and end_date:
        if finance_type in ['all', 'income']:
            incomes_db = IncomeRecord.objects.filter(date__range=(start_date, end_date))
            income_data = [
                {
                    'date': i.date,
                    'category': i.get_source_display(),
                    'amount': i.amount,
                    'note': i.description,
                }
                for i in incomes_db
            ]

            sold_pigs = SoldPig.objects.filter(date_sold__range=(start_date, end_date))

            sold_sows_data = [
                {
                    'date': sp.date_sold,
                    'category': 'Sold Sow',
                    'amount': sp.sold_price,
                    'note': f"Sow: {sp.sow.name if sp.sow else 'Unknown'}"
                }
                for sp in sold_pigs
                if sp.pig_type == 'sow'
            ]

            sold_piglets_data = [
                {
                    'date': sp.date_sold,
                    'category': 'Sold Piglet',
                    'amount': sp.sold_price,
                    'note': f"Piglet: {sp.piglet.name if sp.piglet else 'Unknown'}"
                }
                for sp in sold_pigs
                if sp.pig_type == 'piglet'
            ]

            incomes = income_data + sold_sows_data + sold_piglets_data

        if finance_type in ['all', 'expense']:
            expenses_db = ExpenseRecord.objects.filter(date__range=(start_date, end_date))
            expenses = [
                {
                    'date': e.date,
                    'category': e.get_category_display(),
                    'amount': e.amount,
                    'note': e.description,
                }
                for e in expenses_db
            ]

    total_income = sum(item['amount'] for item in incomes)
    total_expense = sum(item['amount'] for item in expenses)
    net_balance = total_income - total_expense

    context = {
        'incomes': incomes,
        'expenses': expenses,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'finance_type': finance_type,
        'start_date': start_date,
        'end_date': end_date,
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        'user': request.user if request.user.is_authenticated else None,
    }

    html_string = render_to_string("reports/finance_report_pdf.html", context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="finance_report.pdf"'
    return response


    

def piglet_births_report(request):
    range_type = request.GET.get('range', 'week')
    today = timezone.now().date()

    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    piglets = []
    if start_date and end_date:
        piglets = Piglet.objects.filter(
            birth_date__range=(start_date, end_date),
            status='active'
        ).select_related('sow')

    report_data = []
    for piglet in piglets:
        report_data.append({
            'piglet_name': piglet.name,
            'sow_name': piglet.sow.name if piglet.sow else 'Unknown',
            'birth_date': piglet.birth_date,
        })

    context = {
        'range': range_type,
        'start_date': start_date,
        'end_date': end_date,
        'report_data': report_data,
        'total_piglets': len(report_data),
    }
    return render(request, 'reports/piglet_births_report.html', context)

def piglet_births_report_pdf(request):
    user = request.user if request.user.is_authenticated else None
    generated_at = timezone.now()

    range_type = request.GET.get('range', 'week')
    today = timezone.now().date()

    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    piglets = []
    if start_date and end_date:
        piglets = Piglet.objects.filter(
            birth_date__range=(start_date, end_date),
            status='active'
        ).select_related('sow')

    report_data = []
    for piglet in piglets:
        report_data.append({
            'piglet_name': piglet.name,
            'sow_name': piglet.sow.name if piglet.sow else 'Unknown',
            'birth_date': piglet.birth_date,
        })

    html_string = render_to_string(
        'reports/piglet_births_report_pdf.html',
        {
            'system_name': "Pig Farm Management System",
            'generated_at': generated_at,
            'user': user,
            'report_data': report_data,
            'total_piglets': len(report_data),
            'start_date': start_date,
            'end_date': end_date,
            'range': range_type,
        }
    )

    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="piglet_births_report.pdf"'
    return response


def sow_report(request):
    range_type = request.GET.get('range', 'week')
    today = timezone.now().date()

    # Determine date range
    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    sows = []
    if start_date and end_date:
        sows = Sow.objects.filter(
            registered_date__range=(start_date, end_date),
            status='active'
        ).select_related('room')

    report_data = []
    for sow in sows:
        report_data.append({
            'name': sow.name,
            'animal_tag_id': sow.animal_tag_id,
            'registered_date': sow.registered_date,
            'room': sow.room.name if sow.room else 'N/A',
            'birth_count': sow.birth_count,
            'piglet_count': sow.piglets.count(),
            'origin': sow.get_origin_display(),
        })

    context = {
        'range': range_type,
        'start_date': start_date,
        'end_date': end_date,
        'report_data': report_data,
        'total_sows': len(report_data),
    }
    return render(request, 'reports/sow_report.html', context)


def sow_report_pdf(request):
    user = request.user if request.user.is_authenticated else None
    generated_at = timezone.now()

    range_type = request.GET.get('range', 'week')
    today = timezone.now().date()

    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    sows = []
    if start_date and end_date:
        sows = Sow.objects.filter(
            registered_date__range=(start_date, end_date),
            status='active'
        ).select_related('room')

    report_data = []
    for sow in sows:
        report_data.append({
            'name': sow.name,
            'animal_tag_id': sow.animal_tag_id,
            'registered_date': sow.registered_date,
            'room': sow.room.name if sow.room else 'N/A',
            'birth_count': sow.birth_count,
            'piglet_count': sow.piglets.count(),
            'origin': sow.get_origin_display(),
        })

    html_string = render_to_string(
        'reports/sow_report_pdf.html',
        {
            'system_name': "Pig Farm Management System",
            'generated_at': generated_at,
            'user': user,
            'report_data': report_data,
            'total_sows': len(report_data),
            'start_date': start_date,
            'end_date': end_date,
            'range': range_type,
        }
    )

    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sow_report.pdf"'
    return response


def weight_report(request):
    range_type = request.GET.get('range', 'week')
    pig_type = request.GET.get('pig_type', 'all')
    today = timezone.now().date()

    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    records = []
    if start_date and end_date:
        query = WeightRecord.objects.filter(
            recorded_date__range=(start_date, end_date)
        ).select_related('sow', 'piglet')

        if pig_type in ['sow', 'piglet']:
            query = query.filter(target_type=pig_type)

        for record in query:
            if record.target_type == 'sow' and record.sow:
                name = record.sow.name
                tag = record.sow.animal_tag_id
            elif record.target_type == 'piglet' and record.piglet:
                name = record.piglet.name
                tag = record.piglet.animal_tag_id
            else:
                name = "-"
                tag = "-"

            # Example weight status logic
            if record.weight < 50:
                status = "Underweight"
            elif 50 <= record.weight < 250:
                status = "Ideal"
            else:
                status = "Overweight"

            records.append({
                'pig_type': record.get_target_type_display(),
                'name': name,
                'tag': tag,
                'date': record.recorded_date,
                'weight': record.weight,
                'status': status,
            })

    context = {
        'range': range_type,
        'pig_type': pig_type,
        'start_date': start_date,
        'end_date': end_date,
        'records': records,
        'total_records': len(records),
    }

    return render(request, 'reports/weight_report.html', context)


def weight_report_pdf(request):
    user = request.user if request.user.is_authenticated else None
    generated_at = timezone.now()

    range_type = request.GET.get('range', 'week')
    pig_type = request.GET.get('pig_type', 'all')
    today = timezone.now().date()

    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    records = []
    if start_date and end_date:
        query = WeightRecord.objects.filter(
            recorded_date__range=(start_date, end_date)
        ).select_related('sow', 'piglet')

        if pig_type in ['sow', 'piglet']:
            query = query.filter(target_type=pig_type)

        for record in query:
            if record.target_type == 'sow' and record.sow:
                name = record.sow.name
                tag = record.sow.animal_tag_id
            elif record.target_type == 'piglet' and record.piglet:
                name = record.piglet.name
                tag = record.piglet.animal_tag_id
            else:
                name = "-"
                tag = "-"

            if record.weight < 50:
                status = "Underweight"
            elif 50 <= record.weight < 250:
                status = "Ideal"
            else:
                status = "Overweight"

            records.append({
                'pig_type': record.get_target_type_display(),
                'name': name,
                'tag': tag,
                'date': record.recorded_date,
                'weight': record.weight,
                'status': status,
            })

    html_string = render_to_string(
        'reports/weight_report_pdf.html',
        {
            'system_name': "Pig Farm Management System",
            'generated_at': generated_at,
            'user': user,
            'records': records,
            'total_records': len(records),
            'start_date': start_date,
            'end_date': end_date,
            'range': range_type,
            'pig_type': pig_type,
        }
    )

    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="weight_report.pdf"'
    return response

def feeding_cost_report(request):
    range_type = request.GET.get('range', 'week')
    pig_type = request.GET.get('pig_type', 'all')
    today = timezone.now().date()

    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    records = []
    if start_date and end_date:
        query = FeedingRecord.objects.filter(
            recorded_at__date__range=(start_date, end_date)
        ).select_related('sow', 'piglet', 'feed')

        if pig_type == 'sow':
            query = query.filter(feeding_target_type='sow')
        elif pig_type == 'piglet':
            query = query.filter(feeding_target_type='piglet')

        for record in query:
            if record.sow:
                pig_type_val = 'Sow'
                name = record.sow.name
                tag = record.sow.animal_tag_id
            elif record.piglet:
                pig_type_val = 'Piglet'
                name = record.piglet.name
                tag = record.piglet.animal_tag_id
            else:
                pig_type_val = '-'
                name = '-'
                tag = '-'

            records.append({
                'pig_type': pig_type_val,
                'name': name,
                'tag': tag,
                'date': record.recorded_at.date(),
                'feed_name': record.feed.name if record.feed else '-',
                'quantity': record.quantity_used,
                'total_cost': record.total_cost,
            })

    total_cost = sum(r['total_cost'] for r in records)

    context = {
        'range': range_type,
        'pig_type': pig_type,
        'start_date': start_date,
        'end_date': end_date,
        'records': records,
        'total_cost': total_cost,
        'total_records': len(records),
    }

    return render(request, 'reports/feeding_cost_report.html', context)


def feeding_cost_report_pdf(request):
    user = request.user if request.user.is_authenticated else None
    generated_at = timezone.now()

    range_type = request.GET.get('range', 'week')
    pig_type = request.GET.get('pig_type', 'all')
    today = timezone.now().date()

    if range_type == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif range_type == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif range_type == 'custom':
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
    else:
        start_date = None
        end_date = None

    records = []
    if start_date and end_date:
        query = FeedingRecord.objects.filter(
            date__range=(start_date, end_date)
        ).select_related('sow', 'piglet')

        if pig_type == 'sow':
            query = query.filter(sow__isnull=False)
        elif pig_type == 'piglet':
            query = query.filter(piglet__isnull=False)

        for record in query:
            if record.sow:
                pig_type_val = 'Sow'
                name = record.sow.name
                tag = record.sow.animal_tag_id
            elif record.piglet:
                pig_type_val = 'Piglet'
                name = record.piglet.name
                tag = record.piglet.animal_tag_id
            else:
                pig_type_val = '-'
                name = '-'
                tag = '-'

            records.append({
                'pig_type': pig_type_val,
                'name': name,
                'tag': tag,
                'date': record.date,
                'feed_name': record.feed_name,
                'quantity': record.quantity,
                'total_cost': record.total_cost,
            })

    total_cost = sum(r['total_cost'] for r in records)

    html_string = render_to_string(
        'reports/feeding_cost_report_pdf.html',
        {
            'system_name': "Pig Farm Management System",
            'generated_at': generated_at,
            'user': user,
            'records': records,
            'total_records': len(records),
            'total_cost': total_cost,
            'start_date': start_date,
            'end_date': end_date,
            'range': range_type,
            'pig_type': pig_type,
        }
    )

    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="feeding_cost_report.pdf"'
    return response