import os
import django
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cp_verse.settings")
django.setup()

# Run migrations automatically on startup (if not already applied)
# WARNING: This is a temporary workaround.
try:
    call_command('migrate', interactive=False)
except Exception as e:
    # Log the error rather than crashing the application
    import logging
    logger = logging.getLogger("django")
    logger.error("Error during automatic migrations: %s", e)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
