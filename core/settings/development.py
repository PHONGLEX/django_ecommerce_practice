from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/


ALLOWED_HOSTS = []


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('NAME'),
        'USER': config('USER'),
        'PASSWORD': config('PASSWORD'),
        'HOST': config('HOST'),
    }
}

STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
