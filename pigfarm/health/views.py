from django.shortcuts import render, redirect, get_object_or_404
from .models import HealthRecord, Vaccination, VaccinationRecord
from farm.models import Sow, Piglet
from django.contrib import messages
from .forms import *
from django.utils.timezone import now
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST



def add_or_edit_health_record(request, record_id=None):
    """Handles both adding and editing health records."""
    health_record = None
    if record_id:
        health_record = get_object_or_404(HealthRecord, id=record_id)

    sows = Sow.objects.filter(status='active')
    piglets = Piglet.objects.filter(status='active')
   

    if request.method == 'POST':
        form = HealthRecordForm(request.POST, instance=health_record)

        # 🔍 DEBUG: Print the raw POST data to see what is being sent
        print("📌 DEBUG - Raw POST Data:", request.POST)

        if form.is_valid():
            health_record = form.save(commit=False)

            # 🔍 DEBUG: Print the selected status
            print("📌 DEBUG - Status Selected:", form.cleaned_data.get('status'))

            # Ensure only one target is assigned
            if form.cleaned_data['health_target_type'] == 'sow':
                health_record.piglet = None  # Only assign sow
            else:
                health_record.sow = None  # Only assign piglet

            health_record.save()
            messages.success(request, "Health record saved successfully!")
            return redirect('health_records')

        else:
            print("❌ DEBUG - Form Errors:", form.errors)  # Print form errors for debugging

    else:
        form = HealthRecordForm(instance=health_record)

    return render(request, 'health/add_health_record.html', {
        'form': form,
        'sows': sows,
        'piglets': piglets,
        'health_record': health_record,
    })

def health_records_list(request):
    """Fetch and display all health records."""
    health_records = HealthRecord.objects.all().order_by('-treatment_date')  # Order by latest treatment
    return render(request, 'health/health_records.html', {'health_records': health_records})

def delete_health_record(request, record_id):
    """Handles the deletion of a health record."""
    health_record = get_object_or_404(HealthRecord, id=record_id)

    if request.method == 'POST':  # Ensures only POST requests delete records
        health_record.delete()
        messages.success(request, "Health record deleted successfully!")

    return redirect('health_records')


@require_POST
def delete_health_record_from_sow(request, record_id):
    health_record = get_object_or_404(HealthRecord, id=record_id)

    if not health_record.sow:
        messages.error(request, "This health record is not linked to a sow.")
        return redirect('health_records')  # fallback

    sow_id = health_record.sow.unique_id
    health_record.delete()
    messages.success(request, "Health record deleted successfully.")
    return redirect('sow_profile', sow_id=sow_id)



def add_or_edit_vaccination(request, pk=None):
    """Handles adding and updating vaccines."""
    vaccination = None
    if pk:
        vaccination = get_object_or_404(Vaccination, pk=pk)

    if request.method == 'POST':
        form = VaccinationForm(request.POST, instance=vaccination)
        if form.is_valid():
            form.save()
            messages.success(request, "Vaccination record saved successfully!")
            return redirect('vaccination_list')  # Redirect to vaccine list page
        else:
            messages.error(request, "Failed to save vaccination record. Please check the form.")
    else:
        form = VaccinationForm(instance=vaccination)

    return render(request, 'health/add_vaccination.html', {
        'form': form,
        'vaccination': vaccination,
    })

def vaccination_list(request):
    """Displays the list of all recorded vaccinations."""
    vaccinations = Vaccination.objects.all().order_by('-id')  # Sort by most recent

    return render(request, 'health/vaccination_list.html', {
        'vaccinations': vaccinations
    })

def delete_vaccination(request, vaccine_id):
    """Handles the deletion of a vaccine."""
    vaccination = get_object_or_404(Vaccination, id=vaccine_id)
    vaccination.delete()
    messages.success(request, f"Vaccine '{vaccination.name}' deleted successfully!")
    return redirect('vaccination_list')

