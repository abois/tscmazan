"""
Personnalisation de l'admin Wagtail pour simplifier l'usage
par les bénévoles du club.
"""

from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from actualites.models import ArticlePage
from club.models import Competition, Palmares
from galerie.models import Album


# ──────────────────────────────────────────────
# 1. Snippets avec leurs propres menus
# ──────────────────────────────────────────────

class AlbumViewSet(SnippetViewSet):
    model = Album
    icon = "image"
    menu_label = "Albums photos"
    menu_name = "albums"
    menu_order = 200
    add_to_admin_menu = True
    list_display = ["titre", "date"]
    list_filter = ["date"]
    search_fields = ["titre"]


class PalmaresViewSet(SnippetViewSet):
    model = Palmares
    icon = "trophy"
    menu_label = "Palmarès"
    menu_name = "palmares"
    menu_order = 210
    add_to_admin_menu = True
    list_display = ["annee", "titre", "categorie"]
    list_filter = ["categorie", "niveau"]


class CompetitionViewSet(SnippetViewSet):
    model = Competition
    icon = "calendar"
    menu_label = "Compétitions"
    menu_name = "competitions"
    menu_order = 220
    add_to_admin_menu = True
    list_display = ["titre", "saison", "date_debut"]
    list_filter = ["saison"]


# Re-register with custom viewsets
register_snippet(Album, viewset=AlbumViewSet)
register_snippet(Palmares, viewset=PalmaresViewSet)
register_snippet(Competition, viewset=CompetitionViewSet)


# ──────────────────────────────────────────────
# 2. Raccourci "Nouvelle actu" dans le menu
# ──────────────────────────────────────────────

@hooks.register("register_admin_menu_item")
def register_actu_menu():
    from actualites.models import ActualitesIndexPage

    index = ActualitesIndexPage.objects.first()
    if index:
        url = f"/admin/pages/add/actualites/articlepage/{index.pk}/"
    else:
        url = "/admin/pages/"

    return MenuItem(
        "Nouvelle actu",
        url,
        icon_name="doc-full-inverse",
        order=190,
    )


# ──────────────────────────────────────────────
# 3. Masquer les menus inutiles pour simplifier
# ──────────────────────────────────────────────

@hooks.register("construct_main_menu")
def hide_unnecessary_menus(request, menu_items):
    """Cache les menus techniques pour les non-superusers."""
    if not request.user.is_superuser:
        hidden = {"documents", "rapports", "aide", "snippets"}
        menu_items[:] = [item for item in menu_items if item.name not in hidden]


# ──────────────────────────────────────────────
# 4. Dashboard personnalisé avec raccourcis
# ──────────────────────────────────────────────

class QuickActionPanel:
    order = 50

    def __init__(self, request):
        self.request = request

    @property
    def media(self):
        from django.forms import Media
        return Media()

    def render(self):
        from actualites.models import ActualitesIndexPage

        index = ActualitesIndexPage.objects.first()
        add_article_url = f"/admin/pages/add/actualites/articlepage/{index.pk}/" if index else "/admin/pages/"

        return format_html(
            """
            <section class="panel" style="margin-bottom: 2rem;">
                <h2 class="panel__heading" style="margin-bottom: 1rem;">Actions rapides</h2>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <a href="{}" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; background: #f8f4f0; border-radius: 0.5rem; text-decoration: none; color: #333; border: 1px solid #e5ddd5;">
                        <span style="font-size: 1.3rem;">📝</span>
                        <strong style="font-size: 0.9rem;">Publier une actu</strong>
                    </a>
                    <a href="/admin/snippets/galerie/album/create/" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; background: #f8f4f0; border-radius: 0.5rem; text-decoration: none; color: #333; border: 1px solid #e5ddd5;">
                        <span style="font-size: 1.3rem;">📸</span>
                        <strong style="font-size: 0.9rem;">Ajouter des photos</strong>
                    </a>
                    <a href="/admin/snippets/club/palmares/create/" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; background: #f8f4f0; border-radius: 0.5rem; text-decoration: none; color: #333; border: 1px solid #e5ddd5;">
                        <span style="font-size: 1.3rem;">🏆</span>
                        <strong style="font-size: 0.9rem;">Ajouter un palmarès</strong>
                    </a>
                    <a href="/admin/snippets/club/competition/create/" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; background: #f8f4f0; border-radius: 0.5rem; text-decoration: none; color: #333; border: 1px solid #e5ddd5;">
                        <span style="font-size: 1.3rem;">🎾</span>
                        <strong style="font-size: 0.9rem;">Ajouter une compétition</strong>
                    </a>
                </div>
            </section>
            """,
            add_article_url,
        )


@hooks.register("construct_homepage_panels")
def add_quick_actions_panel(request, panels):
    panels.insert(0, QuickActionPanel(request))


# ──────────────────────────────────────────────
# 5. Branding admin
# ──────────────────────────────────────────────

@hooks.register("insert_global_admin_css")
def admin_custom_css():
    return "<style>.sidebar .sidebar-panel { background: #3D1D09; }.sidebar .sidebar__inner { background: #3D1D09; }</style>"
