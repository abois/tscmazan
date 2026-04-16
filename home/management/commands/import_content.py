"""
Management command pour importer le contenu du site actuel tscmazan.com
dans le nouveau CMS Wagtail.

Usage: python manage.py import_content
"""

import io
import logging
from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from wagtail.images.models import Image
from wagtail.models import Page, Site

from actualites.models import ActualitesIndexPage, ArticlePage
from club.models import ClubPage, EcoleTennisPage, ResultatsPage, TarifsPage
from contact.models import ContactPage
from galerie.models import GaleriePage
from home.models import HomePage

logger = logging.getLogger(__name__)

BASE_URL = "https://www.tscmazan.com"


def fetch_page(path):
    """Récupère et parse une page du site actuel."""
    url = urljoin(BASE_URL, path)
    logger.info("Fetching %s", url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.content, "html.parser")


def download_image(url, title=""):
    """Télécharge une image et la crée dans Wagtail."""
    if not url:
        return None
    if url.startswith("/"):
        url = urljoin(BASE_URL, url)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "image" not in content_type:
            return None
        filename = url.split("/")[-1].split("?")[0] or "image.jpg"
        image = Image(title=title or filename)
        image.file.save(filename, ImageFile(io.BytesIO(resp.content)), save=True)
        logger.info("Downloaded image: %s", filename)
        return image
    except Exception as e:
        logger.warning("Failed to download image %s: %s", url, e)
        return None


