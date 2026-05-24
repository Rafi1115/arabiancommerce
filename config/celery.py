import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'process-scheduled-notifications-every-minute': {
        'task': 'apps.notifications.tasks.process_scheduled_notifications',
        'schedule': crontab(minute='*'),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')