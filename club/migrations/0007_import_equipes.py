import re

from django.db import migrations


EQUIPE_PATTERN = re.compile(r"<h3>(.*?)</h3>\s*<p>(.*?)</p>", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(html):
    return TAG_RE.sub("", html or "").strip()


def importer_equipes_depuis_richtext(apps, schema_editor):
    ResultatsPage = apps.get_model("club", "ResultatsPage")
    Equipe = apps.get_model("club", "Equipe")

    for page in ResultatsPage.objects.all():
        html = page.equipes_texte or ""
        if not html:
            continue
        for ordre, match in enumerate(EQUIPE_PATTERN.finditer(html)):
            nom = _strip_tags(match.group(1))
            description = _strip_tags(match.group(2))
            if not nom:
                continue
            Equipe.objects.get_or_create(
                nom=nom,
                defaults={"description": description, "ordre": ordre},
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("club", "0006_equipe"),
    ]

    operations = [
        migrations.RunPython(importer_equipes_depuis_richtext, noop_reverse),
    ]
