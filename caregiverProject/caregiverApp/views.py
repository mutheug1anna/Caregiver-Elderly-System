from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Adherence, Caregiver, Patient, Prescription, Medication, PrescriptionSchedule, MedicationLog, PatientCaregiver, Reminder, Response

# 1.login
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('home')
        
    if request.method == 'POST':
        # Retrieve form data matching the name attributes in your HTML template
        email_input = request.POST.get('email')
        password_input = request.POST.get('password')
        
        # NOTE: If you are using standard Django auth where the 'username' field 
        # treats the email as the username, pass 'email_input' to the username parameter.
        user = authenticate(request, username=email_input, password=password_input)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                messages.success(request, "Welcome Back, Admin!")
                return redirect('admin_dashboard')
            else:
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect('home')
        else:
            messages.error(request, "Invalid email credential matching or incorrect password.")
            return redirect('login')

    return render(request, 'caregiverApp/login.html')



# 2.caregiver signup
def signUp_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('fullName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, "This email address is already registered.")
            return redirect('signup')
            
        # Creates the regular caregiver user account safely in db
        User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )
        Caregiver.objects.get_or_create(
            email=email,
            defaults={
                'fullName': name,
                'phoneNumber': '', 
                'passwordHash': '',  
            }
        )
        
        
        
        
        messages.success(request, f"Account created successfully for {name}! Please enter your credentials below to log in.")
        return redirect('login')
        
    return render(request, 'caregiverApp/signUp.html')

# 3. logout
def logout_view(request):
    logout(request)
    return redirect('login')


