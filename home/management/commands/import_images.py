"""
Management command pour télécharger les images du site actuel tscmazan.com
et les associer aux pages Wagtail.

Usage: python manage.py import_images
"""

import io
import logging
import time

import requests
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from wagtail.images.models import Image

from actualites.models import ArticlePage
from home.models import HomePage

logger = logging.getLogger(__name__)

BASE = "https://www.tscmazan.com"

# Images à télécharger en version haute résolution (pas les thumbs)
HERO_IMAGES = [
    (f"{BASE}/s/img/emotionheader.jpg?1760952206.920px.240px", "Bannière TSC Mazan"),
]

ARTICLE_IMAGES = {
    "championnes-2025": (f"{BASE}/s/cc_images/cache_2496290789.jpg?t=1751213145", "Championnes Vaucluse 2025"),
    "equipe-vincensini-podium": (f"{BASE}/s/cc_images/cache_2486119266.jpg?t=1571497674", "Équipe Vincensini podium"),
    "seniors-champions-vaucluse": (f"{BASE}/s/cc_images/cache_2486119361.jpg?t=1571501007", "Séniors champions Vaucluse"),
    "champions-jeunes-2022-2023": (f"{BASE}/s/cc_images/cache_2493122881.jpg?t=1678282014", "Champions jeunes 2023"),
    "equipe-2-finale-seniors": (f"{BASE}/s/cc_images/cache_2484674323.jpg?t=1556968386", "Équipe 2 finale séniors"),
}

GALLERY_ALBUMS = {
    "Champions Vaucluse 2023 U17/18": [
        f"{BASE}/s/cc_images/cache_2495177{i:03d}.jpg" for i in range(23, 41)
    ],
    "Fête du tennis juin 2022": [
        f"{BASE}/s/cc_images/cache_2492229{i:03d}.jpg" for i in range(179, 183)
    ],
    "Champions Vaucluse 2022": [
        f"{BASE}/s/cc_images/cache_2493122{i:03d}.jpg" for i in range(900, 904)
    ],
    "Open Mazan 2022": [
        f"{BASE}/s/cc_images/cache_2492229{i:03d}.JPG" for i in range(213, 217)
    ],
}

SPONSOR_IMAGES = [
    (f"{BASE}/s/cc_images/thumb_2496617451.png", "Sponsor 1"),
    (f"{BASE}/s/cc_images/thumb_2496617452.jpg", "Sponsor 2"),
    (f"{BASE}/s/cc_images/thumb_2496617453.png", "Sponsor 3"),
    (f"{BASE}/s/cc_images/thumb_2496617454.png", "Sponsor 4"),
    (f"{BASE}/s/cc_images/thumb_2496617455.png", "Sponsor 5"),
    (f"{BASE}/s/cc_images/thumb_2496617456.png", "Sponsor 6"),
    (f"{BASE}/s/cc_images/thumb_2496617457.jpg", "Sponsor 7"),
    (f"{BASE}/s/cc_images/thumb_2496617458.jpg", "Sponsor 8"),
    (f"{BASE}/s/cc_images/thumb_2496617459.jpg", "Sponsor 9"),
    (f"{BASE}/s/cc_images/thumb_2496617460.jpg", "Sponsor 10"),
    (f"{BASE}/s/cc_images/thumb_2496617461.png", "Sponsor 11"),
    (f"{BASE}/s/cc_images/thumb_2496617462.jpg", "Sponsor 12"),
    (f"{BASE}/s/cc_images/thumb_2496617463.jpg", "Sponsor 13"),
]


def download_image(url, title):
    """Télécharge une image et la crée dans Wagtail."""
    existing = Image.objects.filter(title=title).first()
    if existing:
        return existing

    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "image" not in content_type and len(resp.content) < 1000:
            return None

        ext = url.split(".")[-1].split("?")[0].lower()
        if ext not in ("jpg", "jpeg", "png", "gif", "webp"):
            ext = "jpg"
        filename = f"{title.replace(' ', '_').replace('/', '-')[:60]}.{ext}"

        # Lire les dimensions avec Pillow
        from PIL import Image as PILImage

        pil_img = PILImage.open(io.BytesIO(resp.content))
        width, height = pil_img.size

        image_file = ImageFile(io.BytesIO(resp.content), name=filename)
        image = Image(title=title, width=width, height=height, file=image_file)
        image.save()
        return image
    except Exception as e:
        logger.warning("Échec téléchargement %s: %s", url, e)
        return None


