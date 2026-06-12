import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "career_neuron.settings")

# Run migrations if enabled in environment (useful for Render/Docker)
if os.getenv("RUN_MIGRATIONS_ON_STARTUP", "false").lower() in ("true", "1", "yes"):
    try:
        django.setup()
        from django.core.management import call_command
        print("Running migrations on startup...")
        call_command("migrate", interactive=False)
    except Exception as e:
        print(f"Error running migrations on startup: {e}")

application = get_wsgi_application()

