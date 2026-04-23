import io
from datetime import date

from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.files.images import ImageFile
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from PIL import Image as PILImage
from wagtail.images.models import Image

from wagtail.contrib.forms.models import FormSubmission

from actualites.models import ActualitesIndexPage, ArticlePage
from club.models import Equipe, Palmares
from contact.models import ContactPage
from galerie.models import Album, AlbumPhoto, GaleriePage

from home.models import HomePage, MenuItem, SiteSettings
from .forms import AlbumForm, ArticleForm, EquipeForm, PageForm, PalmaresForm, SettingsForm

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

# Pages qui ont une gestion dédiée → URL directe au lieu de editer_page
PAGE_REDIRECTS = {
    "ActualitesIndexPage": "/gestion/actus/",
    "ResultatsPage": "/gestion/palmares/",
}


@login_required(login_url=LOGIN_URL)
def dashboard(request):
    home = HomePage.objects.first()
    pages = []
    if home:
        # Homepage en premier
        pages.append({
            "pk": home.pk,
            "title": "Page d'accueil",
            "url": f"/gestion/page/{home.pk}/",
        })
        for child in home.get_children().live():
            cls_name = child.specific.__class__.__name__
            # Soit gestion dédiée, soit éditeur de page
            url = PAGE_REDIRECTS.get(cls_name, f"/gestion/page/{child.pk}/")
            pages.append({
                "pk": child.pk,
                "title": child.title,
                "url": url,
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
        "items": [
            {
                "titre": a.title,
                "sous_titre": a.date.strftime("%d/%m/%Y"),
                "edit_url": f"/gestion/editer-actu/{a.pk}/",
                "view_url": a.url,
                "share_url": f"/gestion/partager-actu/{a.pk}/",
            }
            for a in articles
        ],
        "ajouter_url": "/gestion/nouvelle-actu/",
        "ajouter_label": "Nouvelle actu",
        "retour_url": "/gestion/",
        "retour_label": "Accueil",
    })


