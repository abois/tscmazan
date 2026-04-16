import io
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.files.images import ImageFile
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from PIL import Image as PILImage
from wagtail.images.models import Image

from actualites.models import ActualitesIndexPage, ArticlePage
from club.models import Palmares
from galerie.models import Album, AlbumPhoto

from home.models import HomePage, SiteSettings
from .forms import AlbumForm, ArticleForm, PageForm, PalmaresForm, SettingsForm

# Pages éditables avec leurs icônes
PAGE_ICONS = {
    "HomePage": "🏠",
    "ClubPage": "🏛️",
    "TarifsPage": "💰",
    "EcoleTennisPage": "🎓",
    "ResultatsPage": "📊",
    "GaleriePage": "🖼️",
    "ContactPage": "✉️",
}

LOGIN_URL = "/admin/login/"


def _upload_image(file, title):
    """Upload un fichier image dans Wagtail."""
    data = file.read()
    pil = PILImage.open(io.BytesIO(data))
    w, h = pil.size
    img = Image(title=title, width=w, height=h)
    img.file.save(file.name, ImageFile(io.BytesIO(data), name=file.name))
    img.save()
    return img


# ── Dashboard ──────────────────────────────────────

@login_required(login_url=LOGIN_URL)
def dashboard(request):
    from wagtail.models import Page as WagtailPage

    home = HomePage.objects.first()
    pages = []
    if home:
        for child in home.get_children().live():
            cls_name = child.specific.__class__.__name__
            pages.append({
                "pk": child.pk,
                "title": child.title,
                "icone": PAGE_ICONS.get(cls_name, "📄"),
            })
        # Ajouter la homepage elle-même en premier
        pages.insert(0, {
            "pk": home.pk,
            "title": "Page d'accueil",
            "icone": "🏠",
        })

    return render(request, "gestion/dashboard.html", {
        "recent_articles": ArticlePage.objects.live().order_by("-date")[:5],
        "recent_albums": Album.objects.all()[:5],
        "recent_palmares": Palmares.objects.all()[:5],
        "pages": pages,
    })


# ── Actualités ─────────────────────────────────────

@login_required(login_url=LOGIN_URL)
def liste_actus(request):
    articles = ArticlePage.objects.live().order_by("-date")
    return render(request, "gestion/liste.html", {
        "titre_page": "Actualités",
        "icone": "📝",
        "items": [{"titre": a.title, "sous_titre": a.date.strftime("%d/%m/%Y"), "edit_url": f"/gestion/editer-actu/{a.pk}/", "view_url": a.url} for a in articles],
        "ajouter_url": "/gestion/nouvelle-actu/",
        "ajouter_label": "Nouvelle actu",
    })