class Command(BaseCommand):
    help = "Télécharge les images du site tscmazan.com et les associe aux pages"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Import des images tscmazan.com ===\n"))

        self._import_hero()
        self._import_article_images()
        self._import_sponsor_images()
        self._import_gallery_images()

        total = Image.objects.count()
        self.stdout.write(self.style.SUCCESS(f"\n=== Terminé — {total} images au total dans Wagtail ==="))

    def _import_hero(self):
        self.stdout.write("Import de l'image hero...")
        for url, title in HERO_IMAGES:
            img = download_image(url, title)
            if img:
                home = HomePage.objects.first()
                if home and not home.hero_image:
                    home.hero_image = img
                    home.save_revision().publish()
                    self.stdout.write(self.style.SUCCESS(f"  Hero image '{title}' associée"))
            else:
                self.stdout.write(self.style.WARNING(f"  Échec: {title}"))

        # Essayer aussi la photo des championnes 2025 comme hero si le header est trop petit
        url_champ = f"{BASE}/s/cc_images/cache_2496290789.jpg?t=1751213145"
        img_champ = download_image(url_champ, "Championnes 2025 - Hero")
        if img_champ:
            home = HomePage.objects.first()
            if home:
                home.hero_image = img_champ
                home.ecole_image = download_image(
                    f"{BASE}/s/cc_images/cache_2493122881.jpg?t=1678282014",
                    "Champions jeunes - École"
                )
                home.save_revision().publish()
                self.stdout.write(self.style.SUCCESS("  Image hero et école mises à jour"))

    def _import_article_images(self):
        self.stdout.write("Import des images d'articles...")
        for slug, (url, title) in ARTICLE_IMAGES.items():
            img = download_image(url, title)
            if img:
                article = ArticlePage.objects.filter(slug=slug).first()
                if article and not article.image:
                    article.image = img
                    article.save_revision().publish()
                    self.stdout.write(self.style.SUCCESS(f"  '{title}' → article '{slug}'"))
            else:
                self.stdout.write(self.style.WARNING(f"  Échec: {title}"))
            time.sleep(0.3)

    def _import_sponsor_images(self):
        self.stdout.write("Import des logos sponsors...")
        home = HomePage.objects.first()
        if not home:
            return

        sponsors_data = []
        for url, title in SPONSOR_IMAGES:
            img = download_image(url, title)
            if img:
                sponsors_data.append({
                    "type": "sponsor",
                    "value": {"nom": title, "logo": img.pk, "url": ""},
                })
                self.stdout.write(self.style.SUCCESS(f"  Logo '{title}' téléchargé"))
            else:
                self.stdout.write(self.style.WARNING(f"  Échec: {title}"))
            time.sleep(0.3)

        if sponsors_data:
            home.sponsors = sponsors_data
            home.save_revision().publish()
            self.stdout.write(self.style.SUCCESS(f"  {len(sponsors_data)} sponsors associés à la homepage"))

    def _import_gallery_images(self):
        self.stdout.write("Import des photos galerie...")
        from galerie.models import GaleriePage

        galerie = GaleriePage.objects.first()
        if not galerie:
            self.stdout.write(self.style.WARNING("  Pas de page galerie trouvée"))
            return

        albums_data = []
        for album_title, urls in GALLERY_ALBUMS.items():
            self.stdout.write(f"  Album: {album_title}")
            photo_pks = []
            for i, url in enumerate(urls):
                title = f"{album_title} - Photo {i+1}"
                img = download_image(url, title)
                if img:
                    photo_pks.append(img.pk)
                    self.stdout.write(f"    Photo {i+1}/{len(urls)} OK")
                else:
                    self.stdout.write(self.style.WARNING(f"    Photo {i+1}/{len(urls)} ÉCHEC"))
                time.sleep(0.3)

            if photo_pks:
                albums_data.append({
                    "type": "album",
                    "value": {
                        "titre": album_title,
                        "description": "",
                        "photos": photo_pks,
                    },
                })

        if albums_data:
            galerie.albums = albums_data
            galerie.save_revision().publish()
            self.stdout.write(self.style.SUCCESS(f"  {len(albums_data)} albums créés"))