#caregiver protal
@login_required
def home_view(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        #partients action-
        if action == 'create_patient':
            name = request.POST.get('fullName', '').strip()
            phone = request.POST.get('phoneNumber', '').strip()
            dob = request.POST.get('dateOfBirth', '1960-01-01')
            
            if name and phone:
                patient= Patient.objects.create(
                    fullName=name, 
                    phoneNumber=phone, 
                    dateOfBirth=dob, 
                    caregiverID=request.user
                )
                
                caregiver = Caregiver.objects.filter(email=request.user.email).first()
                if caregiver:
                    PatientCaregiver.objects.get_or_create(
                        patientID= patient,
                        caregiverID=caregiver,
                        defaults={'assignmentStatus': 'Active', 'startDate': timezone.localdate()}
                    )
            return redirect('home')
            
        elif action == 'edit_patient':
            p_id = request.POST.get('patientID')
            patient = get_object_or_404(Patient, patientID=p_id, caregiverID=request.user)
            patient.fullName = request.POST.get('fullName', patient.fullName).strip()
            patient.phoneNumber = request.POST.get('phoneNumber', patient.phoneNumber).strip()
            patient.dateOfBirth = request.POST.get('dateOfBirth', patient.dateOfBirth)
            patient.save()
            return redirect('home')
            
        elif action == 'delete_patient':
            p_id = request.POST.get('patientID')
            Patient.objects.filter(patientID=p_id, caregiverID=request.user).delete()
            return redirect('home')
            
        # medication
        elif action == 'create_medication':
            name = request.POST.get('medicationName', '').strip()
            color = request.POST.get('colorBoxCode', '').strip()
            if name and color:
                Medication.objects.create(medicationName=name, colorBoxCode=color)
            else:
                messages.error(request, "Both Medication Name and Color Box Code are required!")
            return redirect('home')
            
        elif action == 'edit_medication':
            med_id = request.POST.get('medicationID')
            med = get_object_or_404(Medication, medicationID=med_id)
            med.medicationName = request.POST.get('medicationName', med.medicationName).strip()
            med.colorBoxCode = request.POST.get('colorBoxCode', med.colorBoxCode).strip()
            med.save()
            return redirect('home')
            
        elif action == 'delete_medication':
            med_id = request.POST.get('medicationID')
            Medication.objects.filter(medicationID=med_id).delete()
            return redirect('home')

    context = {
        'patients': Patient.objects.filter(caregiverID=request.user).order_by('fullName'),
        'meds': Medication.objects.all().order_by('medicationName')
    }
    return render(request, 'caregiverApp/home.html', context)




def logout_view(request):
    logout(request)
    return redirect('login')

# schedule
@login_required
def schedule_view(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Ccreate
        if action == 'create_tx':
            patient_id = request.POST.get('patient')
            med_id = request.POST.get('medication')
            dosage = request.POST.get('dosage', '').strip()
            form_time = request.POST.get('scheduled_time')
            
            if patient_id and med_id and dosage and form_time:
                patient = get_object_or_404(Patient, patientID=patient_id, caregiverID=request.user)
                medication = get_object_or_404(Medication, medicationID=med_id)
                
                tx = Prescription.objects.create(
                    patientID=patient,
                    medicationID=medication,
                    dosage=dosage,
                    status='Scheduled'
                )
                PrescriptionSchedule.objects.create(
                    prescriptionID=tx,
                    scheduledTime=form_time
                )
            return redirect('schedule')
            
        # edit
        elif action == 'edit_reminder':
            schedule_id = request.POST.get('schedule_id')
            patient_id = request.POST.get('patient')
            med_id = request.POST.get('medication')
            dosage = request.POST.get('dosage', '').strip()
            form_time = request.POST.get('scheduled_time')
            
            slot = get_object_or_404(PrescriptionSchedule, scheduleID=schedule_id, prescriptionID__patientID__caregiverID=request.user)
            
            # 1. Update Time
            slot.scheduledTime = form_time
            slot.save()
            
            # 2. Update Prescription Data (Patient, Medication, Dosage)
            prescription = slot.prescriptionID
            prescription.patientID_id = patient_id
            prescription.medicationID_id = med_id
            prescription.dosage = dosage
            prescription.save()
                
            return redirect('schedule')

        # MARK REMINDER AS TAKEN
        elif action == 'mark_taken':
            schedule_id = request.POST.get('schedule_id')
            slot = get_object_or_404(PrescriptionSchedule, scheduleID=schedule_id, prescriptionID__patientID__caregiverID=request.user)
            
            today = timezone.localdate()
            log, created = MedicationLog.objects.get_or_create(scheduleID=slot, logDate=today)
            log.medStatus = 'Taken'
            log.takenAt = timezone.now()
            log.save()
            return redirect('schedule')
            
        # delete
        elif action == 'delete_tx':
            tx_id = request.POST.get('tx_id')
            Prescription.objects.filter(prescriptionID=tx_id, patientID__caregiverID=request.user).delete()
            return redirect('schedule')

    schedules = PrescriptionSchedule.objects.filter(
        prescriptionID__patientID__caregiverID=request.user
    ).select_related('prescriptionID__patientID', 'prescriptionID__medicationID')
    
    today = timezone.localdate()
    
    for slot in schedules:
        MedicationLog.objects.get_or_create(scheduleID=slot, logDate=today)

    context = {
        'patients': Patient.objects.filter(caregiverID=request.user).order_by('fullName'),
        'meds': Medication.objects.all().order_by('medicationName'),
        'schedules': schedules,
        'today': today
    }
    return render(request, 'caregiverApp/schedule.html', context)


# adherence
@login_required
def adherence_view(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    today = timezone.localdate()
    
    logs = MedicationLog.objects.select_related(
        'scheduleID__prescriptionID__patientID', 
        'scheduleID__prescriptionID__medicationID'
    ).filter(logDate=today, scheduleID__prescriptionID__patientID__caregiverID=request.user)
    
    # Create a set of patient IDs who actually have logs today
    patients_with_logs = {log.scheduleID.prescriptionID.patientID.patientID for log in logs}
    
    context = {
        'patients': Patient.objects.filter(caregiverID=request.user).order_by('fullName'),
        'logs': logs,
        'patients_with_logs': patients_with_logs,
        'today': today
    }
    return render(request, 'caregiverApp/adherence.html', context)


# admin dash
@login_required
def admin_dashboard_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied. Only the Superuser can access this dashboard.")
        return redirect('home')
 
    if request.method == 'POST':
        action = request.POST.get('action')
 
        if action == 'admin_update_caregiver':
            user_id = request.POST.get('caregiver_id')
            name = request.POST.get('caregiverName')
            email = request.POST.get('caregiverEmail')
            user_profile = get_object_or_404(User, id=user_id)
            user_profile.first_name = name
            user_profile.email = email
            user_profile.username = email
            user_profile.save()
            messages.success(request, "Caregiver record updated.")
            return redirect('admin_dashboard')
 
        elif action == 'admin_delete_caregiver':
            user_id = request.POST.get('caregiver_id')
            User.objects.filter(id=user_id).delete()
            messages.success(request, "Caregiver record removed from system database.")
            return redirect('admin_dashboard')
 
        elif action == 'admin_update_patient':
            patient_id = request.POST.get('patient_id')
            name = request.POST.get('patientName')
            phone = request.POST.get('patientPhone')
            patient = get_object_or_404(Patient, patientID=patient_id)
            patient.fullName = name
            patient.phoneNumber = phone
            patient.save()
            messages.success(request, f"Patient profile for {name} saved.")
            return redirect('admin_dashboard')
 
        elif action == 'admin_delete_patient':
            patient_id = request.POST.get('patient_id')
            Patient.objects.filter(patientID=patient_id).delete()
            messages.success(request, "Patient profile removed securely.")
            return redirect('admin_dashboard')
 
    today = timezone.localdate()
 
    # --- REPORT DATA ---
 
    # Total system counts
    total_caregivers = User.objects.filter(is_superuser=False).count()
    total_patients = Patient.objects.count()
    total_medications = Medication.objects.count()
    total_prescriptions = Prescription.objects.count()
 
    # Today's adherence summary
    todays_logs = MedicationLog.objects.filter(logDate=today)
    total_taken_today = todays_logs.filter(medStatus='Taken').count()
    total_missed_today = todays_logs.filter(medStatus='Missed').count()
    total_pending_today = todays_logs.filter(medStatus='Pending').count()
 
    # Active caregivers — those who have at least one patient assigned
    active_caregivers = User.objects.filter(
        is_superuser=False,
        patients__isnull=False
    ).distinct()
 
    # Inactive caregivers — those with no patients assigned
    inactive_caregivers = User.objects.filter(
        is_superuser=False,
        patients__isnull=True
    ).distinct()
 
    # Patient medication adherence report — all logs with details
    adherence_report = MedicationLog.objects.select_related(
        'scheduleID__prescriptionID__patientID',
        'scheduleID__prescriptionID__medicationID',
        'scheduleID__prescriptionID__patientID__caregiverID'
    ).order_by('-logDate', 'scheduleID__prescriptionID__patientID__fullName')[:50]
 
    context = {
        'caregivers': User.objects.filter(is_superuser=False).order_by('-date_joined'),
        'patients': Patient.objects.all().order_by('fullName'),
        'today': today,
 
        # Report stats
        'total_caregivers': total_caregivers,
        'total_patients': total_patients,
        'total_medications': total_medications,
        'total_prescriptions': total_prescriptions,
        'total_taken_today': total_taken_today,
        'total_missed_today': total_missed_today,
        'total_pending_today': total_pending_today,
        'active_caregivers': active_caregivers,
        'inactive_caregivers': inactive_caregivers,
        'adherence_report': adherence_report,
    }
    return render(request, 'caregiverApp/admin_dashboard.html', context)
 
 



@csrf_exempt
def africas_talking_webhook(request):
    """
    Listens for incoming SMS replies from Africa's Talking Simulator.
    If a patient replies '1', it marks their active daily log as 'Taken'.
    """
    if request.method == 'POST':
        # Africa's Talking sends webhooks as application/x-www-form-urlencoded data
        sender = request.POST.get('from')  # Patient's phone number (+254...)
        message_text = request.POST.get('text', '').strip() # The text reply (e.g., '1')
        
        print(f"📩 Incoming SMS received from {sender}: Text = '{message_text}'")

        if message_text == '1':
            today = timezone.localdate()
            
            # Find the patient matching this specific phone number
            patient = Patient.objects.filter(phoneNumber=sender).first()
            
            if patient:
         
                active_logs = MedicationLog.objects.filter(
                scheduleID__prescriptionID__patientID=patient,
                logDate=today,
                medStatus__in=['Pending', 'Scheduled']
)

            for log in active_logs:
                log.medStatus = 'Taken'
                log.takenAt = timezone.now()
                log.save()
                
                reminder,_= Reminder.objects.get_or_create(
                    scheduleID=log.scheduleID,
                    sentTime__date=today,
                    defaults={'sentTime': timezone.now(), 'deliveryStatus': 'Delivered'}
                )
                response_record, created = Response.objects.get_or_create(
                    reminderID= reminder,
                    defaults={
                        'patientReply': '1',
                        'responseTime': timezone.now()
                    }
                )
                if created: Adherence.objects.get_or_create(
                    responseID=response_record,
                    defaults={
                        'adherenceStatus': 'Taken',
                        'recordedTime': timezone.now()
                    }
                )
                    
                
                
                
                
                
                
                print(f"🔔 ALERT: {patient.fullName} confirmed medication taken. Dashboard updated!")
            return HttpResponse("Status updated successfully", status=200)
            
    return HttpResponse("Invalid request format", status=400)