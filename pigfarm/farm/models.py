# farm/models.py
from django.db import models
import uuid
from django.utils.timezone import now
from decimal import Decimal
from django.apps import apps
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import redirect



class Insemination(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Name of the insemination method or material")
    description = models.TextField(blank=True, help_text="Optional details about the insemination")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Room(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('full', 'Full'),
        ('maintenance', 'Maintenance'),
    ]

    name = models.CharField(max_length=10, unique=True)
    capacity = models.PositiveIntegerField()
    pig_count = models.PositiveIntegerField(default=0, editable=False)  # Auto-updated from sows
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    note = models.TextField(blank=True, null=True)

    def update_pig_count(self):
        """Update pig_count and status based on sows only."""
        from farm.models import Sow  # Avoid circular import

        sow_count = Sow.objects.filter(room=self).count()
        self.pig_count = sow_count

        if sow_count >= self.capacity:
            self.status = 'full'
        elif sow_count == 0:
            self.status = 'available'
        elif self.status != 'maintenance':
            self.status = 'available'

        self.save()

    def is_full(self):
        return self.pig_count >= self.capacity

    def __str__(self):
        return f"{self.name} - {self.status.capitalize()} (Capacity: {self.capacity}, Current: {self.pig_count})"
    



class Sow(models.Model):
    CATEGORY_CHOICES = [
        ('young', 'Young Sow'),
        ('prime', 'Prime Sow'),
        ('old', 'Old Sow'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    ORIGIN_CHOICES = [
        ('sowed', 'Sowed'),
        ('birthed', 'Birthed'),
        ('born_in_farm', 'Born in Farm'),
    ]

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, unique=True)
    registered_date = models.DateField(default=now)
    birth_count = models.PositiveIntegerField(default=0)
    total_piglets = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    promoted_from_piglet = models.ForeignKey(
        'farm.Piglet',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='promoted_sow'
    )

    inherited_insemination_type = models.ForeignKey(
        'farm.Insemination',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Insemination type inherited from the piglet if promoted"
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='young'
    )

    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='sows')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    animal_tag_id = models.CharField(
    max_length=50,
    unique=True,
    null=True,
    blank=True,
    help_text="E.g., RW-PIG-001"
    )

    origin = models.CharField(
        max_length=20,
        choices=ORIGIN_CHOICES,
        default='sowed',
        help_text="Where this sow came from (Sowed, Birthed, or Born in Farm)"
    )

    initial_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Cost of buying the sow (if not born in the farm)"
    )

    def __str__(self):
        return f"{self.name} ({self.unique_id})"

    def update_piglet_count(self):
        self.total_piglets = self.piglets.count()
        self.save()

    def update_birth_count(self):
        unique_birth_dates = self.piglets.values_list("birth_date", flat=True).distinct()
        self.birth_count = len(unique_birth_dates) if unique_birth_dates else 0
        self.save()

    def update_category(self, weight):
        if weight < 150:
            self.category = 'young'
        elif 150 <= weight < 250:
            self.category = 'prime'
        else:
            self.category = 'old'
        self.save()

    @property
    def piglet_sow_count(self):
        return self.piglets.count()

    @property
    def current_weight(self):
        WeightRecord = apps.get_model('health', 'WeightRecord')
        latest_record = WeightRecord.objects.filter(sow=self, target_type='sow').order_by('-recorded_date').first()
        return latest_record.weight if latest_record else None

    @property
    def last_weighing_date(self):
        WeightRecord = apps.get_model('health', 'WeightRecord')
        latest_record = WeightRecord.objects.filter(sow=self, target_type='sow').order_by('-recorded_date').first()
        return latest_record.recorded_date if latest_record else None

    @property
    def weight_status(self):
        WeightRecord = apps.get_model('health', 'WeightRecord')
        latest_record = WeightRecord.objects.filter(sow=self, target_type='sow').order_by('-recorded_date').first()
        return latest_record.status if latest_record else None

    @property
    def total_feeding_cost(self):
        return self.feeding_records.aggregate(total=Sum('total_cost'))['total'] or Decimal(0)

    @property
    def total_vaccination_cost(self):
        VaccinationRecord = apps.get_model('health', 'VaccinationRecord')
        result = VaccinationRecord.objects.filter(
            sow=self,
            vaccination_target_type='sow'
        ).aggregate(total=Sum('cost'))
        return result['total'] or 0

    @property
    def total_health_cost(self):
        HealthRecord = apps.get_model('health', 'HealthRecord')
        result = HealthRecord.objects.filter(
            sow=self, health_target_type='sow'
        ).aggregate(total=Sum('cost'))
        return result['total'] or 0

    @property
    def total_breeding_cost(self):
        BreedingRecord = apps.get_model('farm', 'BreedingRecord')
        result = BreedingRecord.objects.filter(sow=self).aggregate(total=Sum('cost'))
        return result['total'] or 0

    @property
    def total_spent(self):
        return (
            self.initial_cost +
            self.total_feeding_cost +
            self.total_health_cost +
            self.total_vaccination_cost +
            self.total_breeding_cost
        )


