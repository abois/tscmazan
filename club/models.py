from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.models import Orderable, Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.blocks import CharBlock, StructBlock, RichTextBlock
from wagtail.images.blocks import ImageChooserBlock


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


class Equipe(models.Model):
    """Une équipe du club engagée en compétition."""

    nom = models.CharField(
        max_length=120,
        help_text="Ex: Équipe Séniors Masculine",
    )
    description = models.TextField(
        help_text="Joueurs, capitaine, résultats marquants…",
    )
    ordre = models.PositiveIntegerField(
        default=0,
        help_text="Position dans la liste (plus petit = plus haut)",
    )

    panels = [
        FieldPanel("nom"),
        FieldPanel("description"),
        FieldPanel("ordre"),
    ]

    class Meta:
        verbose_name = "Équipe"
        verbose_name_plural = "Équipes"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom


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

    def stats(self):
        """Compteurs de matchs (utilise prefetch_related si dispo)."""
        victoires = defaites = a_venir = total = 0
        for m in self.matchs.all():
            total += 1
            if not m.score:
                a_venir += 1
            elif m.victoire:
                victoires += 1
            else:
                defaites += 1
        return {
            "total": total,
            "victoires": victoires,
            "defaites": defaites,
            "a_venir": a_venir,
        }

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


class PartenairesPage(Page):
    """Page Partenaires & Sponsoring."""

    # ── Hero ─────────────────────────────────────────
    hero_eyebrow = models.CharField(
        max_length=120,
        default="Sponsoring & Partenariat",
        verbose_name="Sur-titre du hero",
    )
    hero_titre = models.CharField(
        max_length=200,
        default="Devenez partenaire du TSCM",
        verbose_name="Titre du hero",
    )
    intro = RichTextField(
        blank=True,
        help_text="Accroche en haut de page (sous le titre hero).",
    )

    # ── Section "Nos offres" ─────────────────────────
    offres_eyebrow = models.CharField(
        max_length=120,
        default="Nos offres",
        verbose_name="Sur-titre section offres",
    )
    offres_titre = models.CharField(
        max_length=200,
        default="4 formules pour tous les budgets",
        verbose_name="Titre section offres",
    )
    offres_intro = RichTextField(
        blank=True,
        default=(
            "Du soutien à partir de <strong>150 €</strong> aux offres premium, "
            "choisissez la visibilité qui vous ressemble. Toutes nos offres sont "
            "en exclusivité ou en nombre limité."
        ),
        verbose_name="Intro section offres",
    )

    # ── Offre 1 ──────────────────────────────────────
    offre_1_badge = models.CharField(max_length=40, default="Exclusivité", verbose_name="Offre 1 — badge")
    offre_1_titre = models.CharField(
        max_length=200,
        default="Logo en action sur nos t-shirts",
        verbose_name="Offre 1 — titre",
    )
    offre_1_prix = models.CharField(max_length=40, default="150 €", verbose_name="Offre 1 — prix")
    offre_1_prix_suffixe = models.CharField(max_length=40, default="/ an", verbose_name="Offre 1 — suffixe prix")
    offre_1_description = RichTextField(
        blank=True,
        default=(
            "Votre logo sur la manche des t-shirts du club, en vente toute l'année "
            "auprès de nos licenciés via notre partenaire <strong>ASTON</strong>."
        ),
        verbose_name="Offre 1 — description",
    )
    offre_1_bullet_1 = models.CharField(max_length=160, default="Environ 30 t-shirts par production", verbose_name="Offre 1 — point 1")
    offre_1_bullet_2 = models.CharField(max_length=160, default="Visibilité sur toutes les équipes", verbose_name="Offre 1 — point 2")
    offre_1_bullet_3 = models.CharField(max_length=160, default="Diffusion pendant 1 an", verbose_name="Offre 1 — point 3")

    # ── Offre 2 ──────────────────────────────────────
    offre_2_badge = models.CharField(max_length=40, default="Exclusivité", verbose_name="Offre 2 — badge")
    offre_2_titre = models.CharField(
        max_length=200,
        default="Logo sur nos tableaux des scores",
        verbose_name="Offre 2 — titre",
    )
    offre_2_prix = models.CharField(max_length=40, default="180 €", verbose_name="Offre 2 — prix")
    offre_2_prix_suffixe = models.CharField(max_length=40, default="/ an", verbose_name="Offre 2 — suffixe prix")
    offre_2_description = RichTextField(
        blank=True,
        default=(
            "Votre logo sur les <strong>4 tableaux de scores</strong> du club — "
            "présent sur chaque match officiel, sous les yeux de joueurs et de spectateurs."
        ),
        verbose_name="Offre 2 — description",
    )
    offre_2_bullet_1 = models.CharField(max_length=160, default="4 tableaux, 4 courts", verbose_name="Offre 2 — point 1")
    offre_2_bullet_2 = models.CharField(max_length=160, default="~100 matchs par saison", verbose_name="Offre 2 — point 2")
    offre_2_bullet_3 = models.CharField(max_length=160, default="Diffusion pendant 1 an", verbose_name="Offre 2 — point 3")

    # ── Offre 3 ──────────────────────────────────────
    offre_3_badge = models.CharField(max_length=40, default="Exclusivité", verbose_name="Offre 3 — badge")
    offre_3_titre = models.CharField(
        max_length=200,
        default="Logo sur nos filets de court",
        verbose_name="Offre 3 — titre",
    )
    offre_3_prix = models.CharField(max_length=40, default="dès 200 €", verbose_name="Offre 3 — prix")
    offre_3_prix_suffixe = models.CharField(max_length=40, default="/ an", verbose_name="Offre 3 — suffixe prix")
    offre_3_description = RichTextField(
        blank=True,
        default=(
            "Votre logo sur <strong>2 ou 4 filets</strong> (90 × 60 cm). Seule entreprise "
            "visible sur l'un des côtés des filets pendant 1 an."
        ),
        verbose_name="Offre 3 — description",
    )
    offre_3_bullet_1 = models.CharField(max_length=160, default="<strong>Premium</strong> — 2 filets : 200 €", verbose_name="Offre 3 — point 1")
    offre_3_bullet_2 = models.CharField(max_length=160, default="<strong>Privilège</strong> — 4 filets : 250 €", verbose_name="Offre 3 — point 2")
    offre_3_bullet_3 = models.CharField(max_length=160, default="Diffusion pendant 1 an", verbose_name="Offre 3 — point 3")

    # ── Offre 4 ──────────────────────────────────────
    offre_4_badge = models.CharField(max_length=40, default="Premium", verbose_name="Offre 4 — badge")
    offre_4_titre = models.CharField(
        max_length=200,
        default="Bâches publicitaires sur terrain",
        verbose_name="Offre 4 — titre",
    )
    offre_4_prix = models.CharField(max_length=40, default="Sur devis", verbose_name="Offre 4 — prix")
    offre_4_prix_suffixe = models.CharField(max_length=40, default="1 an", verbose_name="Offre 4 — suffixe prix")
    offre_4_description = RichTextField(
        blank=True,
        default=(
            "Bâches <strong>2 × 1,5 m</strong> installées sur les grillages de milieu de "
            "terrain et fonds de court. Fourniture par nos soins, ou fournie par vos soins "
            "et installée par nous."
        ),
        verbose_name="Offre 4 — description",
    )
    offre_4_bullet_1 = models.CharField(max_length=160, default="Visibilité maximale sur court", verbose_name="Offre 4 — point 1")
    offre_4_bullet_2 = models.CharField(max_length=160, default="Fabrication possible de notre côté", verbose_name="Offre 4 — point 2")
    offre_4_bullet_3 = models.CharField(max_length=160, default="Diffusion pendant 1 an", verbose_name="Offre 4 — point 3")

    # ── Section "Sur mesure" ─────────────────────────
    sur_mesure_eyebrow = models.CharField(
        max_length=120,
        default="Sur mesure",
        verbose_name="Sur-titre section sur-mesure",
    )
    sur_mesure_titre = models.CharField(
        max_length=200,
        default="Chez nous, tout est possible",
        verbose_name="Titre section sur-mesure",
    )
    offre_personnalisee_texte = RichTextField(
        blank=True,
        verbose_name="Texte de l'offre personnalisée",
        help_text="Bloc \"Offre sur mesure\" après les 4 offres standards.",
    )
    sur_mesure_cta_label = models.CharField(
        max_length=120,
        default="Construire une offre ensemble",
        verbose_name="Label du bouton sur-mesure",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [FieldPanel("hero_eyebrow"), FieldPanel("hero_titre"), FieldPanel("intro")],
            heading="Hero",
        ),
        MultiFieldPanel(
            [FieldPanel("offres_eyebrow"), FieldPanel("offres_titre"), FieldPanel("offres_intro")],
            heading="Section Nos offres",
        ),
        MultiFieldPanel(
            [
                FieldPanel("offre_1_badge"), FieldPanel("offre_1_titre"),
                FieldPanel("offre_1_prix"), FieldPanel("offre_1_prix_suffixe"),
                FieldPanel("offre_1_description"),
                FieldPanel("offre_1_bullet_1"), FieldPanel("offre_1_bullet_2"), FieldPanel("offre_1_bullet_3"),
            ],
            heading="Offre 1",
        ),
        MultiFieldPanel(
            [
                FieldPanel("offre_2_badge"), FieldPanel("offre_2_titre"),
                FieldPanel("offre_2_prix"), FieldPanel("offre_2_prix_suffixe"),
                FieldPanel("offre_2_description"),
                FieldPanel("offre_2_bullet_1"), FieldPanel("offre_2_bullet_2"), FieldPanel("offre_2_bullet_3"),
            ],
            heading="Offre 2",
        ),
        MultiFieldPanel(
            [
                FieldPanel("offre_3_badge"), FieldPanel("offre_3_titre"),
                FieldPanel("offre_3_prix"), FieldPanel("offre_3_prix_suffixe"),
                FieldPanel("offre_3_description"),
                FieldPanel("offre_3_bullet_1"), FieldPanel("offre_3_bullet_2"), FieldPanel("offre_3_bullet_3"),
            ],
            heading="Offre 3",
        ),
        MultiFieldPanel(
            [
                FieldPanel("offre_4_badge"), FieldPanel("offre_4_titre"),
                FieldPanel("offre_4_prix"), FieldPanel("offre_4_prix_suffixe"),
                FieldPanel("offre_4_description"),
                FieldPanel("offre_4_bullet_1"), FieldPanel("offre_4_bullet_2"), FieldPanel("offre_4_bullet_3"),
            ],
            heading="Offre 4",
        ),
        MultiFieldPanel(
            [
                FieldPanel("sur_mesure_eyebrow"), FieldPanel("sur_mesure_titre"),
                FieldPanel("offre_personnalisee_texte"), FieldPanel("sur_mesure_cta_label"),
            ],
            heading="Section Sur mesure",
        ),
    ]

    class Meta:
        verbose_name = "Page Partenaires"

    parent_page_types = ["home.HomePage"]


