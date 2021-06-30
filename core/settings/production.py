from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool)
ALLOWED_HOSTS = ['*']


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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('NAME'),
        'USER': config('USER'),
        'PASSWORD': config('PASSWORD'),
        'HOST': config('HOST'),
        'PORT': config('PORT')
    }
}

STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')


AWS_ACCESS_KEY_ID=config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY=config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME=config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN=config('AWS_S3_CUSTOM_DOMAIN')
AWS_S3_OBJECT_PARAMETERS={"CacheControl":"max-age=86400"}
AWS_DEFAULT_ACL=config('AWS_DEFAULT_ACL')
AWS_LOCATION=config('AWS_LOCATION')
STATICFILES_STORAGE="storages.backends.s3boto3.S3Boto3Storage"
STATIC_URL = 'https://%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

import dj_database_url 
prod_db  =  dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(prod_db)