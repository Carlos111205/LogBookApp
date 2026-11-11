from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from logbook.models import LogEntry, StudentProfile


class Command(BaseCommand):
    help = "Assign the pre-account single-student data to its owner's new username."

    def add_arguments(self, parser):
        parser.add_argument("username", help="Username of the student who owns the old single-user records")

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = get_user_model().objects.select_for_update().get(username=username)
        except get_user_model().DoesNotExist as exc:
            raise CommandError(f"No account exists for username '{username}'. Create that account first.") from exc

        old_profiles = list(StudentProfile.objects.select_for_update().filter(user__isnull=True))
        if len(old_profiles) > 1:
            raise CommandError("More than one old profile is unassigned; refusing to guess which student owns them.")
        old_entries = LogEntry.objects.filter(user__isnull=True)
        transferred = old_entries.count()
        current = StudentProfile.objects.filter(user=user).first()

        if old_profiles:
            legacy = old_profiles[0]
            if current:
                transferable = True
                for field in current._meta.concrete_fields:
                    if field.name in {"id", "user", "updated_at"}:
                        continue
                    value = getattr(current, field.name)
                    default = field.get_default()
                    if value not in (None, "", default):
                        transferable = False
                        break
                if not transferable:
                    raise CommandError("That account already has placement details. Refusing to overwrite them with old data.")
                for field in legacy._meta.concrete_fields:
                    if field.name not in {"id", "user", "updated_at"}:
                        setattr(current, field.name, getattr(legacy, field.name))
                current.save()
                legacy.delete()
            else:
                legacy.user = user
                legacy.save(update_fields=["user", "updated_at"])
        elif not transferred:
            self.stdout.write(self.style.WARNING("No unassigned old data was found."))
            return

        old_entries.update(user=user)
        self.stdout.write(self.style.SUCCESS(
            f"Assigned the old profile and {transferred} log book entries to '{username}'."
        ))
