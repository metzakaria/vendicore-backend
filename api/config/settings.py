
from pathlib import Path
import os 
import datetime
from datetime import timedelta
from celery.schedules import crontab
from dotenv import load_dotenv
# Load variables from the .env file
load_dotenv()



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY") 

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG") 

ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True
#CORS_ALLOWED_ORIGINS = ['http://*', 'https://*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #thirdpary
    'rest_framework',
    #'rest_framework.authtoken',
    #'rest_framework_simplejwt',
    #custom apps
    'apps.merchant',
    'apps.product',
    'apps.provider',
    'apps.seeder',  # Seeder app for management commands
    'corsheaders',
]

AUTH_USER_MODEL = 'merchant.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'config.helper.CustomAuthentication',
        #'config.helper.CustomAuthenticationVending',
        #'rest_framework.authentication.SessionAuthentication',
        #'rest_framework.simplejwt.authentication.JWTAuthentication',
    ],
    
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
         'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,  # Set the number of items per page
    'EXCEPTION_HANDLER': 'config.helper.custom_exception_handler',
    #'APPEND_SLASH': False
}

SIMPLE_JWT = {
    #'JWT_EXPIRATION_DELTA': datetime.timedelta(hours=1),
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(minutes=5),
    "BLACKLIST_AFTER_ROTATION": True,
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    #'config.helper.CustomCorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# settings.py
#CELERYD_HIJACK_ROOT_LOGGER= False,
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(module)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        #'file': {
        #    'class': 'logging.FileHandler',
        #    #'filename': os.environ.get('LOG_FILE_PATH'),
        #    'filename': 'logs/api.log',
        #    'formatter': 'verbose',
        #},
       # 'celery': {
       #     'class': 'logging.FileHandler',
       #     'filename': 'debug2.log',
       #     'formatter': 'verbose',
       #},
    },
    
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    
}


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get("DATABASE_ENGINE"),
        'NAME': os.environ.get("DATABASE_NAME"),
        'USER': os.environ.get("DATABASE_USER"),
        'PASSWORD': os.environ.get("DATABASE_PASS"),
        'HOST': os.environ.get("DATABASE_HOST"), 
        'PORT': os.environ.get("DATABASE_PORT"),  
        
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

#TIME_ZONE = 'UTC'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#=============== CELERY ==================#
CELERY_RESULT_BACKEND = os.environ.get('CELERY_BROKER_URL')
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
#CELERYD_HIJACK_ROOT_LOGGER = False

redbeat_redis_url = os.getenv("CELERY_BROKER_URL")
beat_scheduler = "redbeat.RedBeatScheduler"


CELERY_BEAT_SCHEDULE = {
    "reverse-timeout-transactions-every-minute": {
        "task": "apps.product.task.cron_reverse_timeout_unreversed_transaction",
        "schedule": crontab(minute="*/7"),  # every 1 minute
    },
}

#=============== CACHE CONFIGURATION ==================#
# Configure cache for multi-instance deployment
# Uses Redis for production, falls back to local memory cache for development

# Check if Redis URL is provided (production)
REDIS_URL = os.environ.get('REDIS_URL')

if REDIS_URL:
    # Production: Use Redis for distributed caching across multiple instances
    # Requires: pip install django-redis
    try:
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': REDIS_URL,
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'SOCKET_CONNECT_TIMEOUT': 5,
                    'SOCKET_TIMEOUT': 5,
                    'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                    'IGNORE_EXCEPTIONS': True,  # Don't fail if Redis is down
                    #'PARSER_CLASS': 'redis.connection.HiredisParser',  # Faster parsing (optional)
                },
                'KEY_PREFIX': 'vendicore_vas',
                'TIMEOUT': 300,  # 5 minutes default
            }
        }
    except ImportError:
        # Fallback to standard Redis backend if django-redis not installed
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                'LOCATION': REDIS_URL,
                'KEY_PREFIX': 'vendicore_vas',
                'TIMEOUT': 300,
            }
        }
else:
    # Development: Use local memory cache (single instance only)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 300,  # 5 minutes
            'OPTIONS': {
                'MAX_ENTRIES': 10000  # Increased for better performance
            }
        }
    }
