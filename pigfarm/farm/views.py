# farm/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import *
from .forms import *
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from datetime import datetime, timedelta, date
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from decimal import Decimal
from health.models import *
from health.forms import *
import json
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError








# View: Add or Update Room Using Shared Form
def add_room(request, pk=None):
    # 🔍 Debugging: Check if 'pk' is passed
    print(f"Room ID (from URL): {pk}")

    room = None
    if pk:
        # 🔍 Debugging: Confirm room retrieval
        room = get_object_or_404(Room, pk=pk)
        print(f"Editing Room: {room.name}")

    if request.method == 'POST':
        name = request.POST.get('name')
        capacity = request.POST.get('capacity')
        status = request.POST.get('status')
        note = request.POST.get('note')

        # 🔍 Debugging: Check form input values
        print(f"Form Input - Name: {name}, Capacity: {capacity}, Status: {status}")

        if not name or not capacity or not status:
            messages.error(request, "All fields are required.")
            return render(request, 'farm/add_room.html', {'action': 'Add' if not room else 'Update', 'room': room})

        try:
            if room:
                # Update existing room
                room.name = name
                room.capacity = capacity
                room.status = status
                room.note = note
                room.save()
                print(f"✅ Room {room.name} updated successfully.")  # Debug
                messages.success(request, f'Room "{room.name}" updated successfully.')
            else:
                # Create new room
                Room.objects.create(
                    name=name,
                    capacity=capacity,
                    status=status,
                    note=note,
                )
                print(f"✅ New room '{name}' added.")  # Debug
                messages.success(request, f'Room "{name}" added successfully.')
            return redirect('room_list')

        except IntegrityError:
            print(f"⚠️ IntegrityError: Room '{name}' already exists.")  # Debug
            messages.error(request, f'A room with the name "{name}" already exists.')
            return render(request, 'farm/add_room.html', {'action': 'Add' if not room else 'Update', 'room': room})

    return render(request, 'farm/add_room.html', {'action': 'Add' if not room else 'Update', 'room': room})


# View: List Rooms
def room_list(request):
    rooms = Room.objects.all().order_by('name')  # Fetch all rooms sorted by name
    return render(request, 'farm/room_list.html', {'rooms': rooms})


# View: Delete Room
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        messages.success(request, 'Room deleted successfully.')
        return redirect('room_list')
    return render(request, 'farm/room_confirm_delete.html', {'room': room})



#add sow view

CATEGORY_CHOICES = [
    ('young', 'Young Sow'),
    ('prime', 'Prime Sow'),
    ('old', 'Old Sow'),
]

# add and update sow view
def add_sow(request, pk=None):
    """Unified view for adding or updating a sow."""
    sow = None
    rooms = Room.objects.all()
    categories = Sow.CATEGORY_CHOICES

    if pk:
        sow = get_object_or_404(Sow, pk=pk)

    if request.method == 'POST':
        form = SowForm(request.POST, instance=sow)
        if form.is_valid():
            sow = form.save(commit=False)
            selected_room = form.cleaned_data['room']
            initial_cost = form.cleaned_data.get('initial_cost', 0)

            # Assign bought price only when manually adding
            if not pk:
                room_prefix = f"Sow-{selected_room.name}-"
                existing_names = Sow.objects.filter(
                    room=selected_room,
                    name__startswith=room_prefix
                ).values_list('name', flat=True)

                max_order = 0
                for name in existing_names:
                    try:
                        order = int(name.replace(room_prefix, ''))
                        max_order = max(max_order, order)
                    except ValueError:
                        continue

                sow.name = f"{room_prefix}{max_order + 1}"

                # Assign bought price
                sow.initial_cost = initial_cost or 0

            sow.save()
            action = "updated" if pk else "added"
            messages.success(request, f'Sow "{sow.name}" {action} successfully.')
            return redirect('sow_list')
        else:
            messages.error(request, 'Failed to save sow. Please check the form.')
    else:
        form = SowForm(instance=sow)

    return render(request, 'farm/add_sow.html', {
        'form': form,
        'rooms': rooms,
        'categories': categories,
        'action': 'Update' if pk else 'Add',
        'sow': sow,
    })

