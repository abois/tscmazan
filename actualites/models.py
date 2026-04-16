from django.core.paginator import Paginator
from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.search import index

ARTICLES_PER_PAGE = 20


class ActualitesIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        all_articles = (
            ArticlePage.objects.child_of(self).live().order_by("-date")
        )
        paginator = Paginator(all_articles, ARTICLES_PER_PAGE)
        page_number = request.GET.get("page", 1)
        context["articles"] = paginator.get_page(page_number)
        return context

    class Meta:
        verbose_name = "Index des actualités"

    parent_page_types = ["home.HomePage"]
    subpage_types = ["actualites.ArticlePage"]


class ArticlePage(Page):
    date = models.DateField("Date de publication")
    intro = models.CharField(max_length=250, blank=True)
    contenu = RichTextField(blank=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("contenu"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("image"),
        FieldPanel("contenu"),
    ]

    class Meta:
        verbose_name = "Article"

    parent_page_types = ["actualites.ActualitesIndexPage"]
