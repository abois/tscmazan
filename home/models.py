from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.blocks import (
    CharBlock,
    RichTextBlock,
    StructBlock,
    URLBlock,
    ListBlock,
)
from wagtail.images.blocks import ImageChooserBlock
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting


class HeroBlock(StructBlock):
    titre = CharBlock(max_length=120)
    sous_titre = CharBlock(max_length=250, required=False)
    image = ImageChooserBlock()
    cta_texte = CharBlock(max_length=50, default="Réserver un court")
    cta_url = URLBlock(default="https://tenup.fft.fr")
    cta2_texte = CharBlock(max_length=50, required=False, default="Prendre ma licence")
    cta2_url = URLBlock(required=False, default="https://tenup.fft.fr")

    class Meta:
        icon = "image"
        label = "Hero"


class CarteInfoBlock(StructBlock):
    icone = CharBlock(max_length=50, help_text="Nom de l'icône (ex: calendar, users, trophy, map-pin)")
    titre = CharBlock(max_length=80)
    description = CharBlock(max_length=200)
    lien_texte = CharBlock(max_length=50, required=False)
    lien_url = URLBlock(required=False)

    class Meta:
        icon = "doc-full"
        label = "Carte info"


class SponsorBlock(StructBlock):
    nom = CharBlock(max_length=100)
    logo = ImageChooserBlock()
    url = URLBlock(required=False)

    class Meta:
        icon = "group"
        label = "Sponsor"


class HomePage(Page):
    # Hero
    hero_titre = models.CharField(max_length=120, default="Tennis Sporting Club Mazanais")
    hero_sous_titre = models.CharField(
        max_length=250,
        blank=True,
        default="L'esprit sportif, le respect, dans un cadre accueillant, familial et festif",
    )
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Image hero (desktop)",
    )
    hero_image_mobile = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Image hero (mobile)",
        help_text="Version portrait pour mobile. Si vide, l'image desktop sera utilisée.",
    )
    hero_cta_texte = models.CharField(max_length=50, default="Réserver un court")
    hero_cta_url = models.URLField(default="https://tenup.fft.fr")
    hero_cta2_texte = models.CharField(max_length=50, blank=True, default="Prendre ma licence")
    hero_cta2_url = models.URLField(blank=True, default="https://tenup.fft.fr")

    # Section présentation
    presentation_titre = models.CharField(max_length=120, blank=True, default="Bienvenue au club")
    presentation_texte = RichTextField(blank=True)

    # Nombre de courts (chiffres clés)
    nb_courts = models.PositiveIntegerField(default=4, verbose_name="Nombre de courts")
    nb_adherents = models.PositiveIntegerField(default=150, verbose_name="Nombre d'adhérents")
    nb_equipes = models.PositiveIntegerField(default=15, verbose_name="Nombre d'équipes engagées")
    annee_creation = models.PositiveIntegerField(default=1970, verbose_name="Année de création")

    # Section école de tennis
    ecole_titre = models.CharField(max_length=120, blank=True, default="École de Tennis")
    ecole_texte = RichTextField(blank=True)
    ecole_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # Sponsors
    sponsors = StreamField(
        [("sponsor", SponsorBlock())],
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_titre"),
                FieldPanel("hero_sous_titre"),
                FieldPanel("hero_image"),
                FieldPanel("hero_image_mobile"),
                FieldPanel("hero_cta_texte"),
                FieldPanel("hero_cta_url"),
                FieldPanel("hero_cta2_texte"),
                FieldPanel("hero_cta2_url"),
            ],
            heading="Hero",
        ),
        MultiFieldPanel(
            [
                FieldPanel("presentation_titre"),
                FieldPanel("presentation_texte"),
            ],
            heading="Présentation",
        ),
        MultiFieldPanel(
            [
                FieldPanel("nb_courts"),
                FieldPanel("nb_adherents"),
                FieldPanel("nb_equipes"),
                FieldPanel("annee_creation"),
            ],
            heading="Chiffres clés",
        ),
        MultiFieldPanel(
            [
                FieldPanel("ecole_titre"),
                FieldPanel("ecole_texte"),
                FieldPanel("ecole_image"),
            ],
            heading="École de Tennis",
        ),
        FieldPanel("sponsors"),
    ]

    def get_context(self, request):
        from actualites.models import ArticlePage

        context = super().get_context(request)
        context["derniers_articles"] = (
            ArticlePage.objects.live().order_by("-date")[:3]
        )
        return context

    class Meta:
        verbose_name = "Page d'accueil"

    parent_page_types = ["wagtailcore.Page"]


@register_setting
class SiteSettings(BaseGenericSetting):
    """Paramètres globaux du site, administrables depuis Wagtail."""

    tenup_url = models.URLField(
        default="https://tenup.fft.fr/club/62840344",
        verbose_name="Lien Tenup (réservation & licence)",
        help_text="URL de la page du club sur Tenup",
    )
    shop_url = models.URLField(
        blank=True,
        default="https://www.sas-aston.fr",
        verbose_name="Lien boutique partenaire (ASTON)",
        help_text="URL de la boutique en ligne du club. Laisser vide pour masquer le lien du site.",
    )
    telephone = models.CharField(max_length=20, default="04 90 69 86 45")
    email = models.EmailField(default="tscm@bbox.fr")
    adresse = models.TextField(default="Chemin du Bigourd\nSite du COSEC\n84380 Mazan")
    facebook_url = models.URLField(blank=True, default="https://www.facebook.com/profile.php?id=100010233949238")
    instagram_url = models.URLField(blank=True)

    panels = [
        MultiFieldPanel(
            [FieldPanel("tenup_url"), FieldPanel("shop_url")],
            heading="Liens externes",
        ),
        MultiFieldPanel(
            [
                FieldPanel("telephone"),
                FieldPanel("email"),
                FieldPanel("adresse"),
            ],
            heading="Contact",
        ),
        MultiFieldPanel(
            [
                FieldPanel("facebook_url"),
                FieldPanel("instagram_url"),
            ],
            heading="Réseaux sociaux",
        ),
    ]

    class Meta:
        verbose_name = "Paramètres du site"


class MenuItem(models.Model):
    """Élément du menu de navigation, ordonnable."""

    label = models.CharField(max_length=50, verbose_name="Texte affiché")
    url = models.CharField(max_length=200, help_text="Ex: /le-club/ ou https://tenup.fft.fr")
    sort_order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True, verbose_name="Visible")
    open_new_tab = models.BooleanField(default=False, verbose_name="Ouvrir dans un nouvel onglet")

    class Meta:
        ordering = ["sort_order"]
        verbose_name = "Élément de menu"
        verbose_name_plural = "Éléments de menu"

    def __str__(self):
        return self.label
