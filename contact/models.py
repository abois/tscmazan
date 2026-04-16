from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from modelcluster.fields import ParentalKey


class FormField(AbstractFormField):
    page = ParentalKey("ContactPage", on_delete=models.CASCADE, related_name="form_fields")


class ContactPage(AbstractEmailForm):
    intro = RichTextField(blank=True)
    merci_texte = RichTextField(blank=True, verbose_name="Message de remerciement")

    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel(
            [
                FieldPanel("adresse"),
                FieldPanel("telephone"),
                FieldPanel("email"),
                FieldPanel("latitude"),
                FieldPanel("longitude"),
            ],
            heading="Coordonnées",
        ),
        InlinePanel("form_fields", label="Champs du formulaire"),
        FieldPanel("merci_texte"),
        MultiFieldPanel(
            [
                FieldPanel("from_address"),
                FieldPanel("to_address"),
                FieldPanel("subject"),
            ],
            heading="Email de notification",
        ),
    ]

    class Meta:
        verbose_name = "Page Contact"

    parent_page_types = ["home.HomePage"]
