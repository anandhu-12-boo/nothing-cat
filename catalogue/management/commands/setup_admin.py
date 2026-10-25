import getpass
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the dashboard administrator or explicitly reset its password."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Prompt for or use NOTHING_ADMIN_PASSWORD to reset the existing password.",
        )

    def handle(self, *args, **options):
        email = "heimglobal@gmail.com"
        user_model = get_user_model()
        user = user_model._default_manager.filter(email__iexact=email).first()
        created = user is None
        password_changed = created or options["reset_password"]

        if password_changed:
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

        if created:
            user = user_model(username=email, email=email)
        elif user is None:
            raise CommandError("The administrator account could not be loaded.")

        user.email = email
        user.username = email
        if password_changed:
            user.set_password(password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Administrator account ready for {email}; "
                f"password {'set' if password_changed else 'unchanged'}."
            )
        )
