import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caregiverProject.settings')
django.setup()

from caregiverApp.models import PrescriptionSchedule

print("⚡ --- DJANGO DATABASE DIAGNOSTIC --- ⚡")
now = datetime.now()
current_time_str = now.strftime('%H:%M')
print(f"Current System Clock: {current_time_str}")

schedules = PrescriptionSchedule.objects.all()
print(f"Total rows found in database: {schedules.count()}")

for s in schedules:
    # This prints out exactly what text style your database uses
    print(f"ID: {s.scheduleID} | Raw Time in DB: '{s.scheduledTime}' | Type: {type(s.scheduledTime)}")