# add piglet

class Piglet(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=150, unique=True)
    sow = models.ForeignKey('Sow', on_delete=models.CASCADE, related_name='piglets')
    birth_date = models.DateField(default=now)
    initial_weight = models.FloatField()
    current_weight = models.FloatField(default=0.0, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    animal_tag_id = models.CharField(
    max_length=50,
    unique=True,
    null=True,
    blank=True,
    help_text="E.g., RW-PIG-001"
)

    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
        ],
        null=True,
        blank=True,
        help_text="Gender of the piglet"
    )

    # 🔽 Add this line
    insemination_type = models.ForeignKey(
        Insemination,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Insemination type used for this piglet"
    )

    def save(self, *args, **kwargs):
        if not self.name:
            if self.sow:
                birth_order = Piglet.objects.filter(sow=self.sow).count() + 1
                birth_month = self.birth_date.strftime('%m')
                birth_year = self.birth_date.strftime('%y')
                self.name = f"P{self.sow.room.name}{birth_order}.{birth_month}.{birth_year}"

        super().save(*args, **kwargs)
        if self.sow:
            self.sow.update_birth_count()

    def delete(self, *args, **kwargs):
        print(f"Deleting Piglet {self.name} and updating sow count...")
        super().delete(*args, **kwargs)
        self.sow.update_piglet_count()

    def __str__(self):
        return self.name

    @property
    def total_health_cost(self):
        HealthRecord = apps.get_model('health', 'HealthRecord')
        result = HealthRecord.objects.filter(piglet=self, health_target_type='piglet').aggregate(total=Sum('cost'))
        return result['total'] or 0

    @property
    def total_feeding_cost(self):
        return self.feeding_records.aggregate(total=Sum('total_cost'))['total'] or 0

    @property
    def total_vaccination_cost(self):
        VaccinationRecord = apps.get_model('health', 'VaccinationRecord')
        result = VaccinationRecord.objects.filter(
            piglet=self,
            vaccination_target_type='piglet'
        ).aggregate(total=Sum('cost'))
        return result['total'] or 0

    @property
    def total_spent(self):
        return (
            self.total_feeding_cost +
            self.total_health_cost +
            self.total_vaccination_cost
        )
 






