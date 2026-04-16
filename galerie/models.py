from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
class Album(ClusterableModel):
    """Un album photo, géré comme snippet indépendant."""

    titre = models.CharField(max_length=120)
    description = models.CharField(max_length=250, blank=True)
    date = models.DateField(
        null=True,
        blank=True,
        help_text="Date de l'événement (pour le tri)",
    )
    couverture = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Image de couverture de l'album (optionnel, sinon la 1ère photo sera utilisée)",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("titre"),
                FieldPanel("description"),
                FieldPanel("date"),
                FieldPanel("couverture"),
            ],
            heading="Informations de l'album",
        ),
        InlinePanel(
            "photos",
            label="Photo",
            help_text="Ajoutez des photos à l'album. Vous pouvez les réordonner par glisser-déposer.",
        ),
    ]

    class Meta:
        verbose_name = "Album photo"
        verbose_name_plural = "Albums photos"
        ordering = ["-date", "-pk"]

    def __str__(self):
        return self.titre

    @property
    def cover_image(self):
        if self.couverture:
            return self.couverture
        first = self.photos.first()
        return first.image if first else None


class AlbumPhoto(Orderable):
    """Une photo dans un album."""

    album = ParentalKey(Album, on_delete=models.CASCADE, related_name="photos")
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
    )
    legende = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Légende",
        help_text="Optionnel — courte description de la photo",
    )

    panels = [
        FieldPanel("image"),
        FieldPanel("legende"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Photo"


class GaleriePage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["albums"] = Album.objects.prefetch_related("photos__image").all()
        return context

    class Meta:
        verbose_name = "Galerie photos"

    parent_page_types = ["home.HomePage"]
