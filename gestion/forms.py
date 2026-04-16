from django import forms

from actualites.models import ArticlePage
from club.models import Palmares, CATEGORIE_CHOICES, NIVEAU_CHOICES
from galerie.models import Album


class ArticleForm(forms.Form):
    titre = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "Ex: Victoire de l'équipe séniors !"}),
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    photo = forms.ImageField(
        required=False,
        help_text="Optionnel — une photo pour illustrer l'article",
    )
    texte = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 8, "placeholder": "Racontez l'événement...", "class": "ckeditor"}),
    )


class PalmaresForm(forms.Form):
    annee = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={"placeholder": "Ex: 2025"}),
        label="Année",
    )
    titre = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Ex: Champions de Vaucluse Jeunes 17/18"}),
    )
    categorie = forms.ChoiceField(
        choices=[("", "— Choisir —")] + CATEGORIE_CHOICES,
        required=False,
    )
    niveau = forms.ChoiceField(
        choices=[("", "— Choisir —")] + NIVEAU_CHOICES,
        required=False,
    )
    photo = forms.ImageField(required=False, help_text="Optionnel")


class PageForm(forms.Form):
    """Formulaire générique pour éditer le contenu d'une page Wagtail."""
    contenu = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 12, "class": "ckeditor"}),
        label="Contenu de la page",
        required=False,
    )


class SettingsForm(forms.Form):
    """Formulaire pour les paramètres globaux du site."""
    tenup_url = forms.URLField(label="Lien Tenup (réservation & licence)")
    telephone = forms.CharField(max_length=20, label="Téléphone du club")
    email = forms.EmailField(label="Email du club")
    adresse = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), label="Adresse", required=False)
    facebook_url = forms.URLField(label="Page Facebook", required=False)
    instagram_url = forms.URLField(label="Page Instagram", required=False)


class AlbumForm(forms.Form):
    titre = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Ex: Open de Mazan 2025"}),
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Date de l'événement",
    )
    photos = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={"allow_multiple_selected": True, "accept": "image/*"}),
        help_text="Sélectionnez plusieurs photos d'un coup",
    )
