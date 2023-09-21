import os


## get env variable for container

# set default
if os.environ.get("APP_SECRET_KEY") == None:
    os.environ["APP_SECRET_KEY"] = "sdfsfFKLJodsg082343223_"

if os.environ.get("APP_FILE_SIZE_ALLOW") == None:
    os.environ["APP_FILE_SIZE_ALLOW"] = str(10240*1024)

if os.environ.get("APP_USER") == None:
    os.environ["APP_USER"] = "dongvt"

if os.environ.get("APP_PASS") == None:
    os.environ["APP_PASS"] = "dongvt"


if os.environ.get("APP_DATABASE_NAME") == None:
    os.environ["APP_DATABASE_NAME"] = "file_upload"

if os.environ.get("APP_DATABASE_USER") == None:
    os.environ["APP_DATABASE_USER"] = "root"

if os.environ.get("APP_DATABASE_PASS") == None:
    os.environ["APP_DATABASE_PASS"] = ""

if os.environ.get("APP_DATABASE_HOST") == None:
    os.environ["APP_DATABASE_HOST"] = "127.0.0.1"

if os.environ.get("APP_DATABASE_PORT") == None:
    os.environ["APP_DATABASE_PORT"] = "3306"
###

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SECRET_KEY = str(os.environ.get("APP_SECRET_KEY"))

DEBUG = True
ALLOWED_HOSTS = ["*"]

RESOURCE_UPLOAD = BASE_DIR + "/resource_upload/"

# Application definition


# handler upload file ==
FILE_TYPE_ALLOW = {
    "png": "image/png",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "pdf": "application/pdf",
    "txt": "text/plain",
    "csv": "text/plain",
    "abc": "application/octet-stream"
}

# FILE_SIZE = 1024*1024 # 1 MB
FILE_SIZE = int(os.environ.get("APP_FILE_SIZE_ALLOW"))

FILE_RESOURCE_UPLOAD = BASE_DIR + "/resource_upload/"

USER = {
    "USERNAME": str(os.environ.get("APP_USER")),
    "PASSWD": str(os.environ.get("APP_PASS"))
}
# ======================

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True
