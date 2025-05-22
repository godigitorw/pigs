# farm/forms.py
from django import forms
from .models import *
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import F


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'capacity', 'status', 'note']  # Explicitly exclude 'pig_count'
        exclude = ['pig_count']  # Ensure 'pig_count' is excluded
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Room Name'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Capacity'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional Notes'}),
        }



class SowForm(forms.ModelForm):
    category = forms.ChoiceField(
        choices=Sow.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    registered_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )

    room = forms.ModelChoiceField(
        queryset=Room.objects.all(),  # Will be overridden in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        empty_label="Select Room"
    )

    initial_cost = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter buying price'}),
        required=False,
        min_value=0,
        label="Bought Price (RWF)"
    )

    class Meta:
        model = Sow
        fields = ['room', 'registered_date', 'category', 'initial_cost','animal_tag_id']

   


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow all rooms (including full ones) to avoid "invalid choice" error
        self.fields['room'].queryset = Room.objects.all()

    def clean_room(self):
        room = self.cleaned_data.get('room')
        if room and room.pig_count >= room.capacity:
            raise forms.ValidationError(f"The selected room '{room.name}' is already full. Please choose another room.")
        return room


        
class PigletForm(forms.ModelForm):
    sow = forms.ModelChoiceField(
        queryset=Sow.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select Sow',
        }),
        label="Mother Sow"
    )
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Birth Date',
        }),
        label="Birth Date"
    )
    initial_weight = forms.FloatField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Initial Weight (kg)',
        }),
        label="Initial Weight (kg)"
    )
    
    # 🔽 NEW FIELD
    insemination_type = forms.ModelChoiceField(
        queryset=Insemination.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label="Insemination Type Used"
    )

    class Meta:
        model = Piglet
        fields = ['sow', 'birth_date', 'initial_weight', 'insemination_type','animal_tag_id']

    def save(self, commit=True):
        """Set current_weight from initial_weight before saving."""
        instance = super().save(commit=False)
        instance.current_weight = instance.initial_weight
        if commit:
            instance.save()
        return instance 

class FeedStockForm(forms.ModelForm):
    class Meta:
        model = FeedStock
        fields = ['name', 'feed_type', 'stock_quantity', 'unit', 'cost_per_unit']

    # Ensure cost_per_unit appears correctly formatted
    def __init__(self, *args, **kwargs):
        super(FeedStockForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['cost_per_unit'].initial = self.instance.cost_per_unit  # ✅ Ensure initial value is set


class FeedingRecordForm(forms.ModelForm):
    feeding_target_type = forms.ChoiceField(
        choices=[('sow', 'Sow'), ('piglet', 'Piglet')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    sow = forms.ModelChoiceField(
        queryset=Sow.objects.none(),  # Overridden in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    piglet = forms.ModelChoiceField(
        queryset=Piglet.objects.none(),  # Overridden in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    feed = forms.ModelChoiceField(
        queryset=FeedStock.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    quantity_used = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Quantity'}),
        required=True
    )

    class Meta:
        model = FeedingRecord
        fields = ['feeding_target_type', 'sow', 'piglet', 'feed', 'quantity_used']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active sows and piglets
        self.fields['sow'].queryset = Sow.objects.filter(status='active')
        self.fields['piglet'].queryset = Piglet.objects.filter(status='active')

    def clean(self):
        cleaned_data = super().clean()
        feeding_target_type = cleaned_data.get('feeding_target_type')
        sow = cleaned_data.get('sow')
        piglet = cleaned_data.get('piglet')

        if feeding_target_type == 'sow' and not sow:
            self.add_error('sow', 'You must select a sow for this feeding record.')
        elif feeding_target_type == 'piglet' and not piglet:
            self.add_error('piglet', 'You must select a piglet for this feeding record.')
        
        return cleaned_data


class InactivePigForm(forms.Form):
    pig_type = forms.ChoiceField(choices=[('sow', 'Sow'), ('piglet', 'Piglet')])
    pig_id = forms.UUIDField()
    reason = forms.CharField(widget=forms.Textarea) 



class InseminationForm(forms.ModelForm):
    class Meta:
        model = Insemination
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super(InseminationForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter insemination name',
            'id': 'id_name'
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter description (optional)',
            'rows': 4,
            'id': 'id_description'
        })


class BreedingRecordForm(forms.ModelForm):
    class Meta:
        model = BreedingRecord
        fields = [
            'sow', 'heat_detection_date',
            'insemination_1_date', 'insemination_2_date', 'insemination_3_date',
            'insemination_type', 'cost', 'expected_narrow_date',
            'status', 'note'
        ]

    def clean(self):
        cleaned_data = super().clean()
        sow = cleaned_data.get('sow')
        selected_insemination = cleaned_data.get('insemination_type')

        if sow:
            # ✅ First validation: check if sow was born in farm and insemination already used to produce it
            if sow.origin == 'born_in_farm':
                from farm.models import Piglet
                piglet = Piglet.objects.filter(unique_id=sow.unique_id).first()
                if piglet and piglet.insemination_type == selected_insemination:
                    raise forms.ValidationError("This insemination type was already used to produce this sow.")

            # ✅ Second validation: check if sow has an inherited insemination type (from piglet promotion)
            if sow.inherited_insemination_type and sow.inherited_insemination_type == selected_insemination:
                raise forms.ValidationError("This insemination type matches the inherited type from piglet stage. Please use a different one.")

        return cleaned_data
    
    

class IncomeRecordForm(forms.ModelForm):
    class Meta:
        model = IncomeRecord
        fields = ['date', 'source', 'description', 'amount']


class ExpenseRecordForm(forms.ModelForm):
    class Meta:
        model = ExpenseRecord
        fields = ['date', 'category', 'description', 'amount']



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
    return render(request, 'income/add_income.html', context)