def assign_vaccination(request):
    """Handles assigning vaccination to sows or piglets."""
    sows = Sow.objects.filter(status='active')
    piglets = Piglet.objects.filter(status='active')
    vaccines = Vaccination.objects.all()

    if request.method == 'POST':
        print("📌 DEBUG - Form Submitted!")  # Debugging

        form = VaccinationRecordForm(request.POST)
        print(f"📌 DEBUG - Raw POST Data: {request.POST}")  # Show data received

        if form.is_valid():
            print("✅ DEBUG - Form is valid!")  # Confirm form validation

            vaccination_record = form.save(commit=False)

            # Ensure only one target is assigned
            if form.cleaned_data['vaccination_target_type'] == 'sow':
                vaccination_record.piglet = None  # Only assign sow
                last_vaccination = VaccinationRecord.objects.filter(
                    sow=vaccination_record.sow,
                    vaccine=vaccination_record.vaccine
                ).order_by("-vaccination_date").first()
            else:
                vaccination_record.sow = None  # Only assign piglet
                last_vaccination = VaccinationRecord.objects.filter(
                    piglet=vaccination_record.piglet,
                    vaccine=vaccination_record.vaccine
                ).order_by("-vaccination_date").first()

            # ✅ Update the last vaccination status to "Done"
            if last_vaccination and last_vaccination.status != "done":
                print(f"🔄 Updating previous vaccination (ID: {last_vaccination.id}) to 'Done'")  # Debug
                last_vaccination.status = "done"
                last_vaccination.save(update_fields=['status'])  # ✅ Only update status!

            # ✅ Prevent reassignment if next vaccination date has not yet passed
            if last_vaccination and last_vaccination.next_vaccination_date and last_vaccination.next_vaccination_date > now().date():
                messages.error(
                    request,
                    f"❌ This pig is already vaccinated with {vaccination_record.vaccine.name}. "
                    f"Next vaccination is due on {last_vaccination.next_vaccination_date}."
                )
                return redirect("assign_vaccination")

            # ✅ Calculate Next Vaccination Date
            vaccination_record.next_vaccination_date = (
                vaccination_record.vaccination_date + timedelta(days=vaccination_record.vaccine.duration_days)
            )
            vaccination_record.status = "vaccinated"  # ✅ Set new record to Vaccinated

            vaccination_record.save()
            print(f"✅ DEBUG - New vaccination saved (ID: {vaccination_record.id})")  # Confirm save

            messages.success(request, "✅ Vaccination assigned successfully!")
            return redirect('vaccination_records')

        else:
            print(f"❌ DEBUG - Form Errors: {form.errors}")  # Show form errors
            messages.error(request, "Failed to assign vaccination. Please check the form.")

    else:
        form = VaccinationRecordForm()

    return render(request, 'health/assign_vaccination.html', {
        'form': form,
        'sows': sows,
        'piglets': piglets,
        'vaccines': vaccines
    })

def vaccination_records_list(request):
    """Displays a list of all vaccination records, updating overdue records to 'Done' if necessary."""
    today = now().date()

    # ✅ Find all overdue records
    overdue_vaccinations = VaccinationRecord.objects.filter(
        status="overdue",
        next_vaccination_date__lt=today  # If next vaccination date is in the past
    )

    # ✅ Update overdue records to "done"
    for record in overdue_vaccinations:
        print(f"🔄 Updating overdue vaccination (ID: {record.id}) to 'Done'")  # Debugging
        record.status = "done"
        record.save(update_fields=['status'])  # Only update status field

    # ✅ Fetch all updated vaccination records
    records = VaccinationRecord.objects.all().order_by("-vaccination_date")

    return render(request, "health/vaccination_records.html", {"records": records})

def edit_vaccination(request, record_id):
    """Edit an existing vaccination record."""
    vaccination = get_object_or_404(VaccinationRecord, id=record_id)

    if request.method == 'POST':
        form = VaccinationRecordForm(request.POST, instance=vaccination)
        if form.is_valid():
            form.save()
            messages.success(request, "Vaccination record updated successfully!")
            return redirect('vaccination_records')
    else:
        form = VaccinationRecordForm(instance=vaccination)

    return render(request, 'health/assign_vaccination.html', {'form': form, 'vaccination': vaccination})

def delete_vaccination(request, record_id):
    """Delete a vaccination record."""
    vaccination = get_object_or_404(VaccinationRecord, id=record_id)

    if request.method == 'POST':
        vaccination.delete()
        messages.success(request, "Vaccination record deleted successfully!")
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request'})



def add_or_edit_weight_record(request, record_id=None):
    record = None
    if record_id:
        record = get_object_or_404(WeightRecord, id=record_id)

    if request.method == 'POST':
        form = WeightRecordForm(request.POST, instance=record)
        if form.is_valid():
            weight_record = form.save(commit=False)
            weight_record.save()
            if record:
                messages.success(request, "Weight record updated successfully!")
            else:
                messages.success(request, "Weight record added successfully!")
            return redirect('weight_records_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = WeightRecordForm(instance=record)

    return render(request, 'health/record_weight.html', {
        'form': form,
        'record': record,
        'sows': Sow.objects.filter(status='active'),
        'piglets': Piglet.objects.filter(status='active'),
    })



def weight_records_list(request):
    """Retrieve and display all weight records."""
    # Fetch all weight records from the database, sorted by recorded_date
    weight_records = WeightRecord.objects.all().order_by('-recorded_date')

    # Prepare the context
    context = {
        "weight_records": weight_records
    }

    return render(request, "health/weight_records.html", context)


def delete_weight_record(request, record_id):
    """Delete a weight record."""
    record = get_object_or_404(WeightRecord, id=record_id)

    if request.method == 'POST':
        record.delete()

        # Check if 'next' is in POST to redirect (sow profile, piglet profile)
        next_url = request.POST.get('next')
        if next_url:
            messages.success(request, "Weight record deleted successfully.")
            return redirect(next_url)

        # If no redirect, return JSON (general AJAX usage)
        return JsonResponse({'success': True})

    # Handle invalid request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    messages.error(request, "Invalid request.")
    return redirect('dashboard')  # Or any fallback page
