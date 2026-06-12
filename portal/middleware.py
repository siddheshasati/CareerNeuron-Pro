from django.db import DatabaseError, OperationalError
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


class DatabaseErrorCatchMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, (OperationalError, DatabaseError)):
            message = str(exception)
            if "no such table" in message or "auth_user" in message or "relation" in message or "does not exist" in message:
                try:
                    logger.info("Database table missing. Attempting automatic migration...")
                    call_command("migrate", interactive=False)
                    logger.info("Automatic migration completed successfully. Redirecting to retry request.")
                    # Re-run migration and redirect to the same page
                    return HttpResponseRedirect(request.get_full_path())
                except Exception as migrate_err:
                    logger.error(f"Failed to run auto-migration: {migrate_err}")
                    body = (
                        "<h1>Database not ready</h1>"
                        "<p>The Django auth database table is missing, and automatic migration failed.</p>"
                        f"<p>Migration Error: <code>{migrate_err}</code></p>"
                        "<p>Ensure your database is configured correctly and migrations have been applied.</p>"
                        "<p>On Render, make sure <code>DATABASE_URL</code> is set and the service has run <code>python manage.py migrate --noinput</code>.</p>"
                        f"<pre>{message}</pre>"
                    )
                    return HttpResponse(body, status=500)
        return None




