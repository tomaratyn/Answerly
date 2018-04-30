from config.common_settings import *

DEBUG = True

SECRET_KEY = 'some secret'

DATABASES['default']['NAME'] = 'answerly'
DATABASES['default']['USER'] = 'answerly'
DATABASES['default']['PASSWORD'] = 'development'
DATABASES['default']['PORT'] = 5432
DATABASES['default']['HOST'] = 'localhost'

ES_INDEX = 'answerly'
ES_HOST = 'localhost'
ES_PORT = '9200'

TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'django.template.context_processors.debug',
]

CHROMEDRIVER = os.path.join(BASE_DIR, '../chromedriver/chromedriver')