class Command(BaseCommand):
    help = "Importe le contenu du site actuel tscmazan.com dans Wagtail"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Import du contenu tscmazan.com ===\n"))

        home_page = self._get_or_update_homepage()
        self._create_club_page(home_page)
        self._create_tarifs_page(home_page)
        self._create_ecole_page(home_page)
        self._create_actus(home_page)
        self._create_resultats_page(home_page)
        self._create_galerie_page(home_page)
        self._create_contact_page(home_page)

        self.stdout.write(self.style.SUCCESS("\n=== Import terminé ==="))

    def _get_or_update_homepage(self):
        """Met à jour la page d'accueil existante."""
        self.stdout.write("Mise à jour de la page d'accueil...")

        home = HomePage.objects.first()
        if not home:
            self.stdout.write(self.style.ERROR("Aucune HomePage trouvée !"))
            return None

        home.hero_titre = "Tennis Sporting Club Mazanais"
        home.hero_sous_titre = (
            "L'esprit sportif, le respect, dans un cadre accueillant, "
            "familial et festif au cœur du Vaucluse"
        )
        home.hero_cta_texte = "Réserver un court"
        home.hero_cta_url = "https://tenup.fft.fr/"
        home.hero_cta2_texte = "Prendre ma licence"
        home.hero_cta2_url = "https://tenup.fft.fr/"
        home.nb_courts = 4
        home.nb_adherents = 150
        home.annee_creation = 1970
        home.presentation_titre = "Bienvenue au club"
        home.presentation_texte = (
            "<p>Le Tennis Sporting Club Mazanais est un vivier de jeunes prometteurs "
            "axé sur la formation compétitive. Notre équipe pédagogique comprend un "
            "salarié titulaire du Brevet d'État, un jeune en formation DEJEPS, et "
            "trois bénévoles expérimentés.</p>"
            "<p>Le club propose des équipes adultes et jeunes en compétition aux niveaux "
            "départemental et régional, des cours loisirs en expansion, et des compétitions "
            "encadrées par des juges arbitres diplômés FFT.</p>"
            "<p><strong>N'oublions pas que chaque victoire est collective ! TSCM ATTITUDE !!</strong></p>"
        )
        home.ecole_titre = "École de Tennis"
        home.ecole_texte = (
            "<p>Formation et stages de tennis avec nos formateurs diplômés d'État. "
            "Cours pour enfants dès 5 ans et adultes, du mini-tennis à la compétition.</p>"
            "<p>Encadrés par <strong>Thierry Lobbé</strong> (moniteur diplômé d'État) "
            "et <strong>Thomas Bernard-Granger</strong> (moniteur DEJEPS).</p>"
        )

        # Essayer de télécharger des images du site
        try:
            soup = fetch_page("/")
            imgs = soup.find_all("img")
            for img in imgs:
                src = img.get("src", "")
                alt = img.get("alt", "")
                if any(kw in src.lower() or kw in alt.lower() for kw in ["tennis", "court", "club", "hero", "banner"]):
                    hero_img = download_image(src, "Hero TSC Mazan")
                    if hero_img:
                        home.hero_image = hero_img
                        break
        except Exception as e:
            logger.warning("Erreur lors du téléchargement des images d'accueil : %s", e)

        home.save_revision().publish()
        self.stdout.write(self.style.SUCCESS("  Page d'accueil mise à jour"))
        return home

    def _create_child_page(self, parent, page_class, slug, title, **kwargs):
        """Crée une page enfant si elle n'existe pas déjà."""
        existing = page_class.objects.filter(slug=slug).first()
        if existing:
            self.stdout.write(f"  Page '{title}' existe déjà, mise à jour...")
            for key, value in kwargs.items():
                setattr(existing, key, value)
            existing.save_revision().publish()
            return existing

        page = page_class(title=title, slug=slug, **kwargs)
        parent.add_child(instance=page)
        page.save_revision().publish()
        self.stdout.write(self.style.SUCCESS(f"  Page '{title}' créée"))
        return page

    def _create_club_page(self, parent):
        """Crée la page Le Club avec les dirigeants."""
        self.stdout.write("Création de la page Le Club...")

        dirigeants_data = [
            {"type": "dirigeant", "value": {"nom": "Thierry Drai", "role": "Président"}},
            {"type": "dirigeant", "value": {"nom": "Didier Vander", "role": "Vice-président"}},
            {"type": "dirigeant", "value": {"nom": "Bertrand Ferary", "role": "Secrétaire Général"}},
            {"type": "dirigeant", "value": {"nom": "Stéphan Chaumont", "role": "Trésorier"}},
            {"type": "dirigeant", "value": {"nom": "Thierry Lobbé", "role": "Direction sportive"}},
            {"type": "dirigeant", "value": {"nom": "Denis Chalvidal", "role": "Arbitrage / Gestion des tournois"}},
            {"type": "dirigeant", "value": {"nom": "Jean-Pierre Lebreton", "role": "Sponsoring"}},
            {"type": "dirigeant", "value": {"nom": "Thomas Bernard-Granger", "role": "Pôle jeunes / Coaching"}},
        ]

        president_texte = (
            "<p>Je suis heureux de vous accueillir sur notre site internet.</p>"
            "<p>Le Tennis Sporting Club Mazanais est un vivier de jeunes prometteurs, "
            "axé sur la formation compétitive. Notre équipe pédagogique comprend un salarié "
            "titulaire du Brevet d'État, un jeune en formation DEJEPS, et trois bénévoles "
            "expérimentés.</p>"
            "<p>Le club propose des équipes adultes et jeunes en compétition (niveaux "
            "départemental/régional), des cours « loisirs » en expansion, et des compétitions "
            "encadrées par juges arbitres diplômés FFT (JAE1 - JAT1 - JAT2).</p>"
            "<p>Les valeurs que nous défendons sont <strong>l'esprit sportif, le respect, "
            "dans un cadre accueillant, familial et festif</strong>.</p>"
            "<p><em>N'oublions pas que chaque victoire est collective !</em></p>"
            "<p><strong>TSCM ATTITUDE !!</strong></p>"
        )

        self._create_child_page(
            parent,
            ClubPage,
            "le-club",
            "Le Club",
            intro=(
                "<p>Découvrez le Tennis Sporting Club Mazanais, ses dirigeants, "
                "son histoire et sa localisation au cœur du Vaucluse.</p>"
            ),
            president_titre="Le mot du Président",
            president_texte=president_texte,
            president_nom="Thierry Drai",
            dirigeants=dirigeants_data,
            adresse="Chemin du Bigourd, Site du COSEC\n84380 Mazan",
        )

    def _create_tarifs_page(self, parent):
        """Crée la page Tarifs."""
        self.stdout.write("Création de la page Tarifs...")

        contenu = (
            "<p>Le coût total d'une inscription inclut : la cotisation de base au club, "
            "la licence FFT (assurance) et le badge d'accès.</p>"
            "<h3>Cotisations</h3>"
            "<ul>"
            "<li><strong>Adulte</strong> : 140 €</li>"
            "<li><strong>Couple</strong> : 275 € (inclus 2 licences)</li>"
            "<li><strong>Enfant 5-7 ans</strong> + 1h cours/semaine : 160 €</li>"
            "<li><strong>Enfant 8-18 ans</strong> + 1h cours/semaine : 170 €</li>"
            "<li><strong>Enfant 8-18 ans</strong> + 1h30 cours/semaine : 230 €</li>"
            "<li><strong>Enfant 8-18 ans</strong> + 3h cours/semaine : 400 €</li>"
            "</ul>"
            "<h3>Options</h3>"
            "<ul>"
            "<li>Entraînement compétition adultes : 100 €</li>"
            "<li>Préparation physique & cardio (adultes) : 100 € (30 séances)</li>"
            "<li>Préparation physique & cardio (jeunes 10-15 ans) : 100 €</li>"
            "</ul>"
            "<p><em>Réduction de 10 € par enfant à partir du 2ème enfant.</em></p>"
            "<p>Paiement par chèque accepté (maximum 3 chèques sur 3 mois).</p>"
        )

        self._create_child_page(
            parent,
            TarifsPage,
            "tarifs",
            "Tarifs",
            intro="<p>Retrouvez ci-dessous les tarifs d'adhésion au Tennis Sporting Club Mazanais.</p>",
            contenu=contenu,
            lien_inscription="https://tenup.fft.fr/",
        )

    def _create_ecole_page(self, parent):
        """Crée la page École de Tennis."""
        self.stdout.write("Création de la page École de Tennis...")

        contenu = (
            "<p>L'école de tennis du TSC Mazan propose des cours pour tous les âges "
            "et tous les niveaux, encadrés par des formateurs diplômés d'État.</p>"
            "<h3>Nos enseignants</h3>"
            "<ul>"
            "<li><strong>Thierry Lobbé</strong> — Moniteur diplômé d'État, "
            "responsable de la formation (06 24 51 54 01)</li>"
            "<li><strong>Thomas Bernard-Granger</strong> — Moniteur diplômé DEJEPS, "
            "adjoint à la formation</li>"
            "</ul>"
            "<h3>Programme enfants</h3>"
            "<ul>"
            "<li><strong>Mini-Tennis</strong> (5-6 ans) : samedi matin</li>"
            "<li><strong>Initiation</strong> (8-10 ans) : mercredi matin</li>"
            "<li><strong>Perfectionnement</strong> (10+ ans) : mercredi après-midi</li>"
            "</ul>"
            "<h3>Cours adultes</h3>"
            "<p>À partir de 18 ans : lundi, mardi, mercredi et vendredi soir.</p>"
            "<h3>Entraînement compétition</h3>"
            "<p>Jeudi 18h45-21h00, samedi 10h00-11h00.</p>"
            "<h3>Stages</h3>"
            "<p>Stages proposés pendant les vacances scolaires.</p>"
        )

        horaires = (
            "<table>"
            "<tr><th>Jour</th><th>Horaires</th></tr>"
            "<tr><td>Lundi</td><td>17h00 - 20h00</td></tr>"
            "<tr><td>Mardi</td><td>17h00 - 20h30 (cours adultes dames 19h30-20h30)</td></tr>"
            "<tr><td>Mercredi</td><td>9h30 - 12h00 & 13h00 - 18h00</td></tr>"
            "<tr><td>Jeudi</td><td>17h00 - 18h45 + entraînement équipe 18h45-20h45</td></tr>"
            "<tr><td>Vendredi</td><td>17h00 - 20h15</td></tr>"
            "<tr><td>Samedi</td><td>9h30 - 11h30 + entraînement équipe 10h00-11h00</td></tr>"
            "</table>"
            "<h3>Tarifs cours individuels</h3>"
            "<table>"
            "<tr><th>Type</th><th>Adhérent</th><th>Non-adhérent</th></tr>"
            "<tr><td>Individuel</td><td>35 €/h</td><td>40 €/h</td></tr>"
            "<tr><td>Cours à 2</td><td>17 €</td><td>23 €</td></tr>"
            "<tr><td>Cours à 3</td><td>12 €</td><td>17 €</td></tr>"
            "<tr><td>Cours à 4</td><td>9 €</td><td>11 €</td></tr>"
            "</table>"
        )

        self._create_child_page(
            parent,
            EcoleTennisPage,
            "ecole-de-tennis",
            "École de Tennis",
            intro="<p>Formation et stages de tennis pour enfants et adultes avec nos formateurs diplômés d'État.</p>",
            contenu=contenu,
            horaires=horaires,
            lien_inscription="https://tenup.fft.fr/",
        )

    def _create_actus(self, parent):
        """Crée l'index des actualités et quelques articles."""
        self.stdout.write("Création des actualités...")

        index = self._create_child_page(
            parent,
            ActualitesIndexPage,
            "actualites",
            "Actualités",
            intro="<p>Suivez toute l'actualité du Tennis Sporting Club Mazanais.</p>",
        )

        articles = [
            {
                "slug": "championnes-2025",
                "title": "Championnes de Vaucluse 2025",
                "date": date(2025, 6, 15),
                "intro": "Félicitations aux filles du TSCM, championnes de Vaucluse 2025 !",
                "contenu": (
                    "<p>Félicitations à notre équipe féminine qui remporte le titre de "
                    "championnes de Vaucluse 2025 ! Une fierté pour tout le club.</p>"
                ),
            },
            {
                "slug": "equipe-vincensini-podium",
                "title": "Équipe Vincensini sur le podium",
                "date": date(2024, 11, 1),
                "intro": "L'équipe féminine mixte remporte la Coupe Vincensini pour la première fois.",
                "contenu": (
                    "<p>Célébration de l'équipe féminine mixte ayant remporté la Coupe "
                    "Vincensini pour la première fois, avec promotion en 2ème division.</p>"
                    "<p>L'équipe était composée de Marie Caroline, Aurélie, Madeleine, "
                    "Yohan, Benoît et Didier, sous la capitainerie de Didier.</p>"
                ),
            },
            {
                "slug": "seniors-champions-vaucluse",
                "title": "Les séniors champions de Vaucluse",
                "date": date(2024, 6, 1),
                "intro": "L'équipe séniors masculine remporte le titre de champion de Vaucluse.",
                "contenu": (
                    "<p>L'équipe séniors masculine remporte le titre de champion de Vaucluse !</p>"
                    "<p>Félicitations aux joueurs : François Fuentes, Denis Blervaque, Claude Darcy, "
                    "Yohan Rousseau, Alexandre Lacote, Hugo Lebreton, et au capitaine "
                    "Benoît Marillier-Dubois.</p>"
                    "<p>Un grand merci au coach Thierry Lobbé. La cohésion d'équipe, "
                    "la camaraderie et la convivialité ont fait la différence.</p>"
                ),
            },
            {
                "slug": "champions-jeunes-2022-2023",
                "title": "Championnats jeunes 2022-2023",
                "date": date(2023, 6, 1),
                "intro": "Trois générations de jeunes champions de Vaucluse : 17/18, 15/16 et 13/14 ans.",
                "contenu": (
                    "<p>Le TSCM confirme sa vocation de formation avec trois générations "
                    "championnes de Vaucluse :</p>"
                    "<ul>"
                    "<li><strong>Jeunes 17/18 ans</strong> : Champions 2023</li>"
                    "<li><strong>Jeunes 15/16 ans</strong> : Champions 2022</li>"
                    "<li><strong>Jeunes 13/14 ans</strong> : Champions 2022</li>"
                    "</ul>"
                ),
            },
            {
                "slug": "equipe-2-finale-seniors",
                "title": "Équipe masculine 2 en finale séniors",
                "date": date(2024, 5, 5),
                "intro": "Après victoire en demi-finale contre Sérignan du Comtat, direction la finale !",
                "contenu": (
                    "<p>Après victoire contre Sérignan du Comtat en demi-finale, l'équipe 2 "
                    "séniors accède à la finale du championnat homme contre Crillon le Brave, "
                    "à domicile à Mazan.</p>"
                    "<p>Venez nombreux encourager nos joueurs !</p>"
                ),
            },
        ]

        for article_data in articles:
            existing = ArticlePage.objects.filter(slug=article_data["slug"]).first()
            if existing:
                self.stdout.write(f"  Article '{article_data['title']}' existe déjà, ignoré")
                continue
            article = ArticlePage(
                title=article_data["title"],
                slug=article_data["slug"],
                date=article_data["date"],
                intro=article_data["intro"],
                contenu=article_data["contenu"],
            )
            index.add_child(instance=article)
            article.save_revision().publish()
            self.stdout.write(self.style.SUCCESS(f"  Article '{article_data['title']}' créé"))

    def _create_resultats_page(self, parent):
        """Crée la page Résultats."""
        self.stdout.write("Création de la page Résultats...")

        contenu_data = [
            {
                "type": "section",
                "value": {
                    "titre": "Résultats Tournoi Open",
                    "contenu": (
                        "<p>Retrouvez les résultats du tournoi Open du TSCM.</p>"
                        "<h4>Finales</h4>"
                        "<ul>"
                        "<li>Finale Open Hommes</li>"
                        "<li>Finale Open Dames</li>"
                        "<li>Finale 4ème série Hommes</li>"
                        "<li>Finale 4ème série Femmes</li>"
                        "<li>Finale consolante Hommes</li>"
                        "<li>Finale consolante Femmes</li>"
                        "</ul>"
                    ),
                },
            },
            {
                "type": "section",
                "value": {
                    "titre": "Résultats Équipes",
                    "contenu": (
                        "<h4>Séniors</h4>"
                        "<p>Champions de Vaucluse 2024 ! Félicitations à toute l'équipe.</p>"
                        "<h4>Jeunes</h4>"
                        "<ul>"
                        "<li>Champions de Vaucluse 17/18 ans (2023)</li>"
                        "<li>Champions de Vaucluse 15/16 ans (2022)</li>"
                        "<li>Champions de Vaucluse 13/14 ans (2022)</li>"
                        "</ul>"
                    ),
                },
            },
        ]

        self._create_child_page(
            parent,
            ResultatsPage,
            "resultats",
            "Résultats",
            intro="<p>Résultats des tournois et compétitions du TSC Mazan.</p>",
            contenu=contenu_data,
        )

    def _create_galerie_page(self, parent):
        """Crée la page Galerie (vide, à remplir manuellement avec les photos)."""
        self.stdout.write("Création de la page Galerie...")

        self._create_child_page(
            parent,
            GaleriePage,
            "galerie",
            "Galerie Photos",
            intro="<p>Retrouvez en images les moments forts du Tennis Sporting Club Mazanais.</p>",
        )

    def _create_contact_page(self, parent):
        """Crée la page Contact."""
        self.stdout.write("Création de la page Contact...")

        self._create_child_page(
            parent,
            ContactPage,
            "contact",
            "Contact",
            intro=(
                "<p>N'hésitez pas à nous contacter pour toute question concernant "
                "le club, les inscriptions ou les cours de tennis.</p>"
            ),
            merci_texte="<p>Merci pour votre message ! Nous vous répondrons dans les plus brefs délais.</p>",
            adresse="Chemin du Bigourd\nSite du COSEC\n84380 Mazan",
            telephone="04 90 69 86 45",
            email="tscm@bbox.fr",
        )
