from django.urls import path

from . import views

app_name = "gestion"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Actualités
    path("nouvelle-actu/", views.nouvelle_actu, name="nouvelle_actu"),
    path("actus/", views.liste_actus, name="liste_actus"),
    path("editer-actu/<int:pk>/", views.editer_actu, name="editer_actu"),
    # Palmarès
    path("ajouter-palmares/", views.ajouter_palmares, name="ajouter_palmares"),
    path("palmares/", views.liste_palmares, name="liste_palmares"),
    path("editer-palmares/<int:pk>/", views.editer_palmares, name="editer_palmares"),
    # Albums
    path("ajouter-photos/", views.ajouter_photos, name="ajouter_photos"),
    path("albums/", views.liste_albums, name="liste_albums"),
    path("editer-album/<int:pk>/", views.editer_album, name="editer_album"),
    # Pages du site
    path("page/<int:pk>/", views.editer_page, name="editer_page"),
    # Menu
    path("menu/", views.gerer_menu, name="gerer_menu"),
    path("menu/ajouter/", views.ajouter_menu_item, name="ajouter_menu_item"),
    path("menu/<int:pk>/", views.editer_menu_item, name="editer_menu_item"),
    path("menu/reorder/", views.reorder_menu, name="reorder_menu"),
    # Paramètres
    path("parametres/", views.parametres, name="parametres"),
    # Succès
    path("succes/<str:type>/", views.succes, name="succes"),
]
