"""
API Gateway Settings
Port: 18000 (Docker) / 8000 (local dev)
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', 'gateway-dev-secret-key-2024')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'api_gateway.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'api_gateway.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'bookstore_micro_gateway'),
        'USER': os.environ.get('DB_USER', 'bookstore_admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', '123456'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24h

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'BookStore API Gateway',
    'DESCRIPTION': 'Cổng API duy nhất cho BookStore Microservices (BFF). Swagger tổng hợp tất cả các service nội bộ.',
    'VERSION': '1.0.0',
    'SWAGGER_UI_SETTINGS': {
        'urls': [
            {'url': '/api/schema/', 'name': 'API Gateway (Routes Server)'},
            {'url': 'http://localhost:18001/api/schema/', 'name': 'Customer Service'},
            {'url': 'http://localhost:18002/api/schema/', 'name': 'Book Service'},
            {'url': 'http://localhost:18003/api/schema/', 'name': 'Cart Service'},
            {'url': 'http://localhost:18004/api/schema/', 'name': 'Order Service'},
            {'url': 'http://localhost:18005/api/schema/', 'name': 'Pay Service'},
            {'url': 'http://localhost:18006/api/schema/', 'name': 'Ship Service'},
            {'url': 'http://localhost:18007/api/schema/', 'name': 'Comment Service'},
            {'url': 'http://localhost:18008/api/schema/', 'name': 'Catalog Service'},
            {'url': 'http://localhost:18010/api/schema/', 'name': 'Manager Service'},
        ],
        'layout': 'StandaloneLayout', # <--- BAT BUOC DE HIEN THI TOPBAR DROPDOWN!
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
    },
}
