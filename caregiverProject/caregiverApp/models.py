from django.db import models
from django.contrib.auth.models import User


# 1. Admin Table
class Admin(models.Model):
    adminID = models.AutoField(primary_key=True)
    fullName = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    passwordHash = models.CharField(max_length=255)

    def __str__(self):
        return self.fullName

# 2. Caregiver Table
class Caregiver(models.Model):
    caregiverID = models.AutoField(primary_key=True)
    fullName = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    phoneNumber = models.CharField(max_length=15)
    passwordHash = models.CharField(max_length=255)

    def __str__(self):
        return self.fullName

# 3. Patient Table
class Patient(models.Model):
    patientID = models.AutoField(primary_key=True)
    fullName = models.CharField(max_length=100)
    dateOfBirth = models.DateField()
    phoneNumber = models.CharField(max_length=15)
    caregiverID = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patients', db_column='caregiverID')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.fullName


# 4. Patient-Caregiver Bridge Table
class PatientCaregiver(models.Model):
    patientCaregiverID = models.AutoField(primary_key=True)
    patientID = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patientID')
    caregiverID = models.ForeignKey(Caregiver, on_delete=models.CASCADE, db_column='caregiverID')
    assignmentStatus = models.CharField(max_length=20)
    startDate = models.DateField()
    endDate = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Link: {self.caregiverID.fullName} -> {self.patientID.fullName}"

# 5. Medication Entity Table
class Medication(models.Model):
    medicationID = models.AutoField(primary_key=True)
    medicationName = models.CharField(max_length=100)
    colorBoxCode = models.CharField(max_length=30)

    def __str__(self):
        return self.medicationName

# 6. Prescription Header Table
class Prescription(models.Model):
    prescriptionID = models.AutoField(primary_key=True)
    patientID = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patientID')
    medicationID = models.ForeignKey(Medication, on_delete=models.CASCADE, db_column='medicationID')
    dosage = models.CharField(max_length=30)
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"Rx {self.prescriptionID} for {self.patientID.fullName}"

# 7. Prescription Schedule Table
class PrescriptionSchedule(models.Model):
    scheduleID = models.AutoField(primary_key=True)
    prescriptionID = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='time_slots')
    scheduledTime = models.TimeField()

    def __str__(self):
        return f"{self.prescriptionID.patientID.fullName} - {self.scheduledTime}"

# 8. Reminder Logs Table
class Reminder(models.Model):
    reminderID = models.AutoField(primary_key=True)
    scheduleID = models.ForeignKey(PrescriptionSchedule, on_delete=models.CASCADE, db_column='scheduleID')
    sentTime = models.DateTimeField()
    deliveryStatus = models.CharField(max_length=20)

    def __str__(self):
        return f"Reminder {self.reminderID} - Status: {self.deliveryStatus}"

# 9. Response Tracking Table
class Response(models.Model):
    responseID = models.AutoField(primary_key=True)
    reminderID = models.ForeignKey(Reminder, on_delete=models.CASCADE, db_column='reminderID')
    patientReply = models.CharField(max_length=10)
    responseTime = models.DateTimeField()

    def __str__(self):
        return f"Response {self.responseID} (Reply: {self.patientReply})"

# 10. Adherence Status Matrix Table
class Adherence(models.Model):
    adherenceID = models.AutoField(primary_key=True)
    responseID = models.ForeignKey(Response, on_delete=models.CASCADE, db_column='responseID')
    adherenceStatus = models.CharField(max_length=20)
    recordedTime = models.DateTimeField()

    def __str__(self):
        return f"Adherence Record {self.adherenceID}: {self.adherenceStatus}"

# 11. Alert Pushes Table
class Alert(models.Model):
    alertID = models.AutoField(primary_key=True)
    caregiverID = models.ForeignKey(Caregiver, on_delete=models.CASCADE, db_column='caregiverID')
    adherenceID = models.ForeignKey(Adherence, on_delete=models.CASCADE, db_column='adherenceID')
    alertType = models.CharField(max_length=30)
    alertTime = models.DateTimeField()
    alertStatus = models.CharField(max_length=20)

    def __str__(self):
        return f"Alert {self.alertID} for Caregiver {self.caregiverID.fullName}"

#Medication Log table
class MedicationLog(models.Model):
    logID = models.AutoField(primary_key=True)
    scheduleID = models.ForeignKey(PrescriptionSchedule, on_delete=models.CASCADE, related_name='daily_logs', db_column='scheduleID')
    logDate = models.DateField(auto_now_add=True)
    medStatus = models.CharField(max_length=20, default='Pending')  # e.g., Taken, Missed, Pending
    takenAt = models.DateTimeField(null=True, blank=True)  # Timestamp when medication was taken
    
    def __str__(self):
        return f"{self.scheduleID.prescriptionID.patientID.fullName} - {self.medStatus} ({self.logDate})"