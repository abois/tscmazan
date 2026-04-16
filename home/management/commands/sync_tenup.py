"""
Synchronisation des données depuis l'API publique Tenup FFT.

Usage:
    python manage.py sync_tenup              # Tout synchroniser
    python manage.py sync_tenup --tournois   # Seulement les tournois
    python manage.py sync_tenup --rencontres # Seulement les rencontres
    python manage.py sync_tenup --actus      # Seulement les actualités
"""

import logging
from datetime import date, datetime

import requests
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from actualites.models import ActualitesIndexPage, ArticlePage
from club.models import Competition, Match

logger = logging.getLogger(__name__)

CLUB_ID = "62840344"
BASE_URL = f"https://tenup.fft.fr/back/public/v1/clubs/{CLUB_ID}"
HEADERS = {"Accept": "application/json", "User-Agent": "TSCMazan/1.0"}


def fetch(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    logger.info("Fetching %s", url)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


class Command(BaseCommand):
    help = "Synchronise les données depuis Tenup FFT"

    def add_arguments(self, parser):
        parser.add_argument("--tournois", action="store_true")
        parser.add_argument("--rencontres", action="store_true")
        parser.add_argument("--actus", action="store_true")

    def handle(self, *args, **options):
        do_all = not any([options["tournois"], options["rencontres"], options["actus"]])

        if do_all or options["tournois"]:
            self._sync_tournois()
        if do_all or options["rencontres"]:
            self._sync_rencontres()
        if do_all or options["actus"]:
            self._sync_actus()

        self.stdout.write(self.style.SUCCESS("Synchronisation terminée"))

    def _sync_tournois(self):
        self.stdout.write("Synchronisation des tournois...")
        data = fetch("tournois")
        for t in data.get("tournois", []):
            comp, created = Competition.objects.update_or_create(
                titre=t["nom"],
                defaults={
                    "saison": f"{t['dateDebut'][:4]}",
                    "date_debut": t["dateDebut"],
                    "date_fin": t["dateFin"],
                    "description": self._build_tournoi_desc(t),
                },
            )
            action = "créé" if created else "mis à jour"
            self.stdout.write(f"  Tournoi '{t['nom']}' {action} ({t['statut']})")

    def _build_tournoi_desc(self, tournoi):
        epreuves = tournoi.get("epreuves", [])
        # Dédupliquer les épreuves
        seen = set()
        unique = []
        for e in epreuves:
            key = f"{e['natureEpreuve']['libelle']} - {e['categorieAge']['libelle']}"
            if key not in seen:
                seen.add(key)
                unique.append(key)
        lines = [f"<p><strong>Statut :</strong> {tournoi['statut']}</p>"]
        if unique:
            lines.append("<p><strong>Épreuves :</strong></p><ul>")
            for e in unique:
                lines.append(f"<li>{e}</li>")
            lines.append("</ul>")
        return "\n".join(lines)

    def _sync_rencontres(self):
        self.stdout.write("Synchronisation des rencontres...")

        for passe in [True, False]:
            label = "passées" if passe else "à venir"
            data = fetch(f"rencontres?passe={'true' if passe else 'false'}&page=1")
            rencontres = data.get("rencontres", [])
            self.stdout.write(f"  {len(rencontres)} rencontres {label}")

            # Regrouper par championnat
            by_champ = {}
            for r in rencontres:
                champ_name = r["championnat"]["libelle"]
                by_champ.setdefault(champ_name, []).append(r)

            for champ_name, matchs in by_champ.items():
                comp, created = Competition.objects.get_or_create(
                    titre=champ_name,
                    defaults={
                        "saison": matchs[0]["dateReelle"][:4] if matchs else "",
                        "date_debut": matchs[0]["dateReelle"] if matchs else None,
                    },
                )

                for r in matchs:
                    is_club_eq1 = r["idEquipe1"] == r["idEquipeClub"]
                    club_name = r["nomEquipe1"] if is_club_eq1 else r["nomEquipe2"]
                    adversaire = r["nomEquipe2"] if is_club_eq1 else r["nomEquipe1"]
                    score_club = r["scoreEquipe1"] if is_club_eq1 else r["scoreEquipe2"]
                    score_adv = r["scoreEquipe2"] if is_club_eq1 else r["scoreEquipe1"]
                    victoire = r.get("idEquipeGagnante") == r["idEquipeClub"]

                    score_str = ""
                    if score_club is not None and score_adv is not None:
                        score_str = f"{score_club}-{score_adv}"

                    tour = f"{r['dateReelle']} — {r.get('phase', {}).get('libelle', '')}"
                    if r.get("poule"):
                        tour += f" ({r['poule']['libelle']})"

                    Match.objects.update_or_create(
                        competition=comp,
                        joueur_equipe=club_name,
                        adversaire=adversaire,
                        defaults={
                            "tour": tour,
                            "score": score_str,
                            "victoire": victoire,
                        },
                    )
                self.stdout.write(f"    {champ_name}: {len(matchs)} matchs")

    def _sync_actus(self):
        self.stdout.write("Synchronisation des actualités Tenup...")
        data = fetch("actualites")

        index = ActualitesIndexPage.objects.first()
        if not index:
            self.stdout.write(self.style.WARNING("  Pas de page Actualités"))
            return

        for article in data.get("articles", []):
            dt = datetime.fromisoformat(article["datePublication"])
            slug = slugify(article["titre"][:50])

            existing = ArticlePage.objects.filter(slug=slug).first()
            if existing:
                self.stdout.write(f"  '{article['titre']}' existe déjà")
                continue

            texte = article.get("description", "")
            if "<" not in texte:
                texte = "<p>" + texte.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"

            page = ArticlePage(
                title=article["titre"],
                slug=slug,
                date=dt.date(),
                intro=texte[:250].replace("<p>", "").replace("</p>", "").replace("<br>", " "),
                contenu=texte,
            )
            index.add_child(instance=page)
            page.save_revision().publish()
            self.stdout.write(self.style.SUCCESS(f"  '{article['titre']}' créé"))
