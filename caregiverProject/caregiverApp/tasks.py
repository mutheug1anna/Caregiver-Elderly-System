import httpx
import certifi
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import PrescriptionSchedule, MedicationLog, Reminder, Response, Adherence


@shared_task
def send_medication_reminders():
    now = timezone.localtime(timezone.now())
    current_time_str = now.strftime('%H:%M')
    today = now.date()

    print(f"⏰ [CELERY CLOCK] Running search for time matching -> {current_time_str}")

    all_schedules = PrescriptionSchedule.objects.select_related(
        'prescriptionID__patientID',
        'prescriptionID__medicationID'
    ).all()

    due_schedules = [
        slot for slot in all_schedules
        if slot.scheduledTime.strftime('%H:%M') == current_time_str
    ]

    print(f"🎯 Total records found matching this exact minute: {len(due_schedules)}")

    for slot in due_schedules:
        patient = slot.prescriptionID.patientID
        medication = slot.prescriptionID.medicationID
        dosage = slot.prescriptionID.dosage

        message = (
            f"Hello {patient.fullName}, it is time to take {dosage} of "
            f"{medication.colorBoxCode}. Reply 1 to confirm you have taken it."
        )

        print(f"📱 Dispatching SMS to: {patient.phoneNumber}")

        try:
            with httpx.Client(verify=certifi.where(), timeout=15.0) as client:
                response = client.post(
                    'https://api.sandbox.africastalking.com/version1/messaging',
                    headers={
                        'apiKey': settings.AT_API_KEY,
                        'Accept': 'application/json',
                    },
                    data={
                        'username': settings.AT_USERNAME,
                        'to': patient.phoneNumber,
                        'message': message,
                    }
                )

            print(f"📡 AT Response Code: {response.status_code}")
            print(f"📡 AT Response Body: {response.text}")

            if response.status_code == 201:
                print(f"✅ SMS successfully sent to {patient.fullName}!")
                
                Reminder.objects.get_or_create(
                    scheduleID=slot,
                    sentTime__date=today,
                    defaults={'sentTime': now, 'deliveryStatus': 'Delivered'}
                )

            # Create the medication log as Pending when SMS is first sent
            MedicationLog.objects.get_or_create(
                scheduleID=slot,
                logDate=today,
                defaults={'medStatus': 'Pending'}
            )

        except Exception as e:
            print(f"❌ ERROR sending SMS: {str(e)}")
            Reminder.objects.get_or_create(
                scheduleID=slot,
                sentTime__date=today,
                defaults={
                    'sentTime': now,
                    'deliveryStatus': 'Failed',
                }
            )


@shared_task
def check_for_missed_medications():
    """
    Runs every minute via Celery Beat.
    Checks if any medication log is still Pending 10 minutes after its scheduled time.
    If so, sends a follow-up reminder SMS to the patient.
    """
    now = timezone.localtime(timezone.now())
    today = now.date()

    # Calculate what time it was 5 minutes ago
    five_minutes_ago = now - timedelta(minutes=5)
    five_minutes_ago_str = five_minutes_ago.strftime('%H:%M')

    print(f"🔍 [MISSED CHECK] Checking for pending medications scheduled at -> {five_minutes_ago_str}")

    # Get all logs for today that are still Pending
    pending_logs = MedicationLog.objects.filter(
        logDate=today,
        medStatus='Pending'
    ).select_related(
        'scheduleID__prescriptionID__patientID',
        'scheduleID__prescriptionID__medicationID'
    )

    # Filter in Python — find logs whose scheduled time matches exactly 10 minutes ago
    missed_logs = [
        log for log in pending_logs
        if log.scheduleID.scheduledTime.strftime('%H:%M') == five_minutes_ago_str
    ]

    print(f"⚠️ Total missed/pending found: {len(missed_logs)}")

    for log in missed_logs:
        patient = log.scheduleID.prescriptionID.patientID
        medication = log.scheduleID.prescriptionID.medicationID
        dosage = log.scheduleID.prescriptionID.dosage

        # Update status to Missed in the database
        log.medStatus = 'Missed'
        log.save()

        print(f"🔴 MISSED: {patient.fullName} has not confirmed medication after 5 minutes.")

        # Send a follow-up reminder SMS
        retry_message = (
            f"⚠️ Reminder:   Hello {patient.fullName}, you have not confirmed taking "
            f"{dosage} of {medication.colorBoxCode}. "
            f"Please take it now and reply 1 to confirm."
        )

        print(f"📱 Sending retry SMS to: {patient.phoneNumber}")

        try:
            with httpx.Client(verify=certifi.where(), timeout=15.0) as client:
                response = client.post(
                    'https://api.sandbox.africastalking.com/version1/messaging',
                    headers={
                        'apiKey': settings.AT_API_KEY,
                        'Accept': 'application/json',
                    },
                    data={
                        'username': settings.AT_USERNAME,
                        'to': patient.phoneNumber,
                        'message': retry_message,
                    }
                )

            print(f"📡 Retry SMS Response Code: {response.status_code}")

            if response.status_code == 201:
                print(f"✅ Retry SMS successfully sent to {patient.fullName}!")
                
                Reminder.objects.create(
                    scheduleID = log.scheduleID,
                    sentTime = now,
                    deliveryStatus = 'Retry Sent'
                
                )

        except Exception as e:
            print(f"❌ ERROR sending retry SMS: {str(e)}")