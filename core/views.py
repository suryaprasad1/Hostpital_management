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
    Vitals, InsuranceProvider, InsurancePolicy, InsuranceClaim, Invoice, DoctorReview,
    Payment, Complaint, ComplaintReply, ChatSession, ChatMessage
)
from .forms import (
    UserRegistrationForm, PatientForm, AppointmentForm, AppointmentUpdateForm,
    MedicalRecordForm, VitalsForm, InsurancePolicyForm, InsuranceClaimForm, DoctorSearchForm,
    PaymentForm, ComplaintForm, ComplaintReplyForm, ChatMessageForm
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
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
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
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
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
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
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
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
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
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
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
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    records = MedicalRecord.objects.filter(patient=patient).select_related('doctor__user', 'appointment')
    vitals = Vitals.objects.filter(patient=patient).order_by('-recorded_at')[:10]
    return render(request, 'core/patient_history.html', {
        'patient': patient,
        'records': records,
        'vitals': vitals,
    })


@login_required
def medical_record_detail(request, pk):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    record = get_object_or_404(MedicalRecord, pk=pk, patient=patient)
    return render(request, 'core/medical_record_detail.html', {'record': record})


# ──────────────────────────────────────────────────────────
#  INSURANCE
# ──────────────────────────────────────────────────────────
@login_required
def insurance_list(request):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    policies = InsurancePolicy.objects.filter(patient=patient).select_related('provider')
    claims = InsuranceClaim.objects.filter(policy__patient=patient).select_related('policy__provider')
    return render(request, 'core/insurance_list.html', {
        'patient': patient,
        'policies': policies,
        'claims': claims,
    })


@login_required
def insurance_policy_add(request):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
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
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    policy = get_object_or_404(InsurancePolicy, pk=pk, patient=patient)
    claims = InsuranceClaim.objects.filter(policy=policy)
    return render(request, 'core/insurance_policy_detail.html', {
        'policy': policy,
        'claims': claims,
    })


@login_required
def insurance_claim_add(request):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
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
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    invoices = Invoice.objects.filter(patient=patient).select_related('appointment')
    return render(request, 'core/invoice_list.html', {'invoices': invoices, 'patient': patient})


@login_required
def invoice_detail(request, pk):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    invoice = get_object_or_404(Invoice, pk=pk, patient=patient)
    return render(request, 'core/invoice_detail.html', {'invoice': invoice})


# ──────────────────────────────────────────────────────────
#  PAYMENTS
# ──────────────────────────────────────────────────────────
@login_required
def payment_list(request):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    payments = Payment.objects.filter(patient=patient).select_related('invoice', 'appointment')
    return render(request, 'core/payment_list.html', {'payments': payments, 'patient': patient})


@login_required
def payment_create(request, invoice_id=None):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    invoice = None
    if invoice_id:
        invoice = get_object_or_404(Invoice, pk=invoice_id, patient=patient)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.patient = patient
            payment.invoice = invoice
            payment.status = Payment.SUCCESS
            payment.save()
            messages.success(request, f'Payment of ₹{payment.amount} successful!')
            return redirect('payment_list')
    else:
        initial = {}
        if invoice:
            initial['amount'] = invoice.balance_due
        form = PaymentForm(initial=initial)
    return render(request, 'core/payment_form.html', {
        'form': form,
        'patient': patient,
        'invoice': invoice,
    })


@login_required
def payment_detail(request, pk):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    payment = get_object_or_404(Payment, pk=pk, patient=patient)
    return render(request, 'core/payment_detail.html', {'payment': payment})


# ──────────────────────────────────────────────────────────
#  COMPLAINTS
# ──────────────────────────────────────────────────────────
@login_required
def complaint_list(request):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    complaints = Complaint.objects.filter(patient=patient).select_related('assigned_to')
    return render(request, 'core/complaint_list.html', {'complaints': complaints, 'patient': patient})


@login_required
def complaint_create(request):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.patient = patient
            complaint.save()
            messages.success(request, f'Complaint {complaint.complaint_id} submitted successfully!')
            return redirect('complaint_list')
    else:
        form = ComplaintForm()
    return render(request, 'core/complaint_form.html', {'form': form, 'action': 'Submit Complaint'})


@login_required
def complaint_detail(request, pk):
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.info(request, 'Please complete your patient profile first.')
        return redirect('patient_create')
    complaint = get_object_or_404(Complaint, pk=pk, patient=patient)
    replies = complaint.replies.select_related('author')
    if request.method == 'POST':
        reply_form = ComplaintReplyForm(request.POST, instance=complaint)
        if reply_form.is_valid():
            reply = complaint.replies.create(
                author=request.user,
                message=request.POST.get('reply_message', ''),
                is_staff=request.user.is_staff
            )
            messages.success(request, 'Reply added successfully!')
            return redirect('complaint_detail', pk=pk)
    else:
        reply_form = ComplaintReplyForm()
    return render(request, 'core/complaint_detail.html', {
        'complaint': complaint,
        'replies': replies,
        'reply_form': reply_form,
    })


# ──────────────────────────────────────────────────────────
#  CHATBOT
# ──────────────────────────────────────────────────────────
@login_required
def chatbot(request):
    patient = None
    if hasattr(request.user, 'patient_profile'):
        patient = request.user.patient_profile

    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            message_content = form.cleaned_data['message']
            session, created = ChatSession.objects.get_or_create(
                is_active=True,
                user=request.user if request.user.is_authenticated else None
            )
            ChatMessage.objects.create(
                session=session,
                role=ChatMessage.USER,
                content=message_content
            )

            bot_response = get_bot_response(message_content)

            ChatMessage.objects.create(
                session=session,
                role=ChatMessage.BOT,
                content=bot_response
            )
            return redirect('chatbot')
    else:
        form = ChatMessageForm()

    session = ChatSession.objects.filter(
        user=request.user if request.user.is_authenticated else None,
        is_active=True
    ).first()

    if session:
        messages = session.messages.all()
    else:
        messages = []

    return render(request, 'core/chatbot.html', {
        'form': form,
        'messages': messages,
        'patient': patient,
    })


def get_bot_response(message):
    message = message.lower()

    responses = {
        'appointment': 'To book an appointment, go to the Appointments section and click "Book Appointment". You can select a doctor and choose your preferred date and time.',
        'book': 'To book an appointment, go to the Appointments section and click "Book Appointment". You can select a doctor and choose your preferred date and time.',
        'doctor': 'You can view all available doctors on our Doctors page. Use the search filter to find doctors by specialization or name.',
        'specialization': 'We have various specializations including General Medicine, Cardiology, Neurology, Orthopedics, Pediatrics, and more. Check our Doctors page for the complete list.',
        'insurance': 'You can manage your insurance policies in the Insurance section. You can add new policies and view existing claims.',
        'invoice': 'You can view your invoices in the Invoices section. Outstanding payments can be paid online.',
        'payment': 'To make a payment, go to the Payments section or click on any unpaid invoice. We accept Cash, Card, UPI, Net Banking, and Wallet.',
        'contact': 'You can reach us at: Phone: +91-XXX-XXX-XXXX, Email: info@hospital.com, Address: Hospital Address',
        'emergency': 'For emergencies, please call our 24/7 emergency helpline: +91-XXX-XXX-XXXX',
        'hello': 'Hello! How can I help you today? You can ask about appointments, doctors, payments, insurance, or any other hospital services.',
        'hi': 'Hello! How can I help you today? You can ask about appointments, doctors, payments, insurance, or any other hospital services.',
        'help': 'I can help you with: booking appointments, finding doctors, viewing invoices, making payments, insurance queries, and more. Just ask!',
    }

    for key, response in responses.items():
        if key in message:
            return response

    return 'Thank you for your message. For detailed assistance, please contact our helpdesk or visit the relevant section on your dashboard. You can also call us at +91-XXX-XXX-XXXX.'