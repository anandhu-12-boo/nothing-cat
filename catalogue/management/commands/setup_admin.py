import getpass
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update the dashboard administrator account."

    def handle(self, *args, **options):
        email = "heimglobal@gmail.com"
        password = (
            os.environ.get("NOTHING_ADMIN_PASSWORD")
            or os.environ.get("ADMIN_PASSWORD")
        )

        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "No admin password found in environment variables. "
                    "Provide one securely now."
                )
            )
            password = getpass.getpass("Admin password: ")

        if not password:
            raise CommandError("The administrator password cannot be empty.")

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            email=email,
            defaults={"username": email},
        )

        if not created:
            user.username = email

        user.email = email
        user.set_password(password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Administrator account ready for {email}."
            )
        )