@login_required(login_url=LOGIN_URL)
def nouvelle_actu(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            index = ActualitesIndexPage.objects.first()
            if not index:
                return render(request, "gestion/succes.html", {"titre": "Erreur", "description": "La page Actualités n'existe pas."})

            image = None
            if form.cleaned_data["photo"]:
                image = _upload_image(form.cleaned_data["photo"], form.cleaned_data["titre"])

            texte = form.cleaned_data["texte"]
            # Si CKEditor a déjà mis du HTML, on le garde tel quel
            if "<" not in texte:
                texte = f"<p>{texte}</p>"

            article = ArticlePage(
                title=form.cleaned_data["titre"],
                slug=slugify(form.cleaned_data["titre"][:50]),
                date=form.cleaned_data["date"],
                intro=form.cleaned_data["texte"][:250].replace("<", "").replace(">", ""),
                contenu=texte,
                image=image,
            )
            index.add_child(instance=article)
            article.save_revision().publish()
            return redirect("gestion:succes", type="actu")
    else:
        form = ArticleForm(initial={"date": date.today()})
    return render(request, "gestion/formulaire.html", {
        "form": form,
        "titre_page": "Publier une actu",
        "icone": "📝",
        "bouton": "Publier l'article",
    })


@login_required(login_url=LOGIN_URL)
def editer_actu(request, pk):
    article = get_object_or_404(ArticlePage, pk=pk)
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article.title = form.cleaned_data["titre"]
            article.date = form.cleaned_data["date"]
            texte = form.cleaned_data["texte"]
            if "<" not in texte:
                texte = f"<p>{texte}</p>"
            article.contenu = texte
            article.intro = form.cleaned_data["texte"][:250].replace("<", "").replace(">", "")

            if form.cleaned_data["photo"]:
                article.image = _upload_image(form.cleaned_data["photo"], article.title)

            article.save_revision().publish()
            return redirect("gestion:succes", type="actu")
    else:
        form = ArticleForm(initial={
            "titre": article.title,
            "date": article.date,
            "texte": article.contenu,
        })
    return render(request, "gestion/formulaire.html", {
        "form": form,
        "titre_page": "Modifier l'article",
        "icone": "📝",
        "bouton": "Enregistrer",
    })


# ── Palmarès ───────────────────────────────────────

@login_required(login_url=LOGIN_URL)
def liste_palmares(request):
    items = Palmares.objects.all()
    return render(request, "gestion/liste.html", {
        "titre_page": "Palmarès",
        "icone": "🏆",
        "items": [{"titre": f"{p.annee} — {p.titre}", "sous_titre": p.get_categorie_display(), "edit_url": f"/gestion/editer-palmares/{p.pk}/"} for p in items],
        "ajouter_url": "/gestion/ajouter-palmares/",
        "ajouter_label": "Nouveau résultat",
    })


@login_required(login_url=LOGIN_URL)
def ajouter_palmares(request):
    if request.method == "POST":
        form = PalmaresForm(request.POST, request.FILES)
        if form.is_valid():
            photo = None
            if form.cleaned_data["photo"]:
                photo = _upload_image(form.cleaned_data["photo"], form.cleaned_data["titre"])

            Palmares.objects.create(
                annee=form.cleaned_data["annee"],
                titre=form.cleaned_data["titre"],
                categorie=form.cleaned_data["categorie"],
                niveau=form.cleaned_data["niveau"],
                photo=photo,
            )
            return redirect("gestion:succes", type="palmares")
    else:
        form = PalmaresForm(initial={"annee": str(date.today().year)})
    return render(request, "gestion/formulaire.html", {
        "form": form,
        "titre_page": "Ajouter un résultat",
        "icone": "🏆",
        "bouton": "Enregistrer",
    })


@login_required(login_url=LOGIN_URL)
def editer_palmares(request, pk):
    p = get_object_or_404(Palmares, pk=pk)
    if request.method == "POST":
        form = PalmaresForm(request.POST, request.FILES)
        if form.is_valid():
            p.annee = form.cleaned_data["annee"]
            p.titre = form.cleaned_data["titre"]
            p.categorie = form.cleaned_data["categorie"]
            p.niveau = form.cleaned_data["niveau"]
            if form.cleaned_data["photo"]:
                p.photo = _upload_image(form.cleaned_data["photo"], p.titre)
            p.save()
            return redirect("gestion:succes", type="palmares")
    else:
        form = PalmaresForm(initial={
            "annee": p.annee,
            "titre": p.titre,
            "categorie": p.categorie,
            "niveau": p.niveau,
        })
    return render(request, "gestion/formulaire.html", {
        "form": form,
        "titre_page": "Modifier le palmarès",
        "icone": "🏆",
        "bouton": "Enregistrer",
    })


# ── Albums photos ──────────────────────────────────

@login_required(login_url=LOGIN_URL)
def liste_albums(request):
    albums = Album.objects.all()
    return render(request, "gestion/liste.html", {
        "titre_page": "Albums photos",
        "icone": "📸",
        "items": [{"titre": a.titre, "sous_titre": f"{a.photos.count()} photos", "edit_url": f"/gestion/editer-album/{a.pk}/"} for a in albums],
        "ajouter_url": "/gestion/ajouter-photos/",
        "ajouter_label": "Nouvel album",
    })


@login_required(login_url=LOGIN_URL)
def ajouter_photos(request):
    if request.method == "POST":
        form = AlbumForm(request.POST, request.FILES)
        files = request.FILES.getlist("photos")
        if form.is_valid() and files:
            album = Album.objects.create(
                titre=form.cleaned_data["titre"],
                date=form.cleaned_data["date"],
            )
            for i, f in enumerate(files):
                img = _upload_image(f, f"{album.titre} - {i + 1}")
                AlbumPhoto.objects.create(album=album, image=img, sort_order=i)
            return redirect("gestion:succes", type="photos")
    else:
        form = AlbumForm()
    return render(request, "gestion/formulaire.html", {
        "form": form,
        "titre_page": "Ajouter des photos",
        "icone": "📸",
        "bouton": "Créer l'album",
    })


@login_required(login_url=LOGIN_URL)
def editer_album(request, pk):
    album = get_object_or_404(Album, pk=pk)
    if request.method == "POST":
        form = AlbumForm(request.POST, request.FILES)
        files = request.FILES.getlist("photos")
        if form.is_valid():
            album.titre = form.cleaned_data["titre"]
            album.date = form.cleaned_data["date"]
            album.save()
            if files:
                start = album.photos.count()
                for i, f in enumerate(files):
                    img = _upload_image(f, f"{album.titre} - {start + i + 1}")
                    AlbumPhoto.objects.create(album=album, image=img, sort_order=start + i)
            return redirect("gestion:succes", type="photos")
    else:
        form = AlbumForm(initial={"titre": album.titre, "date": album.date})
    return render(request, "gestion/formulaire_album.html", {
        "form": form,
        "album": album,
        "titre_page": f"Modifier : {album.titre}",
        "icone": "📸",
        "bouton": "Enregistrer",
    })


# ── Pages statiques ────────────────────────────────

# Mapping des champs éditables par type de page
PAGE_FIELDS = {
    "HomePage": [
        ("hero_titre", "Titre du hero", "text"),
        ("hero_sous_titre", "Sous-titre du hero", "text"),
        ("presentation_titre", "Titre présentation", "text"),
        ("presentation_texte", "Texte de présentation", "ckeditor"),
        ("ecole_titre", "Titre école de tennis", "text"),
        ("ecole_texte", "Texte école de tennis", "ckeditor"),
        ("nb_courts", "Nombre de courts", "number"),
        ("nb_adherents", "Nombre d'adhérents", "number"),
    ],
    "ClubPage": [
        ("intro", "Introduction", "ckeditor"),
        ("president_nom", "Nom du président", "text"),
        ("president_texte", "Mot du président", "ckeditor"),
        ("adresse", "Adresse du club", "textarea"),
    ],
    "TarifsPage": [
        ("intro", "Introduction", "ckeditor"),
        ("contenu", "Contenu des tarifs", "ckeditor"),
    ],
    "EcoleTennisPage": [
        ("intro", "Introduction", "ckeditor"),
        ("contenu", "Contenu", "ckeditor"),
        ("horaires", "Horaires et tarifs cours", "ckeditor"),
    ],
    "ResultatsPage": [
        ("intro", "Introduction", "ckeditor"),
        ("equipes_texte", "Résultats par équipes", "ckeditor"),
    ],
    "ContactPage": [
        ("intro", "Introduction", "ckeditor"),
        ("adresse", "Adresse", "textarea"),
        ("telephone", "Téléphone", "text"),
        ("email", "Email", "text"),
    ],
}


@login_required(login_url=LOGIN_URL)
def editer_page(request, pk):
    from wagtail.models import Page as WagtailPage

    page = get_object_or_404(WagtailPage, pk=pk).specific
    cls_name = page.__class__.__name__
    fields = PAGE_FIELDS.get(cls_name, [])

    if not fields:
        return redirect("gestion:dashboard")

    if request.method == "POST":
        for field_name, label, field_type in fields:
            value = request.POST.get(field_name, "")
            if field_type == "number":
                value = int(value) if value else 0
            setattr(page, field_name, value)
        page.save_revision().publish()
        return redirect("gestion:succes", type="page")

    return render(request, "gestion/editer_page.html", {
        "page_obj": page,
        "titre_page": f"Modifier : {page.title}",
        "fields": [(name, label, ftype, getattr(page, name, "")) for name, label, ftype in fields],
    })


# ── Paramètres ─────────────────────────────────────

@login_required(login_url=LOGIN_URL)
def parametres(request):
    settings_obj, _ = SiteSettings.objects.get_or_create(pk=1)

    if request.method == "POST":
        form = SettingsForm(request.POST)
        if form.is_valid():
            for field_name in form.cleaned_data:
                setattr(settings_obj, field_name, form.cleaned_data[field_name])
            settings_obj.save()
            return redirect("gestion:succes", type="settings")
    else:
        form = SettingsForm(initial={
            "tenup_url": settings_obj.tenup_url,
            "telephone": settings_obj.telephone,
            "email": settings_obj.email,
            "adresse": settings_obj.adresse,
            "facebook_url": settings_obj.facebook_url,
            "instagram_url": settings_obj.instagram_url,
        })
    return render(request, "gestion/formulaire.html", {
        "form": form,
        "titre_page": "Paramètres du site",
        "icone": "⚙️",
        "bouton": "Enregistrer",
    })


# ── Succès ─────────────────────────────────────────

@login_required(login_url=LOGIN_URL)
def succes(request, type):
    messages = {
        "actu": ("Article publié !", "Votre actualité est en ligne."),
        "palmares": ("Résultat ajouté !", "Le palmarès a été mis à jour."),
        "photos": ("Album créé !", "Les photos sont en ligne dans la galerie."),
        "page": ("Page mise à jour !", "Les modifications sont en ligne."),
        "settings": ("Paramètres sauvegardés !", "Les modifications sont effectives."),
    }
    titre, desc = messages.get(type, ("Terminé !", ""))
    return render(request, "gestion/succes.html", {"titre": titre, "description": desc})
