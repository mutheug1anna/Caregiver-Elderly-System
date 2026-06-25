import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caregiverProject.settings')

app = Celery('caregiverProject')

# Read configuration from Django settings using the 'CELERY_' prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically look for a tasks.py file inside all registered installed apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')