from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ─────────────────────────────────────────────
#  DOCTOR
# ─────────────────────────────────────────────
class Specialization(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='🩺')

    def __str__(self):
        return self.name


class Doctor(models.Model):
    AVAILABLE = 'available'
    ON_LEAVE = 'on_leave'
    INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (AVAILABLE, 'Available'),
        (ON_LEAVE, 'On Leave'),
        (INACTIVE, 'Inactive'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True)
    registration_number = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=15)
    qualification = models.CharField(max_length=200)
    experience_years = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=AVAILABLE)
    available_days = models.CharField(
        max_length=100,
        default='Mon,Tue,Wed,Thu,Fri',
        help_text='Comma-separated days e.g. Mon,Tue,Wed'
    )
    available_from = models.TimeField(default='09:00')
    available_to = models.TimeField(default='17:00')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"

    def get_full_name(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

    @property
    def total_appointments(self):
        return self.appointments.count()

    @property
    def rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0.0


class DoctorReview(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reviews')
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)  # 1-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['doctor', 'patient']

    def __str__(self):
        return f"Review by {self.patient} for {self.doctor}"


# ─────────────────────────────────────────────
#  PATIENT
# ─────────────────────────────────────────────
class Patient(models.Model):
    BLOOD_GROUPS = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    patient_id = models.CharField(max_length=20, unique=True, editable=False)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, blank=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    allergies = models.TextField(blank=True, help_text='List known allergies')
    photo = models.ImageField(upload_to='patients/', blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.patient_id})"

    def save(self, *args, **kwargs):
        if not self.patient_id:
            import random
            self.patient_id = f"PAT{timezone.now().year}{random.randint(10000, 99999)}"
        super().save(*args, **kwargs)

    @property
    def age(self):
        today = timezone.now().date()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @property
    def full_name(self):
        return self.user.get_full_name()


# ─────────────────────────────────────────────
#  APPOINTMENT
# ─────────────────────────────────────────────
class Appointment(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    NO_SHOW = 'no_show'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
        (NO_SHOW, 'No Show'),
    ]
    CONSULTATION = 'consultation'
    FOLLOW_UP = 'follow_up'
    EMERGENCY = 'emergency'
    TYPE_CHOICES = [
        (CONSULTATION, 'Consultation'),
        (FOLLOW_UP, 'Follow-up'),
        (EMERGENCY, 'Emergency'),
    ]

    appointment_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    appointment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=CONSULTATION)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    reason = models.TextField(help_text='Reason for visit')
    symptoms = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text='Doctor notes')
    prescription = models.TextField(blank=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        unique_together = ['doctor', 'appointment_date', 'appointment_time']

    def __str__(self):
        return f"APT-{self.appointment_id}: {self.patient} → {self.doctor} on {self.appointment_date}"

    def save(self, *args, **kwargs):
        if not self.appointment_id:
            import random
            self.appointment_id = f"APT{timezone.now().year}{random.randint(10000, 99999)}"
        if not self.fee:
            self.fee = self.doctor.consultation_fee
        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        return self.appointment_date >= timezone.now().date() and self.status in [self.PENDING, self.CONFIRMED]


# ─────────────────────────────────────────────
#  PATIENT HISTORY
# ─────────────────────────────────────────────
class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='medical_records')
    appointment = models.OneToOneField(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_record'
    )
    record_date = models.DateField(default=timezone.now)
    diagnosis = models.TextField()
    treatment = models.TextField()
    prescription = models.TextField(blank=True)
    lab_results = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-record_date']

    def __str__(self):
        return f"Record: {self.patient} on {self.record_date}"


class Vitals(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_pressure_systolic = models.PositiveSmallIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveSmallIntegerField(null=True, blank=True)
    pulse_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    oxygen_saturation = models.PositiveSmallIntegerField(null=True, blank=True)
    blood_sugar = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Vitals: {self.patient} at {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def bmi(self):
        if self.weight_kg and self.height_cm:
            h = float(self.height_cm) / 100
            return round(float(self.weight_kg) / (h * h), 1)
        return None


# ─────────────────────────────────────────────
#  INSURANCE
# ─────────────────────────────────────────────
class InsuranceProvider(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='insurance/', blank=True, null=True)

    def __str__(self):
        return self.name


class InsurancePolicy(models.Model):
    ACTIVE = 'active'
    EXPIRED = 'expired'
    PENDING = 'pending'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (EXPIRED, 'Expired'),
        (PENDING, 'Pending'),
        (CANCELLED, 'Cancelled'),
    ]
    INDIVIDUAL = 'individual'
    FAMILY = 'family'
    GROUP = 'group'
    TYPE_CHOICES = [
        (INDIVIDUAL, 'Individual'),
        (FAMILY, 'Family'),
        (GROUP, 'Group'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='insurance_policies')
    provider = models.ForeignKey(InsuranceProvider, on_delete=models.CASCADE, related_name='policies')
    policy_number = models.CharField(max_length=100, unique=True)
    policy_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=INDIVIDUAL)
    policy_name = models.CharField(max_length=200)
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    premium_amount = models.DecimalField(max_digits=8, decimal_places=2)
    deductible = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    copay_percentage = models.PositiveSmallIntegerField(default=0, help_text='Patient pays X% of bill')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)
    covered_conditions = models.TextField(blank=True, help_text='Comma-separated conditions covered')
    exclusions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = 'Insurance Policies'

    def __str__(self):
        return f"{self.policy_number} - {self.patient} ({self.provider})"

    @property
    def is_active(self):
        today = timezone.now().date()
        return self.status == self.ACTIVE and self.start_date <= today <= self.end_date

    @property
    def days_remaining(self):
        today = timezone.now().date()
        delta = self.end_date - today
        return delta.days if delta.days > 0 else 0


class InsuranceClaim(models.Model):
    SUBMITTED = 'submitted'
    UNDER_REVIEW = 'under_review'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    PAID = 'paid'
    STATUS_CHOICES = [
        (SUBMITTED, 'Submitted'),
        (UNDER_REVIEW, 'Under Review'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (PAID, 'Paid'),
    ]

    claim_id = models.CharField(max_length=20, unique=True, editable=False)
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE, related_name='claims')
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='insurance_claims'
    )
    claim_date = models.DateField(default=timezone.now)
    claimed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SUBMITTED)
    diagnosis_code = models.CharField(max_length=20, blank=True, help_text='ICD-10 code')
    description = models.TextField()
    documents = models.FileField(upload_to='claims/', blank=True, null=True)
    rejection_reason = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-claim_date']

    def __str__(self):
        return f"Claim {self.claim_id} - {self.policy.patient}"

    def save(self, *args, **kwargs):
        if not self.claim_id:
            import random
            self.claim_id = f"CLM{timezone.now().year}{random.randint(10000, 99999)}"
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
#  BILLING
# ─────────────────────────────────────────────
class Invoice(models.Model):
    UNPAID = 'unpaid'
    PARTIAL = 'partial'
    PAID = 'paid'
    STATUS_CHOICES = [
        (UNPAID, 'Unpaid'),
        (PARTIAL, 'Partially Paid'),
        (PAID, 'Paid'),
    ]

    invoice_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices'
    )
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    insurance_covered = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=UNPAID)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_id} - {self.patient}"

    def save(self, *args, **kwargs):
        if not self.invoice_id:
            import random
            self.invoice_id = f"INV{timezone.now().year}{random.randint(10000, 99999)}"
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount - self.insurance_covered
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid