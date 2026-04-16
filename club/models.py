from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.models import Orderable, Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.blocks import CharBlock, StructBlock, RichTextBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet


class DirigeantBlock(StructBlock):
    nom = CharBlock(max_length=100)
    role = CharBlock(max_length=100)
    photo = ImageChooserBlock(required=False)

    class Meta:
        icon = "user"
        label = "Dirigeant"


class ClubPage(Page):
    intro = RichTextField(blank=True)

    president_titre = models.CharField(max_length=120, default="Le mot du Président")
    president_texte = RichTextField(blank=True)
    president_photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    president_nom = models.CharField(max_length=100, blank=True)

    dirigeants = StreamField(
        [("dirigeant", DirigeantBlock())],
        blank=True,
        use_json_field=True,
    )

    adresse = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel(
            [
                FieldPanel("president_titre"),
                FieldPanel("president_texte"),
                FieldPanel("president_photo"),
                FieldPanel("president_nom"),
            ],
            heading="Mot du Président",
        ),
        FieldPanel("dirigeants"),
        MultiFieldPanel(
            [
                FieldPanel("adresse"),
                FieldPanel("latitude"),
                FieldPanel("longitude"),
            ],
            heading="Localisation",
        ),
    ]

    class Meta:
        verbose_name = "Page du Club"

    parent_page_types = ["home.HomePage"]


class TarifsPage(Page):
    intro = RichTextField(blank=True)
    contenu = RichTextField(blank=True)
    document_tarifs = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    lien_inscription = models.URLField(blank=True, default="https://tenup.fft.fr")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("contenu"),
        FieldPanel("document_tarifs"),
        FieldPanel("lien_inscription"),
    ]

    class Meta:
        verbose_name = "Page Tarifs"

    parent_page_types = ["home.HomePage"]


class EcoleTennisPage(Page):
    intro = RichTextField(blank=True)
    contenu = RichTextField(blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    horaires = RichTextField(blank=True, verbose_name="Horaires et planning")
    lien_inscription = models.URLField(blank=True, default="https://tenup.fft.fr")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("contenu"),
        FieldPanel("image"),
        FieldPanel("horaires"),
        FieldPanel("lien_inscription"),
    ]

    class Meta:
        verbose_name = "Page École de Tennis"

    parent_page_types = ["home.HomePage"]


CATEGORIE_CHOICES = [
    ("jeunes", "Jeunes"),
    ("seniors", "Séniors"),
    ("dames", "Dames"),
    ("mixte", "Mixte"),
]

NIVEAU_CHOICES = [
    ("departemental", "Départemental"),
    ("regional", "Régional"),
    ("national", "National"),
]


@register_snippet
class Palmares(models.Model):
    """Une entrée au palmarès — un titre, une année. Simple."""

    annee = models.CharField(max_length=10, verbose_name="Année", help_text="Ex: 2025")
    titre = models.CharField(max_length=150, help_text="Ex: Champions de Vaucluse Jeunes 17/18")
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, blank=True)
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, blank=True)
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("annee"),
        FieldPanel("titre"),
        FieldPanel("categorie"),
        FieldPanel("niveau"),
        FieldPanel("photo"),
    ]

    class Meta:
        verbose_name = "Palmarès"
        verbose_name_plural = "Palmarès"
        ordering = ["-annee", "titre"]

    def __str__(self):
        return f"{self.annee} — {self.titre}"


@register_snippet
class Competition(ClusterableModel):
    """Une compétition avec ses matchs."""

    titre = models.CharField(max_length=150, help_text="Ex: Open de Mazan 2025")
    saison = models.CharField(max_length=20, blank=True, help_text="Ex: 2024/2025")
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    description = RichTextField(blank=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("titre"),
                FieldPanel("saison"),
                FieldPanel("date_debut"),
                FieldPanel("date_fin"),
                FieldPanel("description"),
            ],
            heading="Compétition",
        ),
        InlinePanel("matchs", label="Match", help_text="Ajoutez les matchs de la compétition"),
    ]

    class Meta:
        verbose_name = "Compétition"
        ordering = ["-date_debut", "-pk"]

    def __str__(self):
        return self.titre


class Match(Orderable):
    """Un match dans une compétition."""

    competition = ParentalKey(Competition, on_delete=models.CASCADE, related_name="matchs")
    tour = models.CharField(max_length=80, blank=True, help_text="Ex: Finale, 1/2 finale")
    joueur_equipe = models.CharField(max_length=150, verbose_name="Joueur / Équipe TSC")
    adversaire = models.CharField(max_length=150, blank=True)
    score = models.CharField(max_length=50, blank=True, help_text="Ex: 6-3 6-4")
    victoire = models.BooleanField(default=False, verbose_name="Victoire ?")

    panels = [
        FieldPanel("tour"),
        FieldPanel("joueur_equipe"),
        FieldPanel("adversaire"),
        FieldPanel("score"),
        FieldPanel("victoire"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Match"

    def __str__(self):
        return f"{self.tour} — {self.joueur_equipe} vs {self.adversaire}"


class ResultatsPage(Page):
    intro = RichTextField(blank=True)
    equipes_texte = RichTextField(
        blank=True,
        verbose_name="Résultats par équipes",
        help_text="Résumé libre des résultats par équipe",
    )
    lien_fft = models.URLField(
        blank=True,
        default="https://tenup.fft.fr/club/62840344",
        verbose_name="Lien FFT / Tenup",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("equipes_texte"),
        FieldPanel("lien_fft"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["palmares_list"] = Palmares.objects.all()
        context["competitions_list"] = Competition.objects.prefetch_related("matchs").all()
        return context

    class Meta:
        verbose_name = "Page Résultats"

    parent_page_types = ["home.HomePage"]
