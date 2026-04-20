from django.contrib import admin
from .models import (
    Specialization, Doctor, DoctorReview, Patient, Appointment,
    MedicalRecord, Vitals, InsuranceProvider, InsurancePolicy, InsuranceClaim,
    Invoice, Payment, PaymentRefund, Complaint, ComplaintReply, ChatSession, ChatMessage
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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'patient', 'amount', 'method', 'status', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['payment_id', 'patient__user__first_name', 'transaction_ref']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'paid_at']

    actions = ['mark_success', 'mark_failed']

    def mark_success(self, request, queryset):
        queryset.update(status='success')
    mark_success.short_description = "Mark as Success"

    def mark_failed(self, request, queryset):
        queryset.update(status='failed')
    mark_failed.short_description = "Mark as Failed"


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = ['payment', 'amount', 'processed_at']
    search_fields = ['payment__payment_id']


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['complaint_id', 'patient', 'subject', 'category', 'priority', 'status', 'created_at']
    list_filter = ['status', 'priority', 'category', 'created_at']
    search_fields = ['complaint_id', 'patient__user__first_name', 'subject']
    readonly_fields = ['complaint_id', 'created_at', 'updated_at']

    actions = ['mark_resolved', 'mark_closed']

    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved')
    mark_resolved.short_description = "Mark as Resolved"

    def mark_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_closed.short_description = "Mark as Closed"


@admin.register(ComplaintReply)
class ComplaintReplyAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'author', 'is_staff', 'created_at']
    list_filter = ['is_staff', 'created_at']
    search_fields = ['complaint__complaint_id', 'author__username']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'started_at', 'ended_at', 'is_active']
    list_filter = ['is_active', 'started_at']
    search_fields = ['session_id', 'user__username']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'content', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'session__session_id']

# Admin site customization
admin.site.site_header = "🏥 MediCare Hospital Admin"
admin.site.site_title = "MediCare Admin"
admin.site.index_title = "Hospital Management System"