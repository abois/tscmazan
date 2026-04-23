from django import forms
from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from modelcluster.fields import ParentalKey


HONEYPOT_FIELD_NAME = "website"  # champ piège : les bots le remplissent, les humains non


class HoneypotFormBuilder(FormBuilder):
    """FormBuilder qui injecte un champ caché anti-bot.

    Les bots remplissent automatiquement tous les inputs — si `website`
    est rempli à la soumission, on jette silencieusement le formulaire.
    """

    @property
    def formfields(self):
        fields = super().formfields
        fields[HONEYPOT_FIELD_NAME] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={
                "autocomplete": "off",
                "tabindex": "-1",
                "style": "position:absolute;left:-9999px;opacity:0;height:0;width:0;",
                "aria-hidden": "true",
            }),
            label="Ne pas remplir ce champ",
        )
        return fields


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

    form_builder = HoneypotFormBuilder

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

    def process_form_submission(self, form):
        # Bot détecté : on ignore silencieusement (pas de 400, pas d'erreur visible
        # pour ne rien apprendre aux scripts). On enregistre juste dans les logs.
        if form.cleaned_data.get(HONEYPOT_FIELD_NAME):
            import logging
            logging.getLogger("django.security").warning(
                "Honeypot déclenché sur /contact/ — soumission ignorée."
            )
            return None
        # On retire le champ honeypot des données sauvegardées
        form.cleaned_data.pop(HONEYPOT_FIELD_NAME, None)
        return super().process_form_submission(form)

    class Meta:
        verbose_name = "Page Contact"

    parent_page_types = ["home.HomePage"]
