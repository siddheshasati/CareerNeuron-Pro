import os
import sys

from django.apps import AppConfig
from django.core.management import call_command


class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "portal"

    def ready(self):
        run_migrations = os.environ.get("RUN_MIGRATIONS_ON_STARTUP", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if not run_migrations:
            return

        management_commands = {
            "migrate",
            "makemigrations",
            "collectstatic",
            "shell",
            "dbshell",
            "showmigrations",
            "test",
        }
        if any(cmd in sys.argv for cmd in management_commands):
            return

        try:
            call_command("migrate", "--noinput")
        except Exception as exc:
            print("[portal] Startup migrate failed:", exc)
