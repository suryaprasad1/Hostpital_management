from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Patient, Doctor, Appointment, MedicalRecord, Vitals, InsurancePolicy, InsuranceClaim, Invoice


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        exclude = ['user', 'patient_id', 'registered_at', 'is_active']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'appointment_type', 'reason', 'symptoms']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
            'symptoms': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Doctor
        self.fields['doctor'].queryset = Doctor.objects.filter(status='available').select_related('user', 'specialization')
        self.fields['doctor'].label_from_instance = lambda obj: f"{obj.get_full_name()} - {obj.specialization} (₹{obj.consultation_fee})"


class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'notes', 'prescription']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
            'prescription': forms.Textarea(attrs={'rows': 4}),
        }


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        exclude = ['patient', 'doctor', 'appointment', 'created_at']
        widgets = {
            'record_date': forms.DateInput(attrs={'type': 'date'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
            'diagnosis': forms.Textarea(attrs={'rows': 4}),
            'treatment': forms.Textarea(attrs={'rows': 4}),
            'prescription': forms.Textarea(attrs={'rows': 4}),
            'lab_results': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class VitalsForm(forms.ModelForm):
    class Meta:
        model = Vitals
        exclude = ['patient', 'appointment', 'recorded_at']


class InsurancePolicyForm(forms.ModelForm):
    class Meta:
        model = InsurancePolicy
        exclude = ['patient', 'created_at']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'covered_conditions': forms.Textarea(attrs={'rows': 3}),
            'exclusions': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class InsuranceClaimForm(forms.ModelForm):
    class Meta:
        model = InsuranceClaim
        fields = ['policy', 'appointment', 'claim_date', 'claimed_amount', 'diagnosis_code', 'description', 'documents']
        widgets = {
            'claim_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, patient=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if patient:
            self.fields['policy'].queryset = InsurancePolicy.objects.filter(patient=patient, status='active')
            self.fields['appointment'].queryset = Appointment.objects.filter(
                patient=patient, status='completed'
            )


class DoctorSearchForm(forms.Form):
    specialization = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Specialization...'}))
    name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Doctor name...'}))
    max_fee = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'placeholder': 'Max fee...'}))