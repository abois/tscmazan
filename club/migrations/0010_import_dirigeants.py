"""Migre les dirigeants du StreamField ClubPage.dirigeants → table Dirigeant."""
from django.db import migrations


def importer_dirigeants_depuis_streamfield(apps, schema_editor):
    ClubPage = apps.get_model("club", "ClubPage")
    Dirigeant = apps.get_model("club", "Dirigeant")
    Image = apps.get_model("wagtailimages", "Image")

    for page in ClubPage.objects.all():
        # Le StreamField est exposé sous forme JSON par l'ORM historique
        raw = page.dirigeants
        # Selon la version de Wagtail/Django, raw peut être un str JSON ou déjà une liste
        if hasattr(raw, "raw_data"):
            blocks = raw.raw_data
        elif isinstance(raw, list):
            blocks = raw
        else:
            import json
            try:
                blocks = json.loads(raw or "[]")
            except Exception:
                blocks = []

        for ordre, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            value = block.get("value") or {}
            nom = (value.get("nom") or "").strip()
            role = (value.get("role") or "").strip()
            if not nom:
                continue
            photo_id = value.get("photo")
            photo = None
            if photo_id:
                try:
                    photo = Image.objects.filter(pk=int(photo_id)).first()
                except (TypeError, ValueError):
                    photo = None
            Dirigeant.objects.get_or_create(
                nom=nom,
                role=role,
                defaults={"photo": photo, "ordre": ordre},
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("club", "0009_dirigeant"),
    ]

    operations = [
        migrations.RunPython(importer_dirigeants_depuis_streamfield, noop_reverse),
    ]