#sow list view
def sow_list(request):
    """View to list all sows."""
    sows = Sow.objects.filter(status='active')
    return render(request, 'farm/sows.html', {'sows': sows})


def sow_delete(request, pk):
    """View to delete a sow."""
    sow = get_object_or_404(Sow, pk=pk)
    sow.delete()
    messages.success(request, f'Sow "{sow.name}" deleted successfully.')
    return JsonResponse({'success': True})



#piglet 

def piglet_list(request):
    piglets = Piglet.objects.filter(status='active')
    rooms = Room.objects.all()
    return render(request, 'farm/piglets.html', {'piglets': piglets, 'rooms': rooms})


def add_piglet(request, pk=None):
    piglet = None
    if pk:
        piglet = get_object_or_404(Piglet, pk=pk)

    sows = Sow.objects.filter(status='active')

    if request.method == 'POST':
        form = PigletForm(request.POST, instance=piglet)
        if form.is_valid():
            piglet = form.save(commit=False)
            piglet.current_weight = piglet.initial_weight  # Auto-set current weight
            piglet.save()
            messages.success(request, f'Piglet "{piglet.name}" {"updated" if pk else "added"} successfully.')
            return redirect('piglets')
    else:
        form = PigletForm(instance=piglet)

    return render(request, 'farm/add_piglet.html', {
        'form': form,
        'sows': sows,
        'action': 'Update' if pk else 'Add',
        'piglet_name': piglet.name if piglet else 'Auto-generated after submission'
    })



def piglet_delete(request, pk):
    """View to delete a sow."""
    piglet = get_object_or_404(Piglet, pk=pk)
    piglet.delete()
    messages.success(request, f'Piglet "{piglet.name}" deleted successfully.')
    return JsonResponse({'success': True})



def sow_profile(request, sow_id):
    sow = get_object_or_404(Sow, unique_id=sow_id)

    # Records
    weight_records = WeightRecord.objects.filter(target_type='sow', sow=sow).order_by('-recorded_date')
    health_records = HealthRecord.objects.filter(sow=sow).order_by('-treatment_date')  # 🩺 Health records

    # Default empty form for weight
    weight_form = WeightRecordForm()

    if request.method == 'POST':
        # 🐷 BREEDING FORM
        

        # ⚖️ WEIGHT FORM
        if 'heart_girth' in request.POST and 'body_length' in request.POST:
            weight_form = WeightRecordForm(request.POST)
            if weight_form.is_valid():
                record = weight_form.save(commit=False)
                record.target_type = 'sow'
                record.sow = sow
                record.piglet = None
                record.save()
                messages.success(request, "Weight record added.")
                return redirect('sow_profile', sow_id=sow_id)
            else:
                messages.error(request, "Error saving weight record. Please check your inputs.")

        # 🩺 HEALTH FORM (only 4 fields)
        elif 'health_issue' in request.POST and 'treatment_given' in request.POST and 'treatment_date' in request.POST and 'status' in request.POST:
            health_issue = request.POST.get('health_issue')
            treatment_given = request.POST.get('treatment_given')
            treatment_date = request.POST.get('treatment_date')
            status = request.POST.get('status')

            HealthRecord.objects.create(
                sow=sow,
                health_target_type='sow',
                health_issue=health_issue,
                treatment_given=treatment_given,
                treatment_date=treatment_date,
                status=status
            )
            messages.success(request, "Health record added.")
            return redirect('sow_profile', sow_id=sow_id)

    context = {
        'sow': sow,
        'weight_records': weight_records,
        'health_records': health_records,
        'weight_form': weight_form,
        'today_date': date.today().strftime('%Y-%m-%d'),
        'current_weight': sow.current_weight,
    }
    return render(request, 'farm/sow_profile.html', context)


