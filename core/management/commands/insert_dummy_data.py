from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from core.models import (
    Specialization, Doctor, Patient, Appointment, Invoice, Payment, Complaint
)


class Command(BaseCommand):
    help = 'Insert dummy data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating specializations...')
        specializations = self._create_specializations()
        
        self.stdout.write('Creating doctors...')
        doctors = self._create_doctors(specializations)
        
        self.stdout.write('Creating patient...')
        patient = self._create_patient()
        
        self.stdout.write('Creating appointments...')
        appointments = self._create_appointments(patient, doctors)
        
        self.stdout.write('Creating invoices...')
        invoices = self._create_invoices(patient, appointments)
        
        self.stdout.write('Creating payments...')
        self._create_payments(patient, invoices)
        
        self.stdout.write('Creating complaints...')
        self._create_complaints(patient)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Dummy data created successfully!'))
        self.stdout.write('\n📋 Test Accounts:')
        self.stdout.write('   Patient: username=patientdemo, password=patient123')
        self.stdout.write('   Doctors: username=dr_rajesh, password=doctor123 (and dr_priya, dr_amit, etc.)')

    def _create_specializations(self):
        specs_data = [
            {'name': 'Cardiology', 'description': 'Heart and cardiovascular system', 'icon': 'heart'},
            {'name': 'Neurology', 'description': 'Brain and nervous system', 'icon': 'brain'},
            {'name': 'Orthopedics', 'description': 'Bones, joints, and muscles', 'icon': 'bone'},
            {'name': 'Pediatrics', 'description': 'Healthcare for children', 'icon': 'baby'},
            {'name': 'General Medicine', 'description': 'General healthcare', 'icon': 'stethoscope'},
            {'name': 'Dermatology', 'description': 'Skin, hair, and nails', 'icon': 'skin'},
        ]
        specs = []
        for spec_data in specs_data:
            spec, _ = Specialization.objects.get_or_create(
                name=spec_data['name'],
                defaults=spec_data
            )
            specs.append(spec)
        return specs

    def _create_doctors(self, specializations):
        doctors_data = [
            {'first_name': 'Rajesh', 'last_name': 'Kumar', 'username': 'dr_rajesh', 'email': 'rajesh@medicare.com', 'qualification': 'MD, DM Cardiology', 'fee': 800},
            {'first_name': 'Priya', 'last_name': 'Sharma', 'username': 'dr_priya', 'email': 'priya@medicare.com', 'qualification': 'MD, DM Neurology', 'fee': 900},
            {'first_name': 'Amit', 'last_name': 'Patel', 'username': 'dr_amit', 'email': 'amit@medicare.com', 'qualification': 'MS Orthopedics', 'fee': 700},
            {'first_name': 'Sneha', 'last_name': 'Reddy', 'username': 'dr_sneha', 'email': 'sneha@medicare.com', 'qualification': 'MD Pediatrics', 'fee': 500},
            {'first_name': 'Vikram', 'last_name': 'Singh', 'username': 'dr_vikram', 'email': 'vikram@medicare.com', 'qualification': 'MD General Medicine', 'fee': 400},
            {'first_name': 'Anjali', 'last_name': 'Mehta', 'username': 'dr_anjali', 'email': 'anjali@medicare.com', 'qualification': 'MD Dermatology', 'fee': 550},
        ]
        doctors = []
        for i, doc_data in enumerate(doctors_data):
            user, created = User.objects.get_or_create(
                username=doc_data['username'],
                defaults={
                    'first_name': doc_data['first_name'],
                    'last_name': doc_data['last_name'],
                    'email': doc_data['email'],
                }
            )
            if created:
                user.set_password('doctor123')
                user.save()
            
            doctor, created = Doctor.objects.get_or_create(
                user=user,
                defaults={
                    'specialization': specializations[i],
                    'registration_number': f'DR{1000+i}',
                    'phone': f'98765{i:05d}',
                    'qualification': doc_data['qualification'],
                    'experience_years': random.randint(5, 20),
                    'consultation_fee': Decimal(doc_data['fee']),
                    'bio': f'Dr. {doc_data["first_name"]} {doc_data["last_name"]} is a highly qualified {doc_data["qualification"]} with years of experience.',
                    'status': Doctor.AVAILABLE,
                }
            )
            doctors.append(doctor)
        return doctors

    def _create_patient(self):
        user, created = User.objects.get_or_create(
            username='patientdemo',
            defaults={
                'first_name': 'Demo',
                'last_name': 'Patient',
                'email': 'demo@patient.com',
            }
        )
        if created:
            user.set_password('patient123')
            user.save()
        
        patient, created = Patient.objects.get_or_create(
            user=user,
            defaults={
                'date_of_birth': '1990-05-15',
                'gender': 'M',
                'blood_group': 'O+',
                'phone': '9876543210',
                'address': '123 Test Street',
                'city': 'Hyderabad',
                'state': 'Telangana',
                'pincode': '500001',
                'emergency_contact_name': 'Emergency Contact',
                'emergency_contact_phone': '9876543211',
            }
        )
        return patient

    def _create_appointments(self, patient, doctors):
        appointments = []
        
        for i, doctor in enumerate(doctors[:5]):
            if i < 3:
                date = timezone.now().date() + timedelta(days=i+1)
                status = random.choice(['pending', 'confirmed'])
            else:
                date = timezone.now().date() - timedelta(days=i-2)
                status = 'completed'
            
            appointment, created = Appointment.objects.get_or_create(
                patient=patient,
                doctor=doctor,
                appointment_date=date,
                defaults={
                    'appointment_time': '10:00',
                    'reason': f'General checkup and consultation for {doctor.specialization.name}',
                    'status': status,
                    'fee': doctor.consultation_fee,
                }
            )
            appointments.append(appointment)
        return appointments

    def _create_invoices(self, patient, appointments):
        invoices = []
        for i, appointment in enumerate(appointments[:3]):
            status = 'paid' if i > 0 else 'unpaid'
            subtotal = appointment.fee
            tax = subtotal * Decimal('0.1')
            total = subtotal + tax
            paid = total if status == 'paid' else Decimal('0')
            
            invoice, created = Invoice.objects.get_or_create(
                appointment=appointment,
                defaults={
                    'patient': patient,
                    'subtotal': subtotal,
                    'tax_amount': tax,
                    'due_date': timezone.now().date() + timedelta(days=7),
                    'amount_paid': paid,
                    'status': 'paid' if status == 'paid' else 'unpaid',
                }
            )
            invoices.append(invoice)
        return invoices

    def _create_payments(self, patient, invoices):
        Payment.objects.get_or_create(
            invoice=invoices[1],
            defaults={
                'patient': patient,
                'amount': invoices[1].subtotal + invoices[1].tax_amount,
                'method': Payment.CARD,
                'status': Payment.SUCCESS,
                'transaction_ref': 'TXN001',
            }
        )
        Payment.objects.get_or_create(
            invoice=invoices[2],
            defaults={
                'patient': patient,
                'amount': invoices[2].subtotal + invoices[2].tax_amount,
                'method': Payment.UPI,
                'status': Payment.SUCCESS,
                'transaction_ref': 'TXN002',
            }
        )

    def _create_complaints(self, patient):
        Complaint.objects.get_or_create(
            patient=patient,
            subject='Waiting time too long',
            defaults={
                'description': 'I had to wait for more than 2 hours for my appointment.',
                'status': 'open',
                'priority': 'medium',
            }
        )
        Complaint.objects.get_or_create(
            patient=patient,
            subject='Billing issue',
            defaults={
                'description': 'There was an error in my invoice amount.',
                'status': 'resolved',
                'priority': 'low',
            }
        )