class ResultatsPage(Page):
    intro = RichTextField(blank=True)
    lien_fft = models.URLField(
        blank=True,
        default="https://tenup.fft.fr/club/62840344",
        verbose_name="Lien FFT / Tenup",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("lien_fft"),
    ]

    def get_context(self, request):
        from datetime import date as _date

        context = super().get_context(request)
        context["palmares_list"] = Palmares.objects.all()

        all_comps = list(Competition.objects.prefetch_related("matchs").all())
        today = _date.today()

        def _statut(c):
            if c.date_fin and c.date_fin < today:
                return "passee"
            if c.date_debut:
                if c.date_debut > today:
                    return "a_venir"
                # Compétition sans date_fin commencée il y a plus de 6 mois → passée
                if not c.date_fin and (today - c.date_debut).days > 180:
                    return "passee"
            return "en_cours"

        competitions_en_cours = [c for c in all_comps if _statut(c) == "en_cours"]
        competitions_a_venir = [c for c in all_comps if _statut(c) == "a_venir"]
        competitions_passees = [c for c in all_comps if _statut(c) == "passee"]

        context["competitions_list"] = all_comps  # compat
        context["competitions_groups"] = [
            ("En cours", competitions_en_cours),
            ("À venir", competitions_a_venir),
            ("Saisons précédentes", competitions_passees),
        ]

        # Titre adaptatif de la section + affichage des sous-titres par groupe
        groups_present = sum(bool(g) for g in (competitions_en_cours, competitions_a_venir, competitions_passees))
        context["competitions_show_subtitles"] = groups_present > 1
        if groups_present == 1:
            if competitions_en_cours:
                context["competitions_titre"] = "Saison en cours"
            elif competitions_passees:
                context["competitions_titre"] = "Saison écoulée"
            else:
                context["competitions_titre"] = "Saison à venir"
        else:
            context["competitions_titre"] = "Nos compétitions"

        context["equipes_list"] = Equipe.objects.all()
        return context

    class Meta:
        verbose_name = "Page Résultats"

    parent_page_types = ["home.HomePage"]
