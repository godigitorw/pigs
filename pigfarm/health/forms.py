from django import forms
from .models import *

class HealthRecordForm(forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = ['health_target_type', 'sow', 'piglet', 'health_issue', 'treatment_given', 'treatment_date', 'status', 'cost', 'note']
        widgets = {
            'treatment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'health_target_type': forms.Select(attrs={'class': 'form-control'}),
            'sow': forms.Select(attrs={'class': 'form-control'}),
            'piglet': forms.Select(attrs={'class': 'form-control'}),
            'health_issue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter health issue'}),
            'treatment_given': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter treatment details'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }



class VaccinationForm(forms.ModelForm):
    class Meta:
        model = Vaccination
        fields = ['name', 'duration_days']

    # Custom styling for form fields
    def __init__(self, *args, **kwargs):
        super(VaccinationForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'form-control custom-input',
            'placeholder': 'Enter vaccine name'
        })
        self.fields['duration_days'].widget.attrs.update({
            'class': 'form-control custom-input',
            'placeholder': 'Enter duration in days'
        })


class VaccinationRecordForm(forms.ModelForm):
    class Meta:
        model = VaccinationRecord
        fields = ['vaccination_target_type', 'sow', 'piglet', 'vaccine', 'vaccination_date', 'cost']



class WeightRecordForm(forms.ModelForm):
    class Meta:
        model = WeightRecord
        fields = ['target_type', 'sow', 'piglet', 'recorded_date', 'weight']
        widgets = {
            'target_type': forms.Select(attrs={'class': 'form-control'}),
            'sow': forms.Select(attrs={'class': 'form-control'}),
            'piglet': forms.Select(attrs={'class': 'form-control'}),
            'recorded_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter actual weight in kg'}),
        }