class FeedStock(models.Model):
    name = models.CharField(max_length=255, unique=True)
    feed_type = models.CharField(max_length=50, choices=[
        ('grain', 'Grain-Based'),
        ('pellet', 'Pellet Feed'),
        ('mash', 'Mash Feed'),
        ('supplement', 'Supplement'),
    ])
    initial_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))  # current/remaining stock
    unit = models.CharField(max_length=20, choices=[
        ('kg', 'Kilograms'),
        ('lb', 'Pounds'),
    ])
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=Decimal('0.00'))
    date_added = models.DateTimeField(default=now)

    def save(self, *args, **kwargs):
        # Calculate total cost
        self.total_cost = Decimal(self.stock_quantity) * Decimal(self.cost_per_unit)

        # Set initial quantity if it's a new record
        if not self.pk:
            self.initial_quantity = self.stock_quantity

        if self.stock_quantity < 0:
            raise ValueError("Stock quantity cannot be negative.")
        
        super().save(*args, **kwargs)

    def stock_status(self):
        """Returns 'Insufficient' if remaining is < 20% of initial, else 'Sufficient'"""
        if self.initial_quantity == 0:
            return "Insufficient"
        percentage_remaining = (self.stock_quantity / self.initial_quantity) * 100
        return "Sufficient" if percentage_remaining >= 20 else "Insufficient"

    def __str__(self):
        return f"{self.name} - {self.stock_quantity} {self.unit}"
    
    @property
    def stock_status(self):
        if self.initial_quantity == 0:
            return "No Initial Data"
        
        percent = (self.stock_quantity / self.initial_quantity) * 100

        if percent < 20:
            return "Low"
        elif percent < 50:
            return "Moderate"
        else:
            return "Good"

    @property
    def stock_status_class(self):
        # Used for badge colors in template
        status = self.stock_status
        if status == "Low":
            return "danger"
        elif status == "Moderate":
            return "warning"
        elif status == "Good":
            return "success"
        else:
            return "secondary"
    