def add_breeding_record(request, sow_id):
    """Allow users to add a breeding record with heat detection and breeding date."""
    sow = get_object_or_404(Sow, unique_id=sow_id)

    if request.method == 'POST':
        heat_detection_date_str = request.POST.get('heat_detection_date')
        breeding_date_str = request.POST.get('breeding_date')

        # Parse dates
        def parse_date(date_str):
            return datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None

        heat_detection_date = parse_date(heat_detection_date_str)
        breeding_date = parse_date(breeding_date_str)

        # Validate that breeding date is within 3 days after heat detection
        if not heat_detection_date or not breeding_date:
            messages.error(request, "Both Heat Detection and Breeding Date are required.")
            return redirect('sow_profile', sow_id=sow_id)

        if (breeding_date - heat_detection_date).days > 3:
            messages.error(request, "Breeding Date must be within 3 days of Heat Detection.")
            return redirect('sow_profile', sow_id=sow_id)

        # Calculate expected farrow date (114 days after breeding)
        expected_farrow_date = breeding_date + timedelta(days=114)

        # Save record
        BreedingRecord.objects.create(
            sow=sow,
            heat_detection_date=heat_detection_date,
            breeding_date=breeding_date,
            expected_farrow_date=expected_farrow_date,
            status='pending'  # Default status
        )

        messages.success(request, "Breeding record added successfully.")
        return redirect('sow_profile', sow_id=sow_id)

    return redirect('sow_profile', sow_id=sow_id)



