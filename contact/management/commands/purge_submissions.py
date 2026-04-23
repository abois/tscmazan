"""Purge les demandes de contact antérieures à N jours (RGPD).

Usage :
    python manage.py purge_submissions              # default 1095j = 3 ans
    python manage.py purge_submissions --days 365   # override
    python manage.py purge_submissions --dry-run    # ne supprime rien, affiche juste
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from wagtail.contrib.forms.models import FormSubmission


class Command(BaseCommand):
    help = "Supprime les FormSubmission plus vieilles que N jours (RGPD)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=1095,
            help="Ancienneté en jours avant suppression (défaut : 1095 = 3 ans).",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="N'exécute pas la suppression, affiche juste le compte.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)
        qs = FormSubmission.objects.filter(submit_time__lt=cutoff)
        count = qs.count()

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(
                f"[dry-run] {count} soumission(s) antérieure(s) au {cutoff.date()} seraient supprimées."
            ))
            return

        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                f"Aucune soumission antérieure au {cutoff.date()}, rien à supprimer."
            ))
            return

        qs.delete()
        self.stdout.write(self.style.SUCCESS(
            f"{count} soumission(s) antérieure(s) au {cutoff.date()} supprimée(s)."
        ))
