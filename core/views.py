from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse

from .models import (
    Patient, Doctor, Specialization, Appointment, MedicalRecord,
    Vitals, InsuranceProvider, InsurancePolicy, InsuranceClaim, Invoice, DoctorReview
)
from .forms import (
    UserRegistrationForm, PatientForm, AppointmentForm, AppointmentUpdateForm,
    MedicalRecordForm, VitalsForm, InsurancePolicyForm, InsuranceClaimForm, DoctorSearchForm
)


# ──────────────────────────────────────────────────────────
#  HOME & AUTH
# ──────────────────────────────────────────────────────────
def home(request):
    doctors = Doctor.objects.filter(status='available').select_related('user', 'specialization')[:6]
    specializations = Specialization.objects.annotate(doc_count=Count('doctor'))
    stats = {
        'doctors': Doctor.objects.count(),
        'patients': Patient.objects.count(),
        'appointments': Appointment.objects.count(),
        'specializations': Specialization.objects.count(),
    }
    return render(request, 'core/home.html', {
        'doctors': doctors,
        'specializations': specializations,
        'stats': stats,
    })


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        patient_form = PatientForm(request.POST, request.FILES)
        if user_form.is_valid() and patient_form.is_valid():
            user = user_form.save()
            patient = patient_form.save(commit=False)
            patient.user = user
            patient.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('dashboard')
    else:
        user_form = UserRegistrationForm()
        patient_form = PatientForm()
    return render(request, 'registration/register.html', {
        'user_form': user_form,
        'patient_form': patient_form,
    })


@login_required
def dashboard(request):
    try:
        patient = request.user.patient_profile
        upcoming = Appointment.objects.filter(
            patient=patient,
            appointment_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).select_related('doctor__user', 'doctor__specialization')[:5]
        recent_records = MedicalRecord.objects.filter(patient=patient).select_related('doctor__user')[:3]
        active_policies = InsurancePolicy.objects.filter(patient=patient, status='active')
        pending_invoices = Invoice.objects.filter(patient=patient, status__in=['unpaid', 'partial'])
        return render(request, 'core/dashboard.html', {
            'patient': patient,
            'upcoming': upcoming,
            'recent_records': recent_records,
            'active_policies': active_policies,
            'pending_invoices': pending_invoices,
        })
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your profile.')
        return redirect('patient_create')


# ──────────────────────────────────────────────────────────
#  DOCTORS
# ──────────────────────────────────────────────────────────
def doctor_list(request):
    form = DoctorSearchForm(request.GET)
    doctors = Doctor.objects.filter(status='available').select_related('user', 'specialization')
    if form.is_valid():
        if form.cleaned_data.get('specialization'):
            doctors = doctors.filter(specialization__name__icontains=form.cleaned_data['specialization'])
        if form.cleaned_data.get('name'):
            q = form.cleaned_data['name']
            doctors = doctors.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q))
        if form.cleaned_data.get('max_fee'):
            doctors = doctors.filter(consultation_fee__lte=form.cleaned_data['max_fee'])
    specializations = Specialization.objects.all()
    return render(request, 'core/doctor_list.html', {
        'doctors': doctors,
        'form': form,
        'specializations': specializations,
    })


def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    reviews = DoctorReview.objects.filter(doctor=doctor).select_related('patient__user')[:5]
    can_review = False
    if request.user.is_authenticated:
        try:
            patient = request.user.patient_profile
            can_review = Appointment.objects.filter(
                patient=patient, doctor=doctor, status='completed'
            ).exists() and not DoctorReview.objects.filter(doctor=doctor, patient=patient).exists()
        except Patient.DoesNotExist:
            pass
    return render(request, 'core/doctor_detail.html', {
        'doctor': doctor,
        'reviews': reviews,
        'can_review': can_review,
    })


# ──────────────────────────────────────────────────────────
#  PATIENTS
# ──────────────────────────────────────────────────────────
@login_required
def patient_profile(request):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        return redirect('patient_create')
    return render(request, 'core/patient_profile.html', {'patient': patient})


@login_required
def patient_create(request):
    if hasattr(request.user, 'patient_profile'):
        return redirect('patient_profile')
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user
            patient.save()
            messages.success(request, 'Patient profile created successfully!')
            return redirect('dashboard')
    else:
        form = PatientForm()
    return render(request, 'core/patient_form.html', {'form': form, 'action': 'Create'})


@login_required
def patient_edit(request):
    patient = get_object_or_404(Patient, user=request.user)
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('patient_profile')
    else:
        form = PatientForm(instance=patient)
    return render(request, 'core/patient_form.html', {'form': form, 'action': 'Update'})