def update_breeding_status(request, record_id):
    """Allow users to manually update breeding status (Pending, Pregnant, Failed, Done)."""
    record = get_object_or_404(BreedingRecord, id=record_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')

        if new_status in ['pending', 'pregnant', 'failed', 'done']:
            record.status = new_status
            
            # 🆕 If status is "Done," set the actual farrow date to today
            if new_status == 'done' and not record.actual_farrow_date:
                record.actual_farrow_date = now().date()  # Automatically set today's date
            
            record.save()
            messages.success(request, "Breeding status updated successfully.")
        else:
            messages.error(request, "Invalid status selection.")

    return redirect('sow_profile', sow_id=record.sow.unique_id)




def delete_breeding_record(request, record_id):
    """Allow users to delete a breeding record."""
    record = get_object_or_404(BreedingRecord, id=record_id)
    sow_id = record.sow.unique_id  # Get sow ID before deleting

    record.delete()
    messages.success(request, "Breeding record deleted successfully.")
    
    return redirect('sow_profile', sow_id=sow_id)


# 📌 View: List all feed stock
def feed_stock_list(request):
    feeds = FeedStock.objects.all().order_by('-date_added')
    return render(request, 'farm/feed_stock_list.html', {'feeds': feeds})

# 📌 View: Add or Update Feed Stock
def add_feed_stock(request, pk=None):
    """View to add or update feed stock."""
    feed_stock = None
    if pk:
        feed_stock = get_object_or_404(FeedStock, pk=pk)

    if request.method == 'POST':
        form = FeedStockForm(request.POST, instance=feed_stock)
        
        if form.is_valid():
            feed_stock = form.save(commit=False)
            feed_stock.save()
            messages.success(request, f'Feed "{feed_stock.name}" {"updated" if pk else "added"} successfully.')
            return redirect('feed_stock_list')
        else:
            print("❌ Form Errors:", form.errors)  # 🔍 Debugging: Print form errors in the terminal
            messages.error(request, "Failed to save feed stock. Please check the form.")
    else:
        form = FeedStockForm(instance=feed_stock)

    return render(request, 'farm/add_feed_stock.html', {
        'form': form,
        'action': 'Update' if pk else 'Add',
    })






def update_feed_stock(request, pk):
    """Update an existing feed stock record."""
    feed_stock = get_object_or_404(FeedStock, pk=pk)

    if request.method == 'POST':
        form = FeedStockForm(request.POST, instance=feed_stock)
        if form.is_valid():
            form.save()
            messages.success(request, f'Feed "{feed_stock.name}" updated successfully.')
            return redirect('feed_stock_list')
        else:
            messages.error(request, "Failed to update feed stock. Please check the form.")
    else:
        form = FeedStockForm(instance=feed_stock)  # ✅ Pass the instance here!

    return render(request, 'farm/add_feed_stock.html', {
        'form': form,
        'action': 'Update',
        'feed_stock': feed_stock
    })






def delete_feed_stock(request, pk):
    """Delete a feed stock record."""
    feed_stock = get_object_or_404(FeedStock, pk=pk)

    if request.method == 'POST':
        feed_stock.delete()
        messages.success(request, "Feed stock deleted successfully.")
        return redirect('feed_stock_list')

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def add_feeding_record(request):
    """Handles the recording of feed consumption for sows and piglets."""
    sows = Sow.objects.filter(status='active')
    piglets = Piglet.objects.filter(status='active')
    feeds = FeedStock.objects.all()

    if request.method == 'POST':
        form = FeedingRecordForm(request.POST)
        if form.is_valid():
            feeding_record = form.save(commit=False)

            # Ensure only one target is set
            if form.cleaned_data['feeding_target_type'] == 'sow':
                feeding_record.piglet = None  # Only assign sow
            else:
                feeding_record.sow = None  # Only assign piglet

            # Retrieve selected feed stock
            feed_stock = feeding_record.feed

            # Check if enough stock is available
            if Decimal(feeding_record.quantity_used) > feed_stock.stock_quantity:
                messages.error(request, f"Not enough {feed_stock.name} available! (Stock: {feed_stock.stock_quantity} {feed_stock.unit})")
                return redirect('add_feeding_record')

            

            # ✅ Calculate total cost correctly
            feeding_record.total_cost = Decimal(feeding_record.quantity_used) * Decimal(feed_stock.cost_per_unit)
            feeding_record.save()

            messages.success(request, f"Feeding record added successfully! Remaining {feed_stock.name} stock: {feed_stock.stock_quantity} {feed_stock.unit}")
            return redirect('feeding_records')

    else:
        form = FeedingRecordForm()

    return render(request, 'farm/add_feeding_record.html', {
        'form': form,
        'sows': sows,
        'piglets': piglets,
        'feeds': feeds
    })




def feeding_records_list(request):
    """Fetch feeding records and display them in the template"""
    feeding_records = FeedingRecord.objects.all().order_by('-recorded_at')
    
    return render(request, 'farm/feeding_records.html', {
        'feeding_records': feeding_records
    })




def sow_weight_profile(request, sow_id):
    # Fetch the specific sow instance using its unique identifier.
    sow = get_object_or_404(Sow, id=sow_id)

    # Retrieve all associated weight records for the sow, sorted by recorded date.
    weight_records = WeightRecord.objects.filter(sow=sow).order_by('recorded_date')

    # Prepare chart data for visualization, extracting labels and weights.
    chart_data = {
        'labels': [record.recorded_date.strftime('%Y-%m-%d') for record in weight_records],
        'weights': [record.weight for record in weight_records],
    }

    # Pass the sow instance and chart data (as JSON) to the template context.
    context = {
        'sow': sow,
        'chart_data': json.dumps(chart_data),
    }

    # Render the sow's weight profile page.
    return render(request, 'farm/sow_profile.html', context)


def sow_detail(request, sow_id):
    sow = get_object_or_404(Sow, id=sow_id)
    health_records = HealthRecord.objects.filter(sow=sow).order_by('-treatment_date')
    
    return render(request, 'farm/sow_profile.html', {
        'sow': sow,
        'health_records': health_records,
    })


def mark_inactive(request):
    if request.method == 'POST':
        pig_type = request.POST.get('pig_type')
        pig_id = request.POST.get('pig_id')
        reason = request.POST.get('reason')

        if not (pig_type and pig_id and reason):
            messages.error(request, "All fields are required.")
            return redirect('mark_inactive')

        try:
            if pig_type == 'sow':
                pig = get_object_or_404(Sow, unique_id=pig_id)
            elif pig_type == 'piglet':
                pig = get_object_or_404(Piglet, unique_id=pig_id)
            else:
                raise ValueError("Invalid pig type")

            # Create inactive record
            InactivePig.objects.create(
                pig_type=pig_type,
                original_id=pig.unique_id,
                name=pig.name,
                reason=reason
            )

            # Remove from original model
            pig.status = 'inactive'
            pig.save()

            messages.success(request, f"{pig.name} has been marked as inactive.")
            return redirect('inactive_pigs_list')  # ✅ this must match your URL name

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('mark_inactive')

    return render(request, 'farm/mark_inactive.html')


def inactive_pigs_list(request):
    inactive_pigs = InactivePig.objects.all().order_by('-date_marked_inactive')
    return render(request, 'farm/inactive_pigs.html', {'inactive_pigs': inactive_pigs})




def get_active_pigs(request):
    pig_type = request.GET.get('type')
    if pig_type == 'sow':
        pigs = Sow.objects.filter(status='active')
    elif pig_type == 'piglet':
        pigs = Piglet.objects.filter(status='active')
    else:
        return JsonResponse([], safe=False)

    data = [{"id": str(pig.unique_id), "name": pig.name} for pig in pigs]
    return JsonResponse(data, safe=False)


@require_POST
def reactivate_pig(request):
    pig_type = request.POST.get('pig_type')
    pig_id = request.POST.get('pig_id')

    try:
        if pig_type == 'sow':
            from .models import Sow
            pig = Sow.objects.get(unique_id=pig_id)
        elif pig_type == 'piglet':
            from .models import Piglet
            pig = Piglet.objects.get(unique_id=pig_id)
        else:
            messages.error(request, "Invalid pig type.")
            return redirect('inactive_pigs_list')

        # Reactivate the pig
        pig.status = 'active'
        pig.save()

        # Remove from InactivePig log
        InactivePig.objects.filter(original_id=pig_id).delete()

        messages.success(request, f"{pig.name} has been reactivated successfully.")
    except Exception as e:
        messages.error(request, f"Error reactivating pig: {e}")

    return redirect('inactive_pigs_list')


def add_or_edit_insemination(request, insemination_id=None):
    if insemination_id:
        insemination = get_object_or_404(Insemination, id=insemination_id)
        success_message = "Insemination updated successfully."
    else:
        insemination = None
        success_message = "Insemination added successfully."

    if request.method == 'POST':
        form = InseminationForm(request.POST, instance=insemination)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect('insemination_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = InseminationForm(instance=insemination)

    context = {
        'form': form,
        'insemination': insemination
    }
    return render(request, 'farm/insemination_form.html', context)


def list_inseminations(request):
    inseminations = Insemination.objects.all().order_by('-created_at')
    context = {
        'inseminations': inseminations
    }
    return render(request, 'farm/insemination_list.html', context)


def make_sow_from_piglet(request):
    if request.method == 'POST':
        piglet_id = request.POST.get('piglet_id')
        room_id = request.POST.get('room_id')

        piglet = get_object_or_404(Piglet, id=piglet_id)
        room = get_object_or_404(Room, id=room_id)

        # Generate unique sow name
        base_name = f"Sow-{room.name}-"
        existing_names = Sow.objects.filter(
            room=room, name__startswith=base_name
        ).values_list('name', flat=True)

        max_order = 0
        for name in existing_names:
            try:
                order = int(name.replace(base_name, ''))
                max_order = max(max_order, order)
            except ValueError:
                continue

        unique_name = f"{base_name}{max_order + 1}"

        sow = Sow.objects.create(
            name=unique_name,
            room=room,
            registered_date=now().date(),
            promoted_from_piglet=piglet,
            inherited_insemination_type=piglet.insemination_type,
            origin='born_in_farm',
            initial_cost=0,
        )

        # Deactivate the piglet
        piglet.status = 'inactive'
        piglet.save()

        messages.success(request, f"Piglet '{piglet.name}' promoted to Sow '{sow.name}' successfully.")
        return redirect('sow_list')
    

def add_or_update_breeding_record(request, record_id=None):
    if record_id:
        record = get_object_or_404(BreedingRecord, id=record_id)
    else:
        record = None

    if request.method == 'POST':
        form = BreedingRecordForm(request.POST, instance=record)
        if form.is_valid():
            breeding_record = form.save(commit=False)

            # Set expected farrow date if confirmed pregnant
            if breeding_record.status == 'confirmed_pregnant' and breeding_record.insemination_3_date:
                breeding_record.expected_farrow_date = breeding_record.insemination_3_date + timedelta(days=114)

            breeding_record.save()
            messages.success(request, 'Breeding record saved successfully.')
            return redirect('breeding_records_list')
        else:
            messages.error(request, 'This insemination type matches the inherited type from piglet stage. Please use a different one.')
    else:
        form = BreedingRecordForm(instance=record)

    context = {
        'form': form,
        'record': record,
    }
    return render(request, 'farm/add_breeding_record.html', context)



def breeding_records_list(request):
    records = BreedingRecord.objects.select_related('sow', 'insemination_type').order_by('-created_at')
    context = {
        'records': records
    }
    return render(request, 'farm/breeding_records.html', context)


@require_POST
def delete_breeding_record(request, record_id):
    record = get_object_or_404(BreedingRecord, id=record_id)
    record.delete()
    messages.success(request, f"Breeding record for {record.sow.name} deleted successfully.")
    return redirect('breeding_records_list')




def add_or_update_income_record(request, record_id=None):
    record = get_object_or_404(IncomeRecord, id=record_id) if record_id else None

    if request.method == 'POST':
        form = IncomeRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income record saved successfully.')
            return redirect('income_list')
        else:
            messages.error(request, 'There was an error saving the income record.')
    else:
        form = IncomeRecordForm(instance=record)

    context = {
        'form': form,
        'record': record,
    }
    return render(request, 'farm/add_income.html', context)


def income_list(request):
    incomes = IncomeRecord.objects.all().order_by('-date')
    total_income = incomes.aggregate(total=models.Sum('amount'))['total'] or 0

    context = {
        'incomes': incomes,
        'total_income': total_income,
    }
    return render(request, 'farm/income_list.html', context)



@require_POST
def sell_sow(request):
    sow_id = request.POST.get('sow_id')
    sold_price = Decimal(request.POST.get('sold_price'))

    sow = get_object_or_404(Sow, unique_id=sow_id)

    feeding_cost = sow.total_feeding_cost
    health_cost = sow.total_health_cost
    vaccination_cost = sow.total_vaccination_cost
    breeding_cost = sow.total_breeding_cost

    total_cost = feeding_cost + health_cost + vaccination_cost + breeding_cost + sow.initial_cost

    SoldPig.objects.create(
        pig_type='sow',
        sow=sow,
        sold_price=sold_price,
        total_cost=total_cost
    )

    sow.status = 'inactive'
    sow.save()

    messages.success(request, f'Sow "{sow.name}" sold successfully.')
    return redirect('sow_list')



def piglet_profile(request, unique_id):
    piglet = get_object_or_404(Piglet, unique_id=unique_id)

    # Get weight records for chart (if needed)
    weight_records = WeightRecord.objects.filter(piglet=piglet, target_type='piglet').order_by('recorded_date')

    chart_data = {
        "labels": [record.recorded_date.strftime("%Y-%m-%d") for record in weight_records],
        "weights": [float(record.weight) for record in weight_records],
    }

    context = {
        "piglet": piglet,
        "chart_data": chart_data,
        "total_health_cost": piglet.total_health_cost,
        "total_feeding_cost": piglet.total_feeding_cost,
        "total_spent": piglet.total_health_cost + piglet.total_feeding_cost + piglet.total_vaccination_cost,    
    }

    return render(request, "farm/piglet_profile.html", context)


@require_POST
def sell_piglet(request):
    piglet_id = request.POST.get("piglet_id")
    selling_price = Decimal(request.POST.get("selling_price"))

    piglet = get_object_or_404(Piglet, id=piglet_id)
    total_cost = piglet.total_feeding_cost + piglet.total_health_cost + piglet.total_vaccination_cost

    # make sure these exist

    SoldPig.objects.create(
        pig_type='piglet',
        piglet=piglet,
        sold_price=selling_price,
        total_cost=total_cost
    )

    piglet.status = 'inactive'
    piglet.save()

    messages.success(request, f"Piglet '{piglet.name}' sold successfully.")
    return redirect('piglets')  # make sure 'piglets' is a valid URL name