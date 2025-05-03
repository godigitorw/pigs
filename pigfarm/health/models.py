from django.db import models
from farm.models import Sow, Piglet  
import uuid
from django.utils.timezone import now
from decimal import Decimal
from django.core.exceptions import ValidationError
from datetime import timedelta


class HealthRecord(models.Model):
    """Model to track health records of pigs (Sows & Piglets)"""

    HEALTH_TARGET_CHOICES = [
        ('sow', 'Sow'),
        ('piglet', 'Piglet'),
    ]

    STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('recovered', 'Recovered'),
        ('critical', 'Critical'),  # ✅ Ensure this is exactly spelled correctly
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    health_target_type = models.CharField(max_length=10, choices=HEALTH_TARGET_CHOICES)
    sow = models.ForeignKey(Sow, on_delete=models.CASCADE, null=True, blank=True, related_name="health_records")
    piglet = models.ForeignKey(Piglet, on_delete=models.CASCADE, null=True, blank=True, related_name="health_records")
    health_issue = models.CharField(max_length=255, help_text="Specify disease or health issue")
    treatment_given = models.TextField(help_text="Describe treatment, medication, or deworming given")
    dosage = models.CharField(max_length=50, blank=True, help_text="Dosage amount (e.g., 5ml)")
    treatment_date = models.DateField(default=now)
    next_treatment_date = models.DateField(null=True, blank=True, help_text="Optional next treatment date")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='under_treatment')
    cost = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'),help_text="Cost of this health treatment") 
    note = models.TextField(blank=True, null=True, help_text="Optional notes or observations about the health treatment")

    def __str__(self):
        return f"{self.health_target_type.capitalize()} - {self.health_issue} ({self.treatment_date})"
    


class Vaccination(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    duration_days = models.PositiveIntegerField(help_text="Number of days before the next vaccination is due")
    date_added = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"
    

class VaccinationRecord(models.Model):
    STATUS_CHOICES = [
        ('vaccinated', 'Vaccinated'),
        ('overdue', 'Overdue'),
        ('done', 'Done'),
    ]

    TARGET_CHOICES = [
        ('sow', 'Sow'),
        ('piglet', 'Piglet'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vaccination_target_type = models.CharField(max_length=10, choices=TARGET_CHOICES, default='sow')  
    sow = models.ForeignKey('farm.Sow', on_delete=models.CASCADE, null=True, blank=True)
    piglet = models.ForeignKey('farm.Piglet', on_delete=models.CASCADE, null=True, blank=True)
    vaccine = models.ForeignKey('health.Vaccination', on_delete=models.CASCADE)
    vaccination_date = models.DateField()
    next_vaccination_date = models.DateField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='vaccinated')

    def save(self, *args, **kwargs):
        """Ensure next vaccination date is set and update status accordingly."""
        if self.vaccine.duration_days:
            self.next_vaccination_date = self.vaccination_date + timedelta(days=self.vaccine.duration_days)

        # ✅ Auto-update status
        today = now().date()
        if self.next_vaccination_date and self.next_vaccination_date < today:
            self.status = "overdue"  # If today is past next date, it's overdue

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vaccine.name} - {self.vaccination_target_type}"
    



    

class WeightRecord(models.Model):
    TARGET_CHOICES = [
        ('sow', 'Sow'),
        ('piglet', 'Piglet'),
    ]

    STATUS_CHOICES = [
        ('increased', 'Increased'),
        ('decreased', 'Decreased'),
        ('no_change', 'No Change'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES, default='sow')
    sow = models.ForeignKey('farm.Sow', on_delete=models.CASCADE, null=True, blank=True)
    piglet = models.ForeignKey('farm.Piglet', on_delete=models.CASCADE, null=True, blank=True)
    recorded_date = models.DateField(default=now)
    weight = models.DecimalField(max_digits=6, decimal_places=2, help_text="Measured weight in kilograms")
    difference = models.DecimalField(max_digits=6, decimal_places=2, editable=False, default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='no_change')

    def weight_category(self):
        """Automatically determine the weight category.""" 
        if self.weight < 12:
            return 'Blue'
        elif self.weight <= 25:
            return 'Yellow'
        elif self.weight <= 60:
            return 'Purple'
        else:
            return 'Green'

    def save(self, *args, **kwargs):
        # Fetch last weight record
        if self.target_type == 'sow':
            last_record = WeightRecord.objects.filter(sow=self.sow).exclude(id=self.id).order_by('-recorded_date').first()
        else:
            last_record = WeightRecord.objects.filter(piglet=self.piglet).exclude(id=self.id).order_by('-recorded_date').first()

        # Calculate difference and status
        if last_record:
            self.difference = self.weight - last_record.weight
            self.status = (
                'increased' if self.difference > 0 else
                'decreased' if self.difference < 0 else
                'no_change'
            )
        else:
            self.difference = 0
            self.status = 'no_change'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.target_type.capitalize()} - {self.recorded_date} - {self.weight} kg"
