# 🏥 MediCare — Hospital Management System


A full-featured Django web application for hospital management covering patients, doctors, appointments, medical history, insurance, and billing.
<img width="3010" height="1690" alt="image" src="https://github.com/user-attachments/assets/ba1dbadd-a967-4cb7-9ac6-8bf40f08b812" />
<img width="2912" height="1682" alt="image" src="https://github.com/user-attachments/assets/003663c2-2ae1-4a8a-8d78-37fa1ff8adb7" />
<img width="2942" height="1650" alt="image" src="https://github.com/user-attachments/assets/1d442325-5662-4ebb-a1ce-8bd46c55279f" />


---

## 🚀 Quick Start

### 1. Create & Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Migrations
```bash
python manage.py makemigrations core
python manage.py migrate
```

### 4. Seed Sample Data
```bash
python manage.py seed_data
```

### 5. Run the Server
```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000**

---

## 🔑 Default Credentials

| Role    | Username   | Password    | URL            |
|---------|-----------|-------------|----------------|
| Admin   | admin      | admin123    | /admin/        |
| Patient | patient1   | patient123  | /dashboard/    |
| Doctor  | drpriya    | doctor123   | /dashboard/    |

---

## 📁 Project Structure

```
hospital_project/
├── manage.py
├── requirements.txt
├── hospital_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/
│   ├── models.py          ← All data models
│   ├── views.py           ← All views
│   ├── urls.py            ← URL patterns
│   ├── forms.py           ← Django forms
│   ├── admin.py           ← Admin configuration
│   └── management/
│       └── commands/
│           └── seed_data.py
├── templates/
│   ├── base.html
│   ├── core/
│   │   ├── home.html
│   │   ├── dashboard.html
│   │   ├── doctor_list.html
│   │   ├── doctor_detail.html
│   │   ├── patient_profile.html
│   │   ├── patient_form.html
│   │   ├── patient_history.html
│   │   ├── medical_record_detail.html
│   │   ├── appointment_list.html
│   │   ├── appointment_form.html
│   │   ├── appointment_detail.html
│   │   ├── insurance_list.html
│   │   ├── insurance_form.html
│   │   ├── insurance_policy_detail.html
│   │   ├── insurance_claim_form.html
│   │   ├── invoice_list.html
│   │   └── invoice_detail.html
│   └── registration/
│       ├── login.html
│       └── register.html
└── static/
    └── css/
```

---

## 🗺️ URL Map

| URL | View | Description |
|-----|------|-------------|
| `/` | home | Landing page |
| `/register/` | register | Patient registration |
| `/login/` | login | Login |
| `/dashboard/` | dashboard | Patient dashboard |
| `/doctors/` | doctor_list | Browse doctors |
| `/doctors/<pk>/` | doctor_detail | Doctor profile |
| `/appointments/` | appointment_list | All appointments |
| `/appointments/book/` | appointment_book | Book appointment |
| `/appointments/<pk>/` | appointment_detail | Appointment detail |
| `/history/` | patient_history | Medical records & vitals |
| `/history/<pk>/` | medical_record_detail | Single record |
| `/insurance/` | insurance_list | Policies & claims |
| `/insurance/add/` | insurance_policy_add | Add policy |
| `/insurance/<pk>/` | insurance_policy_detail | Policy detail |
| `/insurance/claim/add/` | insurance_claim_add | File a claim |
| `/invoices/` | invoice_list | All invoices |
| `/invoices/<pk>/` | invoice_detail | Invoice + print |
| `/admin/` | Django Admin | Full admin panel |

---

## 📊 Models

### Core Models
- **Specialization** — Medical specializations (Cardiology, Neurology, etc.)
- **Doctor** — Doctor profile linked to User
- **DoctorReview** — Patient reviews for doctors
- **Patient** — Patient profile linked to User
- **Appointment** — Consultation bookings
- **MedicalRecord** — Diagnosis, treatment, prescriptions
- **Vitals** — Blood pressure, weight, pulse, temperature, etc.
- **InsuranceProvider** — Insurance companies
- **InsurancePolicy** — Patient insurance policies
- **InsuranceClaim** — Claims against policies
- **Invoice** — Billing records

---

## 🔧 Tech Stack

- **Backend:** Django 4.2+
- **Database:** SQLite (dev) / PostgreSQL (production)
- **Frontend:** Pure CSS + HTML (no frameworks — fast loading)
- **Icons:** Font Awesome 6
- **Fonts:** DM Sans + Playfair Display (Google Fonts)
