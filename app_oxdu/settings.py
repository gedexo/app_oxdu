from pathlib import Path

from decouple import config


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="mu2zt*8$t6pb926p443ig@-*zi*(v23csz_*7l-yo0hfqr2%8#")

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_PLUGINS = [
    "admin_interface",
    "colorfield",
    "compressor",
    "crispy_bootstrap5",
    "crispy_forms",
    "django_extensions",
    "django_filters",
    "django_tables2",
    "import_export",
    "registration",
    "tinymce",
    "easy_thumbnails",
    'simple_history',
    'mptt',
    "fcm_django",
    "rest_framework",
    "rest_framework.authtoken",
]

DJANGO_APPS = [
    "django.contrib.admin",
     'django.contrib.sites',
    "django.contrib.humanize",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    # "django.contrib.sessions",
    "user_sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
MODULES = ["employees", "admission", "core", "accounts", "accounting", "transactions", "masters", "branches"]

INSTALLED_APPS = INSTALLED_PLUGINS + DJANGO_APPS + MODULES


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # "django.contrib.sessions.middleware.SessionMiddleware",
    "user_sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'simple_history.middleware.HistoryRequestMiddleware',
    'accounts.middleware.UpdateLastSeenMiddleware',
]

ROOT_URLCONF = "app_oxdu.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.main_context",
            ]
        },
    }
]

WSGI_APPLICATION = "app_oxdu.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": config("DB_NAME", default=BASE_DIR / "db.sqlite3"),
        "USER": config("DB_USER", default=""),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": "",
    }
}


# Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
#     # {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
#     {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
#     # {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
# ]

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # other finders..
    "compressor.finders.CompressorFinder",
)


# Django Compressor Settings
COMPRESS_ENABLED = False
COMPRESS_CSS_HASHING_METHOD = "content"
COMPRESS_FILTERS = {"css": ["compressor.filters.css_default.CssAbsoluteFilter", "compressor.filters.cssmin.rCSSMinFilter"], "js": ["compressor.filters.jsmin.JSMinFilter"]}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019", "admin.E410"]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

SESSION_ENGINE = "user_sessions.backends.db"
SESSION_CACHE_ALIAS = "default"
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240
# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_L10N = True
USE_TZ = True

USE_L10N = False
DATE_INPUT_FORMATS = ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d %b %Y", "%d %b, %Y", "%d %b %Y", "%d %b, %Y", "%d %B, %Y", "%d %B %Y")
DATETIME_INPUT_FORMATS = ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M", "%d/%m/%y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
SHORT_DATETIME_FORMAT = "d/m/Y g:i A"
SHORT_DATE_FORMAT = "d/m/Y"

# Static files (CSS, JavaScript, Images)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATIC_URL = "/static/"
STATIC_FILE_ROOT = BASE_DIR / "static"
STATICFILES_DIRS = ((BASE_DIR / "static"),)
STATIC_ROOT = BASE_DIR / "assets"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_AUTO_LOGIN = True
SEND_ACTIVATION_EMAIL = False
REGISTRATION_EMAIL_SUBJECT_PREFIX = ""

REGISTRATION_OPEN = True
LOGIN_URL = "/accounts/login/"
LOGOUT_URL = "/accounts/logout/"
LOGIN_REDIRECT_URL = "/"

SITE_ID = 1
if DEBUG is False:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    COMPRESS_ENABLED = False
    X_FRAME_OPTIONS = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    HTML_MINIFY = True
    KEEP_COMMENTS_ON_MINIFYING = False


APP_SETTINGS = {
    "logo": "/static/app/config/logo.png",
    "logo_mini": "/static/app/config/logo_mini.png",
    "favicon": "/static/app/config/favicon.ico",
    "site_name": "OXDU ERP",
    "site_title": "OXDU ERP | Efficiency amplified, productivity perfected.",
    "site_description": "Efficiency amplified, productivity perfected.",
    "site_keywords": "Efficiency amplified, productivity perfected.",
    "background_image": "/static/app/config/background.jpg",
}


THUMBNAIL_ALIASES = {'': {'avatar': {'size': (50, 50), 'crop': True}}}

GRAPH_MODELS = {'all_applications': True, 'group_models': True}

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://erp.oxdu.in",
    cast=lambda v: [u.strip() for u in v.split(",")]
)

# Firebase service account path (used by firebase-admin in your project)
FIREBASE_CREDENTIAL_PATH = config(
    "FIREBASE_CREDENTIAL_PATH",
    default=str(BASE_DIR / "secrets" / "firebase-service-account.json")
)

FCM_DJANGO_SETTINGS = {
    # Path to your service account JSON (we used FIREBASE_CREDENTIAL_PATH)
    "SERVICE_ACCOUNT_PATH": FIREBASE_CREDENTIAL_PATH,

    # Keep these defaults, tweak as needed:
    "ONE_DEVICE_PER_USER": False,
    "DELETE_INACTIVE_DEVICES": True,
    "UPDATE_ON_DUPLICATE_REG_ID": True,
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp-relay.brevo.com")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=587)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=True)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", )
HR_EMAIL = config("HR_EMAIL", default=DEFAULT_FROM_EMAIL)   

#Razorpay
#Razorpay
RAZORPAY_KEY_ID = config("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = config("RAZORPAY_KEY_SECRET", default="")
RAZORPAY_WEBHOOK_SECRET = config("RAZORPAY_WEBHOOK_SECRET", default="")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    print("⚠️ WARNING: Razorpay credentials not found in environment variables!")