class FeedingRecord(models.Model):
    """Model to record feeding activities"""
    
    FEEDING_TARGET_CHOICES = [
        ('sow', 'Sow'),
        ('piglet', 'Piglet'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    feeding_target_type = models.CharField(max_length=10, choices=FEEDING_TARGET_CHOICES)  # Sow or Piglet
    sow = models.ForeignKey(Sow, on_delete=models.CASCADE, null=True, blank=True, related_name="feeding_records")
    piglet = models.ForeignKey(Piglet, on_delete=models.CASCADE, null=True, blank=True, related_name="feeding_records")
    feed = models.ForeignKey(FeedStock, on_delete=models.CASCADE, related_name="feeding_records")  # Feed type used
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)  # Amount of feed consumed
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, editable=False)  # Auto-calculated cost
    recorded_at = models.DateTimeField(default=now)  # Timestamp when feeding is recorded

    def save(self, *args, **kwargs):
        """Ensure feed stock updates and calculate cost"""
        # Check if this is an update (record already exists in database)
        is_update = self.pk is not None and FeedingRecord.objects.filter(pk=self.pk).exists()

        if is_update:
            # Get the old record to restore stock before recalculating
            old_record = FeedingRecord.objects.get(pk=self.pk)
            # Restore the previously deducted quantity to feed stock
            self.feed.stock_quantity += old_record.quantity_used
            self.feed.save()

        # Check if enough stock is available for the new/updated quantity
        if self.quantity_used > self.feed.stock_quantity:
            raise ValueError("Not enough feed stock available!")

        # Deduct the new quantity from feed stock
        self.feed.stock_quantity -= self.quantity_used
        self.feed.total_cost = self.feed.stock_quantity * Decimal(self.feed.cost_per_unit)
        self.feed.save()

        # Calculate cost
        self.total_cost = self.quantity_used * self.feed.cost_per_unit

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Restore feed stock when deleting a feeding record"""
        # Restore the quantity back to feed stock
        self.feed.stock_quantity += self.quantity_used
        self.feed.total_cost = self.feed.stock_quantity * Decimal(self.feed.cost_per_unit)
        self.feed.save()

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Feeding {self.feeding_target_type} - {self.feed.name} - {self.quantity_used}kg"



class InactivePig(models.Model):
    PIG_TYPE_CHOICES = [
        ('sow', 'Sow'),
        ('piglet', 'Piglet'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pig_type = models.CharField(max_length=10, choices=PIG_TYPE_CHOICES)
    original_id = models.UUIDField()  # ID from original Sow or Piglet
    name = models.CharField(max_length=100)
    reason = models.TextField()
    date_marked_inactive = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.pig_type}) - Inactive"
    


class BreedingRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed_pregnant', 'Confirmed Pregnant'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sow = models.ForeignKey(Sow, on_delete=models.CASCADE, related_name='breeding_records')
    
    heat_detection_date = models.DateField(null=True, blank=True)
    insemination_1_date = models.DateField(null=True, blank=True)
    insemination_2_date = models.DateField(null=True, blank=True)
    insemination_3_date = models.DateField(null=True, blank=True)
    
    insemination_type = models.ForeignKey('Insemination', on_delete=models.PROTECT, null=True, blank=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    expected_narrow_date = models.DateField(null=True, blank=True)
    expected_farrow_date = models.DateField(null=True, blank=True)
    actual_farrow_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=now)

    def save(self, *args, **kwargs):
        # Auto-set expected farrow date if status is confirmed and not already set
        if self.status == 'confirmed_pregnant' and self.insemination_3_date:
            self.expected_farrow_date = self.insemination_3_date + timedelta(days=114)  # 3 months, 3 weeks, 3 days
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Breeding for {self.sow.name} - {self.status}"
    

class IncomeRecord(models.Model):
    SOURCE_CHOICES = [
        ('manure', 'Manure Sale'),
        ('service', 'Service Rendered'),
        ('other', 'Other'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(default=timezone.now)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_source_display()} - {self.amount} RWF"
    


# models.py
class ExpenseRecord(models.Model):
    CATEGORY_CHOICES = [
        ('feed', 'Feed Purchase'),
        ('medicine', 'Veterinary Medicine'),
        ('maintenance', 'Maintenance'),
        ('salary', 'Staff Salary'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount} RWF"



class BankAccount(models.Model):
    """Model to track bank accounts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_name = models.CharField(max_length=200, help_text="Name of the bank account")
    bank_name = models.CharField(max_length=200, help_text="Name of the bank")
    account_number = models.CharField(max_length=100, unique=True, help_text="Bank account number")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Current account balance")
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Starting balance when account was added")
    is_active = models.BooleanField(default=True, help_text="Whether this account is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account_name} - {self.bank_name} ({self.account_number})"

    class Meta:
        ordering = ['-created_at']


class BankTransaction(models.Model):
    """Model to track bank deposits and withdrawals"""
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, help_text="Description of the transaction")
    reference = models.CharField(max_length=100, blank=True, help_text="Transaction reference number")
    transaction_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2, editable=False, help_text="Account balance after this transaction")

    def save(self, *args, **kwargs):
        """Update account balance when transaction is saved"""
        # Check if this is a new transaction (not yet in database)
        is_new = self.pk is None or not BankTransaction.objects.filter(pk=self.pk).exists()

        if is_new:
            if self.transaction_type == 'deposit':
                self.account.balance += self.amount
            else:  # withdrawal
                if self.amount > self.account.balance:
                    raise ValueError("Insufficient balance for withdrawal!")
                self.account.balance -= self.amount

            self.balance_after = self.account.balance
            self.account.save()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Restore account balance when transaction is deleted"""
        if self.transaction_type == 'deposit':
            self.account.balance -= self.amount
        else:  # withdrawal
            self.account.balance += self.amount

        self.account.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} RWF on {self.transaction_date}"

    class Meta:
        ordering = ['-transaction_date', '-created_at']


class SoldPig(models.Model):
    PIG_TYPE_CHOICES = [
        ('sow', 'Sow'),
        ('piglet', 'Piglet'),
    ]
    
    pig_type = models.CharField(max_length=10, choices=PIG_TYPE_CHOICES)
    sow = models.ForeignKey('Sow', on_delete=models.SET_NULL, null=True, blank=True)
    piglet = models.ForeignKey('Piglet', on_delete=models.SET_NULL, null=True, blank=True)
    
    sold_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    date_sold = models.DateField(default=now)

    def __str__(self):
        return f"{self.pig_type.capitalize()} Sold - {self.sow or self.piglet}"
    

@require_POST
def sell_sow(request):
    sow_id = request.POST.get("sow_id")
    selling_price = Decimal(request.POST.get("selling_price"))

    sow = get_object_or_404(Sow, id=sow_id)
    total_cost = sow.total_feeding_cost + sow.total_vaccination_cost + sow.total_health_cost + sow.total_breeding_cost

    SoldPig.objects.create(
        pig_type='sow',
        sow=sow,
        sold_price=selling_price,
        total_cost=total_cost,
    )

    sow.status = 'inactive'
    sow.save()

    messages.success(request, f"Sow '{sow.name}' sold successfully.")
    return redirect('sows')  # Make sure 'sows' is a valid named URL pattern


@require_POST
def sell_piglet(request):
    piglet_id = request.POST.get("piglet_id")
    selling_price = Decimal(request.POST.get("selling_price"))

    piglet = get_object_or_404(Piglet, id=piglet_id)
    total_cost = piglet.total_feeding_cost + piglet.total_health_cost
    # You may want to store profit separately elsewhere if needed

    SoldPig.objects.create(
        pig_type='piglet',
        piglet=piglet,
        sold_price=selling_price,
        total_cost=total_cost,
    )

    piglet.status = 'inactive'
    piglet.save()

    messages.success(request, f"Piglet '{piglet.name}' sold successfully.")
    return redirect('piglets')# farm/models.py - Add this new model at the end of the file

class PigTask(models.Model):
    """
    Task/Reminder system for individual pigs (sows and piglets)
    Allows scheduling tasks like vaccinations, weighing, diet changes, breeding, etc.
    """
    TASK_TYPE_CHOICES = [
        ('vaccination', 'Vaccination'),
        ('weighing', 'Weighing'),
        ('diet_change', 'Diet Change'),
        ('breeding', 'Breeding/Insemination'),
        ('health_check', 'Health Check'),
        ('feeding_plan', 'Feeding Plan'),
        ('breastfeeding', 'Breastfeeding Monitoring'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    PIG_TYPE_CHOICES = [
        ('sow', 'Sow'),
        ('piglet', 'Piglet'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Target pig
    pig_type = models.CharField(max_length=10, choices=PIG_TYPE_CHOICES)
    sow = models.ForeignKey('Sow', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    piglet = models.ForeignKey('Piglet', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    
    # Task details
    task_type = models.CharField(max_length=30, choices=TASK_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Additional notes or instructions")
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Notifications
    send_email = models.BooleanField(default=True, help_text="Send email reminder")
    email_sent = models.BooleanField(default=False, editable=False)
    reminder_days_before = models.PositiveIntegerField(default=2, help_text="Days before due date to send reminder")
    
    # Metadata
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date', '-created_at']
    
    def __str__(self):
        pig_name = self.sow.name if self.sow else (self.piglet.name if self.piglet else "Unknown")
        return f"{self.get_task_type_display()} for {pig_name} - {self.due_date}"
    
    def save(self, *args, **kwargs):
        # Auto-update status to overdue if past due date and still pending
        from django.utils import timezone
        if self.status == 'pending' and self.due_date < timezone.now().date():
            self.status = 'overdue'
        super().save(*args, **kwargs)
    
    @property
    def pig_name(self):
        """Get the name of the associated pig"""
        if self.sow:
            return self.sow.name
        elif self.piglet:
            return self.piglet.name
        return "Unknown"
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        delta = self.due_date - today
        return delta.days
    
    @property
    def should_send_reminder(self):
        """Check if reminder should be sent"""
        if self.email_sent or not self.send_email or self.status != 'pending':
            return False
        return self.days_until_due <= self.reminder_days_before
