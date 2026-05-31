from django.db import DatabaseError, OperationalError
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class DatabaseErrorCatchMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, (OperationalError, DatabaseError)):
            message = str(exception)
            if "no such table" in message or "auth_user" in message or "relation \"auth_user\"" in message:
                body = (
                    "<h1>Database not ready</h1>"
                    "<p>The Django auth database table is missing.</p>"
                    "<p>Ensure your database is configured correctly and migrations have been applied.</p>"
                    "<p>On Render, make sure <code>DATABASE_URL</code> is set and the service has run <code>python manage.py migrate --noinput</code>.</p>"
                    f"<pre>{message}</pre>"
                )
                return HttpResponse(body, status=500)
        return None
