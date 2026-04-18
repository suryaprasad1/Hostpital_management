from django.contrib import admin
from .models import (
    Specialization, Doctor, DoctorReview, Patient, Appointment,
    MedicalRecord, Vitals, InsuranceProvider, InsurancePolicy, InsuranceClaim, Invoice
)


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'specialization', 'registration_number', 'consultation_fee', 'status']
    list_filter = ['status', 'specialization']
    search_fields = ['user__first_name', 'user__last_name', 'registration_number']
    raw_id_fields = ['user']

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Doctor Name'


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'patient_id', 'gender', 'blood_group', 'phone', 'city']
    list_filter = ['gender', 'blood_group', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'patient_id', 'phone']
    raw_id_fields = ['user']
    readonly_fields = ['patient_id', 'registered_at']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'is_paid']
    list_filter = ['status', 'appointment_type', 'is_paid', 'appointment_date']
    search_fields = ['appointment_id', 'patient__user__first_name', 'doctor__user__first_name']
    readonly_fields = ['appointment_id', 'created_at']
    date_hierarchy = 'appointment_date'

    actions = ['mark_confirmed', 'mark_completed']

    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    mark_confirmed.short_description = "Mark as Confirmed"

    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_completed.short_description = "Mark as Completed"


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'record_date', 'follow_up_date']
    list_filter = ['record_date']
    search_fields = ['patient__user__first_name', 'diagnosis']
    date_hierarchy = 'record_date'


@admin.register(Vitals)
class VitalsAdmin(admin.ModelAdmin):
    list_display = ['patient', 'recorded_at', 'weight_kg', 'blood_pressure_systolic', 'pulse_rate']
    list_filter = ['recorded_at']
    search_fields = ['patient__user__first_name']


@admin.register(InsuranceProvider)
class InsuranceProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone', 'email', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = ['policy_number', 'patient', 'provider', 'policy_type', 'coverage_amount', 'status', 'end_date']
    list_filter = ['status', 'policy_type', 'provider']
    search_fields = ['policy_number', 'patient__user__first_name']
    readonly_fields = ['created_at']


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = ['claim_id', 'policy', 'claim_date', 'claimed_amount', 'approved_amount', 'status']
    list_filter = ['status', 'claim_date']
    search_fields = ['claim_id', 'policy__patient__user__first_name']
    readonly_fields = ['claim_id', 'created_at']

    actions = ['approve_claims', 'reject_claims']

    def approve_claims(self, request, queryset):
        for claim in queryset:
            claim.status = 'approved'
            claim.approved_amount = claim.claimed_amount
            claim.save()
    approve_claims.short_description = "Approve selected claims"

    def reject_claims(self, request, queryset):
        queryset.update(status='rejected')
    reject_claims.short_description = "Reject selected claims"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_id', 'patient', 'issue_date', 'total_amount', 'amount_paid', 'status']
    list_filter = ['status', 'issue_date']
    search_fields = ['invoice_id', 'patient__user__first_name']
    readonly_fields = ['invoice_id', 'created_at']

# Admin site customization
admin.site.site_header = "🏥 MediCare Hospital Admin"
admin.site.site_title = "MediCare Admin"
admin.site.index_title = "Hospital Management System"