# ──────────────────────────────────────────────────────────
#  APPOINTMENTS
# ──────────────────────────────────────────────────────────
@login_required
def appointment_list(request):
    patient = get_object_or_404(Patient, user=request.user)
    status_filter = request.GET.get('status', '')
    appointments = Appointment.objects.filter(patient=patient).select_related('doctor__user', 'doctor__specialization')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    return render(request, 'core/appointment_list.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'status_choices': Appointment.STATUS_CHOICES,
    })


@login_required
def appointment_book(request, doctor_id=None):
    patient = get_object_or_404(Patient, user=request.user)
    initial = {}
    if doctor_id:
        initial['doctor'] = doctor_id
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.fee = appointment.doctor.consultation_fee
            appointment.save()
            messages.success(request, f'Appointment booked successfully! ID: {appointment.appointment_id}')
            return redirect('appointment_detail', pk=appointment.pk)
    else:
        form = AppointmentForm(initial=initial)
    return render(request, 'core/appointment_form.html', {'form': form, 'patient': patient})


@login_required
def appointment_detail(request, pk):
    patient = get_object_or_404(Patient, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, patient=patient)
    try:
        medical_record = appointment.medical_record
    except MedicalRecord.DoesNotExist:
        medical_record = None
    return render(request, 'core/appointment_detail.html', {
        'appointment': appointment,
        'medical_record': medical_record,
    })


@login_required
def appointment_cancel(request, pk):
    patient = get_object_or_404(Patient, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, patient=patient)
    if appointment.status in ['pending', 'confirmed']:
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    else:
        messages.error(request, 'This appointment cannot be cancelled.')
    return redirect('appointment_list')


# ──────────────────────────────────────────────────────────
#  MEDICAL HISTORY
# ──────────────────────────────────────────────────────────
@login_required
def patient_history(request):
    patient = get_object_or_404(Patient, user=request.user)
    records = MedicalRecord.objects.filter(patient=patient).select_related('doctor__user', 'appointment')
    vitals = Vitals.objects.filter(patient=patient).order_by('-recorded_at')[:10]
    return render(request, 'core/patient_history.html', {
        'patient': patient,
        'records': records,
        'vitals': vitals,
    })


@login_required
def medical_record_detail(request, pk):
    patient = get_object_or_404(Patient, user=request.user)
    record = get_object_or_404(MedicalRecord, pk=pk, patient=patient)
    return render(request, 'core/medical_record_detail.html', {'record': record})


# ──────────────────────────────────────────────────────────
#  INSURANCE
# ──────────────────────────────────────────────────────────
@login_required
def insurance_list(request):
    patient = get_object_or_404(Patient, user=request.user)
    policies = InsurancePolicy.objects.filter(patient=patient).select_related('provider')
    claims = InsuranceClaim.objects.filter(policy__patient=patient).select_related('policy__provider')
    return render(request, 'core/insurance_list.html', {
        'patient': patient,
        'policies': policies,
        'claims': claims,
    })


@login_required
def insurance_policy_add(request):
    patient = get_object_or_404(Patient, user=request.user)
    if request.method == 'POST':
        form = InsurancePolicyForm(request.POST)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.patient = patient
            policy.save()
            messages.success(request, f'Insurance policy {policy.policy_number} added successfully!')
            return redirect('insurance_list')
    else:
        form = InsurancePolicyForm()
    return render(request, 'core/insurance_form.html', {'form': form, 'action': 'Add Policy'})


@login_required
def insurance_policy_detail(request, pk):
    patient = get_object_or_404(Patient, user=request.user)
    policy = get_object_or_404(InsurancePolicy, pk=pk, patient=patient)
    claims = InsuranceClaim.objects.filter(policy=policy)
    return render(request, 'core/insurance_policy_detail.html', {
        'policy': policy,
        'claims': claims,
    })


@login_required
def insurance_claim_add(request):
    patient = get_object_or_404(Patient, user=request.user)
    if request.method == 'POST':
        form = InsuranceClaimForm(patient=patient, data=request.POST, files=request.FILES)
        if form.is_valid():
            claim = form.save()
            messages.success(request, f'Claim {claim.claim_id} submitted successfully!')
            return redirect('insurance_list')
    else:
        form = InsuranceClaimForm(patient=patient)
    return render(request, 'core/insurance_claim_form.html', {'form': form, 'action': 'Submit Claim'})


# ──────────────────────────────────────────────────────────
#  INVOICES / BILLING
# ──────────────────────────────────────────────────────────
@login_required
def invoice_list(request):
    patient = get_object_or_404(Patient, user=request.user)
    invoices = Invoice.objects.filter(patient=patient).select_related('appointment')
    return render(request, 'core/invoice_list.html', {'invoices': invoices, 'patient': patient})


@login_required
def invoice_detail(request, pk):
    patient = get_object_or_404(Patient, user=request.user)
    invoice = get_object_or_404(Invoice, pk=pk, patient=patient)
    return render(request, 'core/invoice_detail.html', {'invoice': invoice})