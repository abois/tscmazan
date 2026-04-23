# Mise en production — TSC Mazan

Checklist complète à parcourir avant et après déploiement. Les étapes sont groupées par domaine. Coche au fur et à mesure.

---

## 1. Environnement & secrets

- [ ] Définir `DJANGO_SETTINGS_MODULE=tscmazan.settings.production`
- [ ] `SECRET_KEY` lue depuis une variable d'environnement (ne jamais commiter)
- [ ] `ALLOWED_HOSTS` configuré dans `production.py` ou via env :
  ```python
  ALLOWED_HOSTS = ["www.tscmazan.com", "tscmazan.com"]
  ```
- [ ] `WAGTAILADMIN_BASE_URL` (déjà `https://www.tscmazan.com` dans base.py) — à ajuster si autre domaine
- [ ] `CSRF_TRUSTED_ORIGINS` ajouté en prod :
  ```python
  CSRF_TRUSTED_ORIGINS = ["https://www.tscmazan.com", "https://tscmazan.com"]
  ```

## 2. Base de données

- [ ] Migrer SQLite → **PostgreSQL** pour la prod (recommandé Wagtail)
- [ ] Dans `production.py` ou `settings/local.py` :
  ```python
  DATABASES = {
      "default": {
          "ENGINE": "django.db.backends.postgresql",
          "NAME": os.environ["DB_NAME"],
          "USER": os.environ["DB_USER"],
          "PASSWORD": os.environ["DB_PASSWORD"],
          "HOST": os.environ.get("DB_HOST", "localhost"),
          "PORT": os.environ.get("DB_PORT", "5432"),
      }
  }
  ```
- [ ] Exporter la data SQLite → `python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission -e sessions --indent 2 > data.json`
- [ ] Créer la base PG, lancer `python manage.py migrate`, puis `loaddata data.json`
- [ ] Vérifier les 8 migrations `club/` dont la data-migration `0007_import_equipes`

## 3. Email (SMTP)

Le formulaire `/contact/` envoie un mail à l'admin via Wagtail `AbstractEmailForm`.

- [ ] Champs configurés sur la ContactPage dans l'admin Wagtail (déjà fait en dev) :
  - `to_address` = `tscm@bbox.fr` (ou mail dédié)
  - `from_address` = mail du domaine (ex. `noreply@tscmazan.com`)
  - `subject` = sujet du mail de notification
- [ ] Provider SMTP choisi : OVH, Brevo, Postmark, Mailgun, SendGrid…
- [ ] Ajouter dans `production.py` (ou mieux, `settings/local.py` pour ne pas commiter) :
  ```python
  import os
  EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
  EMAIL_HOST = os.environ["EMAIL_HOST"]
  EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
  EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
  DEFAULT_FROM_EMAIL = "TSC Mazan <noreply@tscmazan.com>"
  ```
- [ ] Tester l'envoi : `python manage.py sendtestemail tscm@bbox.fr`
- [ ] Configurer SPF / DKIM / DMARC sur le DNS du domaine pour éviter le spam

## 4. Assets statiques

- [ ] Installer Node côté serveur OU builder en local et commiter `tscmazan/static/css/tailwind.css`
- [ ] Build CSS : `npm ci && npm run build:css`
- [ ] Collecter les statiques : `python manage.py collectstatic --noinput`
- [ ] Vérifier que `whitenoise` ou nginx sert bien `/static/` (déjà configuré avec `whitenoise.middleware.WhiteNoiseMiddleware`)
- [ ] `ManifestStaticFilesStorage` est actif en prod (déjà dans production.py) — attention aux imports CSS relatifs

## 5. Médias utilisateur

- [ ] `MEDIA_ROOT` sur un volume persistant (pas dans le conteneur jetable)
- [ ] nginx sert `/media/` directement (pas Django)
- [ ] Backup régulier du dossier `media/` (photos palmarès, école, dirigeants, albums)

## 6. HTTPS & sécurité

Dans `production.py`, ajouter :

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
# Si derrière un reverse proxy qui termine TLS :
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

