from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Doctors
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),

    # Patients
    path('patient/profile/', views.patient_profile, name='patient_profile'),
    path('patient/create/', views.patient_create, name='patient_create'),
    path('patient/edit/', views.patient_edit, name='patient_edit'),

    # Appointments
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/book/', views.appointment_book, name='appointment_book'),
    path('appointments/book/<int:doctor_id>/', views.appointment_book, name='appointment_book_doctor'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),

    # Medical History
    path('history/', views.patient_history, name='patient_history'),
    path('history/<int:pk>/', views.medical_record_detail, name='medical_record_detail'),

    # Insurance
    path('insurance/', views.insurance_list, name='insurance_list'),
    path('insurance/add/', views.insurance_policy_add, name='insurance_policy_add'),
    path('insurance/<int:pk>/', views.insurance_policy_detail, name='insurance_policy_detail'),
    path('insurance/claim/add/', views.insurance_claim_add, name='insurance_claim_add'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/create/<int:invoice_id>/', views.payment_create, name='payment_create_invoice'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),

    # Complaints
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints/create/', views.complaint_create, name='complaint_create'),
    path('complaints/<int:pk>/', views.complaint_detail, name='complaint_detail'),

    # Chatbot
    path('chatbot/', views.chatbot, name='chatbot'),
]