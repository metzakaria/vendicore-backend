import os
import logging
from celery import Celery
from celery.signals import setup_logging  # noqa
from . import settings

# set the default Django settings module for the 'celery' program.
# this is also used in manage.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
app = Celery('config')

app.add_defaults({
    'CELERYD_HIJACK_ROOT_LOGGER': False,
})
app.config_from_object('django.conf:settings', namespace='CELERY')

@setup_logging.connect
def setup_celery_logging(**kwargs):  
    return logging.getLogger('celery') 

#@setup_logging.connect
#def config_loggers(*args, **kwargs):
#    from logging.config import dictConfig  # noqa
#    from django.conf import settings  # noqa

#    dictConfig(settings.LOGGING)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()