- [ ] Certificat TLS (Let's Encrypt via certbot ou managé par le provider)
- [ ] Redirection 301 de `http://` → `https://` et de `tscmazan.com` → `www.tscmazan.com` (ou inverse, mais choisir un seul host canonique)

## 7. Serveur d'application

Le `Dockerfile` existant installe **gunicorn 20.0.4** (à mettre à jour vers une version récente).

- [ ] Commande : `gunicorn tscmazan.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 30`
- [ ] Reverse proxy nginx devant, avec `/media/` servi par nginx
- [ ] Logs redirigés vers un fichier ou un service (journald, CloudWatch, etc.)
- [ ] Healthcheck : `curl -fsS https://www.tscmazan.com/ | grep "Tennis Sporting"`

## 8. DNS & domaine

- [ ] Enregistrement A / AAAA du domaine vers l'IP du serveur
- [ ] CNAME `www` → domaine racine (ou inversement)
- [ ] **MX** pour recevoir les mails sur l'alias `tscm@bbox.fr` (déjà géré par Bbox semble-t-il — à vérifier)
- [ ] SPF/DKIM pour les envois sortants (si on envoie depuis noreply@tscmazan.com)

## 9. Contenu initial (via `/gestion/` ou admin Wagtail)

### Paramètres du site (`/gestion/parametres/`)
- [ ] Téléphone, email, adresse
- [ ] URL Tenup (déjà renseignée)
- [ ] URLs Facebook / Instagram
- [ ] URL boutique ASTON

### Homepage
- [ ] `seo_title` (déjà défini : « Tennis Club de Mazan — Tennis & pickleball en Vaucluse »)
- [ ] `search_description` (déjà défini)
- [ ] Image hero, chiffres clés (licenciés, courts, équipes, année)

### ContactPage
- [ ] `to_address`, `from_address`, `subject` (déjà définis — vérifier après le dump SQL)
- [ ] `adresse`, `telephone`, `email`, `latitude`, `longitude`

### Autres pages
- [ ] `le-club/` : dirigeants (StreamField), mot du président, photo
- [ ] `ecole-de-tennis/` : contenu, horaires
- [ ] `tarifs/` : contenu
- [ ] `partenaires/` : vérifier les 4 offres et leurs prix (éditables via `/gestion/page/<pk>/`)
- [ ] `resultats/` : lancer `python manage.py sync_tenup` si la commande est prête (voir `home/management/commands/sync_tenup.py`)
- [ ] Créer au moins une actu et un album photo

### Menu
- [ ] Vérifier `/gestion/menu/` — entrées et ordre

## 10. SEO post-déploiement

- [ ] Vérifier `https://www.tscmazan.com/sitemap.xml` renvoie du 200
- [ ] Vérifier `https://www.tscmazan.com/robots.txt` renvoie du 200 et contient bien `Sitemap: https://www.tscmazan.com/sitemap.xml`
- [ ] Soumettre le sitemap à **Google Search Console** (property https:// avec www)
- [ ] Vérifier l'indexation avec `site:tscmazan.com` après quelques jours
- [ ] Tester les balises Open Graph / Twitter :
  - [https://www.opengraph.xyz/](https://www.opengraph.xyz/) ou metatags.io
  - Facebook Debugger : https://developers.facebook.com/tools/debug/
  - Card Validator Twitter
- [ ] Tester le JSON-LD : https://search.google.com/test/rich-results
  - SportsClub sur la home
  - BreadcrumbList + AboutPage sur /le-club/
  - ItemList + SportsEvent sur /resultats/
  - ContactPage sur /contact/
- [ ] Valider l'accessibilité / Lighthouse (≥ 95 en SEO / accessibilité attendu)
- [ ] Créer un profil **Google Business** pour le club (photos, horaires, adresse — capital pour le SEO local "tennis mazan", "tennis vaucluse")

## 11. PWA

- [ ] Vérifier `https://www.tscmazan.com/manifest.json` accessible
- [ ] Vérifier `/serviceworker.js` chargé sur la home (DevTools → Application → Service Workers)
- [ ] Tester l'install sur Android Chrome / iOS Safari
- [ ] Vérifier l'offline fallback (page `/offline/`)

## 12. Superuser Wagtail

- [ ] Créer un superuser : `python manage.py createsuperuser`
- [ ] Vérifier qu'on peut se connecter sur `/admin/` (Wagtail) et `/gestion/` (interface simplifiée)
- [ ] Créer les comptes bénévoles avec **juste** les droits édition (pas superuser) — à voir dans Wagtail Groups

## 13. Synchronisation Tenup (compétitions & matchs)

- [ ] Vérifier la commande `python manage.py sync_tenup` (import des matchs FFT)
- [ ] Si elle nécessite des credentials, les mettre en env
- [ ] Mettre en place un **cron** pour la lancer quotidiennement (ex. via `cron` système ou via `django-q` / `celery` si déjà présent)
- [ ] Exemple cron : `0 2 * * * cd /app && python manage.py sync_tenup >> /var/log/tscm/sync.log 2>&1`

## 14. Sauvegarde & monitoring

- [ ] Backup quotidien de la DB (dump PG compressé vers S3 ou équivalent)
- [ ] Backup hebdomadaire du dossier `media/`
- [ ] Monitoring uptime (UptimeRobot, Better Stack, etc.)
- [ ] Sentry (ou équivalent) pour les erreurs Django 500 — optionnel mais utile

## 15. Post-go-live : vérifs finales

Ordre à suivre le jour J :

1. [ ] Déployer, lancer migrations, collectstatic
2. [ ] Se connecter sur `/admin/` et `/gestion/` avec le superuser
3. [ ] Soumettre une demande de test via `/contact/` et vérifier :
   - Apparition dans `/gestion/contacts/`
   - Réception du mail sur `tscm@bbox.fr`
4. [ ] Tester la navigation mobile (viewport 375px, iPhone réel idéalement)
5. [ ] Tester `/resultats/`, `/partenaires/`, `/le-club/`, `/ecole-de-tennis/`, `/tarifs/`, `/actualites/`, `/galerie/`
6. [ ] Vérifier la bannière PWA (peut être dismissée)
7. [ ] Tester la 404 : aller sur `/inexistant/`
8. [ ] Soumettre le sitemap à Google Search Console
9. [ ] Google Business : poster la fiche à jour avec photos
10. [ ] Communiquer l'URL aux licenciés (newsletter, Facebook, affiches club)

---

## Quick-reference : variables d'environnement attendues

À fournir via `.env`, secrets manager, systemd `Environment=`, ou équivalent :

```
DJANGO_SETTINGS_MODULE=tscmazan.settings.production
SECRET_KEY=...
ALLOWED_HOSTS=www.tscmazan.com,tscmazan.com
DB_NAME=tscmazan
DB_USER=tscmazan
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@tscmazan.com
EMAIL_HOST_PASSWORD=...
```

## Commandes mémo

```sh
# Build CSS Tailwind
npm ci && npm run build:css

# Collecter les statiques
python manage.py collectstatic --noinput

# Migrer la base
python manage.py migrate

# Créer un superuser
python manage.py createsuperuser

# Synchro Tenup
python manage.py sync_tenup

# Lancer en prod
gunicorn tscmazan.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 30
```