@login_required(login_url=LOGIN_URL)
def partager_actu(request, pk):
    article = get_object_or_404(ArticlePage, pk=pk)
    return render(request, "gestion/succes.html", {
        "titre": "Partager sur Facebook",
        "description": "Partagez cette actualité sur la page du club.",
        "share_actu": {
            "pk": article.pk,
            "title": article.title,
            "intro": article.intro,
            "url": request.build_absolute_uri(article.url),
        },
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
            request.session["last_published_actu"] = {
                "pk": article.pk,
                "title": article.title,
                "intro": article.intro,
                "url": request.build_absolute_uri(article.url),
            }
            return redirect("gestion:succes", type="actu")
    else:
        form = ArticleForm(initial={"date": date.today()})
    return render(request, "gestion/formulaire.html", {
        "form": form,
        "titre_page": "Publier une actu",
        "icone": "📝",
        "bouton": "Publier l'article",
        "retour_url": "/gestion/actus/",
        "retour_label": "Actualités",
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
            request.session["last_published_actu"] = {
                "pk": article.pk,
                "title": article.title,
                "intro": article.intro,
                "url": request.build_absolute_uri(article.url),
            }
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
        "retour_url": "/gestion/actus/",
        "retour_label": "Actualités",
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
        "retour_url": "/gestion/",
        "retour_label": "Accueil",
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
        "retour_url": "/gestion/palmares/",
        "retour_label": "Palmarès",
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
        "retour_url": "/gestion/palmares/",
        "retour_label": "Palmarès",
    })


# ── Équipes ────────────────────────────────────────

@login_required(login_url=LOGIN_URL)
def liste_equipes(request):
    items = Equipe.objects.all()
    return render(request, "gestion/liste.html", {
        "titre_page": "Équipes engagées",
        "icone": "👥",
        "items": [
            {
                "titre": e.nom,
                "sous_titre": e.description[:120] + ("…" if len(e.description) > 120 else ""),
                "edit_url": f"/gestion/editer-equipe/{e.pk}/",
            }
            for e in items
        ],
        "ajouter_url": "/gestion/ajouter-equipe/",
        "ajouter_label": "Nouvelle équipe",
        "retour_url": "/gestion/",
        "retour_label": "Accueil",
    })


@login_required(login_url=LOGIN_URL)
def ajouter_equipe(request):
    if request.method == "POST":
        form = EquipeForm(request.POST)
        if form.is_valid():
            Equipe.objects.create(
                nom=form.cleaned_data["nom"],
                description=form.cleaned_data["description"],
                ordre=form.cleaned_data["ordre"],
            )
            return redirect("gestion:liste_equipes")
    else:
        next_ordre = (Equipe.objects.order_by("-ordre").values_list("ordre", flat=True).first() or 0) + 1
        form = EquipeForm(initial={"ordre": next_ordre})
    return render(request, "gestion/formulaire.html", {
        "form": form,
        "titre_page": "Ajouter une équipe",
        "icone": "👥",
        "bouton": "Enregistrer",
        "retour_url": "/gestion/equipes/",
        "retour_label": "Équipes",
    })


@login_required(login_url=LOGIN_URL)
def editer_equipe(request, pk):
    e = get_object_or_404(Equipe, pk=pk)
    if request.method == "POST":
        if request.POST.get("action") == "delete":
            e.delete()
            return redirect("gestion:liste_equipes")
        form = EquipeForm(request.POST)
        if form.is_valid():
            e.nom = form.cleaned_data["nom"]
            e.description = form.cleaned_data["description"]
            e.ordre = form.cleaned_data["ordre"]
            e.save()
            return redirect("gestion:liste_equipes")
    else:
        form = EquipeForm(initial={
            "nom": e.nom,
            "description": e.description,
            "ordre": e.ordre,
        })
    return render(request, "gestion/formulaire.html", {
        "form": form,
        "titre_page": "Modifier l'équipe",
        "icone": "👥",
        "bouton": "Enregistrer",
        "retour_url": "/gestion/equipes/",
        "retour_label": "Équipes",
        "delete_label": "Supprimer cette équipe",
        "delete_confirm": "Supprimer définitivement cette équipe ?",
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
        "retour_url": f"/gestion/page/{GaleriePage.objects.first().pk}/" if GaleriePage.objects.exists() else "/gestion/",
        "retour_label": "Galerie",
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
        "retour_url": "/gestion/albums/",
        "retour_label": "Albums",
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
        "retour_url": "/gestion/albums/",
        "retour_label": "Albums",
    })


@login_required(login_url=LOGIN_URL)
def supprimer_photo(request, photo_pk, album_pk):
    photo = get_object_or_404(AlbumPhoto, pk=photo_pk, album_id=album_pk)
    photo.delete()
    return redirect("gestion:editer_album", pk=album_pk)


# ── Pages statiques ────────────────────────────────

# Mapping des champs éditables par type de page
PAGE_FIELDS = {
    "HomePage": [
        ("hero_titre", "Titre du hero", "text"),
        ("hero_sous_titre", "Sous-titre du hero", "text"),
        ("presentation_titre", "Titre section Convivialité", "text"),
        ("presentation_texte", "Texte section Convivialité", "ckeditor"),
        ("ecole_titre", "Titre école de tennis", "text"),
        ("ecole_texte", "Texte école de tennis", "ckeditor"),
        ("nb_courts", "Nombre de courts", "number"),
        ("nb_adherents", "Nombre d'adhérents", "number"),
        ("nb_equipes", "Nombre d'équipes engagées", "number"),
        ("annee_creation", "Année de création du club", "number"),
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
    "PartenairesPage": [
        ("__section__", "Hero", "section"),
        ("hero_eyebrow", "Sur-titre (au-dessus du grand titre)", "text"),
        ("hero_titre", "Grand titre", "text"),
        ("intro", "Accroche sous le titre", "ckeditor"),

        ("__section__", "Section \"Nos offres\"", "section"),
        ("offres_eyebrow", "Sur-titre de la section", "text"),
        ("offres_titre", "Titre de la section", "text"),
        ("offres_intro", "Texte d'introduction", "ckeditor"),

        ("__section__", "Offre 1", "section"),
        ("offre_1_badge", "Badge (Exclusivité, Premium…)", "text"),
        ("offre_1_titre", "Titre de l'offre", "text"),
        ("offre_1_prix", "Prix affiché", "text"),
        ("offre_1_prix_suffixe", "Suffixe du prix (ex. / an)", "text"),
        ("offre_1_description", "Description", "ckeditor"),
        ("offre_1_bullet_1", "Point 1", "inline"),
        ("offre_1_bullet_2", "Point 2", "inline"),
        ("offre_1_bullet_3", "Point 3", "inline"),

        ("__section__", "Offre 2", "section"),
        ("offre_2_badge", "Badge", "text"),
        ("offre_2_titre", "Titre de l'offre", "text"),
        ("offre_2_prix", "Prix affiché", "text"),
        ("offre_2_prix_suffixe", "Suffixe du prix", "text"),
        ("offre_2_description", "Description", "ckeditor"),
        ("offre_2_bullet_1", "Point 1", "inline"),
        ("offre_2_bullet_2", "Point 2", "inline"),
        ("offre_2_bullet_3", "Point 3", "inline"),

        ("__section__", "Offre 3", "section"),
        ("offre_3_badge", "Badge", "text"),
        ("offre_3_titre", "Titre de l'offre", "text"),
        ("offre_3_prix", "Prix affiché", "text"),
        ("offre_3_prix_suffixe", "Suffixe du prix", "text"),
        ("offre_3_description", "Description", "ckeditor"),
        ("offre_3_bullet_1", "Point 1", "inline"),
        ("offre_3_bullet_2", "Point 2", "inline"),
        ("offre_3_bullet_3", "Point 3", "inline"),

        ("__section__", "Offre 4", "section"),
        ("offre_4_badge", "Badge", "text"),
        ("offre_4_titre", "Titre de l'offre", "text"),
        ("offre_4_prix", "Prix affiché", "text"),
        ("offre_4_prix_suffixe", "Suffixe du prix", "text"),
        ("offre_4_description", "Description", "ckeditor"),
        ("offre_4_bullet_1", "Point 1", "inline"),
        ("offre_4_bullet_2", "Point 2", "inline"),
        ("offre_4_bullet_3", "Point 3", "inline"),

        ("__section__", "Section \"Sur mesure\"", "section"),
        ("sur_mesure_eyebrow", "Sur-titre de la section", "text"),
        ("sur_mesure_titre", "Titre de la section", "text"),
        ("offre_personnalisee_texte", "Texte de la section", "ckeditor"),
        ("sur_mesure_cta_label", "Libellé du bouton", "text"),
    ],
    "EcoleTennisPage": [
        ("intro", "Introduction", "ckeditor"),
        ("contenu", "Contenu", "ckeditor"),
        ("horaires", "Horaires et tarifs cours", "ckeditor"),
    ],
    "ResultatsPage": [
        ("intro", "Introduction", "ckeditor"),
    ],
    "ContactPage": [
        ("intro", "Introduction", "ckeditor"),
        ("adresse", "Adresse", "textarea"),
        ("telephone", "Téléphone", "text"),
        ("email", "Email", "text"),
    ],
    "GaleriePage": [
        ("intro", "Texte d'introduction de la galerie", "ckeditor"),
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
            if field_type == "section":
                continue
            value = request.POST.get(field_name, "")
            if field_type == "number":
                value = int(value) if value else 0
            setattr(page, field_name, value)
        page.save_revision().publish()
        return redirect("gestion:succes", type="page")

    return render(request, "gestion/editer_page.html", {
        "page_obj": page,
        "titre_page": f"Modifier : {page.title}",
        "fields": [
            (name, label, ftype, getattr(page, name, "") if ftype != "section" else "")
            for name, label, ftype in fields
        ],
        "is_galerie": cls_name == "GaleriePage",
    })


# ── Demandes de contact ────────────────────────────

@login_required(login_url=LOGIN_URL)
def liste_contacts(request):
    submissions_qs = FormSubmission.objects.filter(
        page__in=ContactPage.objects.all()
    ).order_by("-submit_time")

    if request.method == "POST" and request.POST.get("delete_pk"):
        FormSubmission.objects.filter(pk=request.POST["delete_pk"]).delete()
        return redirect("gestion:liste_contacts")

    submissions = []
    for sub in submissions_qs:
        data = dict(sub.form_data or {})
        # Cherche les valeurs "classiques" pour le résumé de la ligne
        def _find(keys):
            for k, v in data.items():
                if any(needle in k.lower() for needle in keys) and v:
                    return v
            return ""
        submissions.append({
            "pk": sub.pk,
            "date": sub.submit_time,
            "nom": _find(["nom"]),
            "email": _find(["email", "mail"]),
            "objet": _find(["objet", "sujet"]),
            "champs": list(data.items()),
        })

    return render(request, "gestion/liste_contacts.html", {
        "submissions": submissions,
        "titre_page": "Demandes de contact",
        "retour_url": "/gestion/",
        "retour_label": "Accueil",
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
            "shop_url": settings_obj.shop_url,
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


# ── Menu ───────────────────────────────────────────

@login_required(login_url=LOGIN_URL)
def gerer_menu(request):
    return render(request, "gestion/menu.html", {
        "items": MenuItem.objects.all(),
    })


@login_required(login_url=LOGIN_URL)
def ajouter_menu_item(request):
    if request.method == "POST":
        last = MenuItem.objects.order_by("-sort_order").first()
        order = (last.sort_order + 10) if last else 0
        MenuItem.objects.create(
            label=request.POST["label"],
            url=request.POST["url"],
            sort_order=order,
        )
    return redirect("gestion:gerer_menu")


@login_required(login_url=LOGIN_URL)
def editer_menu_item(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete":
            item.delete()
            return redirect("gestion:gerer_menu")
        item.label = request.POST.get("label", item.label)
        item.url = request.POST.get("url", item.url)
        item.is_visible = request.POST.get("is_visible") == "on"
        item.open_new_tab = request.POST.get("open_new_tab") == "on"
        item.save()
        return redirect("gestion:gerer_menu")
    return render(request, "gestion/editer_menu_item.html", {"item": item})


@login_required(login_url=LOGIN_URL)
def reorder_menu(request):
    import json
    if request.method == "POST":
        data = json.loads(request.body)
        for i, pk in enumerate(data.get("order", [])):
            MenuItem.objects.filter(pk=int(pk)).update(sort_order=i * 10)
        from django.http import JsonResponse
        return JsonResponse({"ok": True})
    from django.http import JsonResponse
    return JsonResponse({"error": "POST only"}, status=405)


# ── Live Edit ──────────────────────────────────────

@login_required(login_url=LOGIN_URL)
def live_edit(request):
    import json
    from django.http import JsonResponse
    from wagtail.models import Page as WagtailPage

    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body)
    fields = data.get("fields", {})

    for field_name, info in fields.items():
        page_pk = info.get("page")
        value = info.get("value", "")
        if not page_pk:
            continue
        try:
            page = WagtailPage.objects.get(pk=int(page_pk)).specific
            if hasattr(page, field_name):
                setattr(page, field_name, value)
                page.save_revision().publish()
        except WagtailPage.DoesNotExist:
            continue

    # Sauvegarder les settings modifiés
    settings_data = data.get("settings", {})
    if settings_data:
        site_settings = SiteSettings.objects.first()
        if site_settings:
            for field_name, value in settings_data.items():
                if hasattr(site_settings, field_name):
                    setattr(site_settings, field_name, value)
            site_settings.save()

    return JsonResponse({"ok": True})


@login_required(login_url=LOGIN_URL)
def live_add_photos(request):
    from django.http import JsonResponse

    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    album_pk = request.POST.get("album_pk")
    files = request.FILES.getlist("photos")
    if not album_pk or not files:
        return JsonResponse({"error": "Missing data"}, status=400)

    album = get_object_or_404(Album, pk=int(album_pk))
    start = album.photos.count()
    for i, f in enumerate(files):
        img = _upload_image(f, f"{album.titre} - {start + i + 1}")
        AlbumPhoto.objects.create(album=album, image=img, sort_order=start + i)

    return JsonResponse({"ok": True, "count": len(files)})


# ── Logout ─────────────────────────────────────────

def logout_view(request):
    auth_logout(request)
    return redirect("/")


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
    context = {"titre": titre, "description": desc}

    # Bloc "Partager sur Facebook" après publication d'une actu
    if type == "actu":
        actu = request.session.pop("last_published_actu", None)
        if actu:
            context["share_actu"] = actu

    return render(request, "gestion/succes.html", context)
