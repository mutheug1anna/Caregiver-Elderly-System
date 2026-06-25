from django.contrib import admin
from .models import (
    Admin, Caregiver, MedicationLog, Patient, PatientCaregiver, 
    Medication, Prescription, PrescriptionSchedule, 
    Reminder, Response, Adherence, Alert
)

# Registering your custom 11-table system architecture
admin.site.register(Admin)
admin.site.register(Caregiver)
admin.site.register(Patient)
admin.site.register(PatientCaregiver)
admin.site.register(Medication)
admin.site.register(Prescription)
admin.site.register(PrescriptionSchedule)
admin.site.register(Reminder)
admin.site.register(Response)
admin.site.register(Adherence)
admin.site.register(Alert)
admin.site.register(MedicationLog)
