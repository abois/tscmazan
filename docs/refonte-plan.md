# Plan global de refonte — TSCM

> Brief reçu le 2026-04-19 (`TSCM MAZAN.docx`). Inspiration : Tennis Club de Lyon ([tennisclublyon.com](https://www.tennisclublyon.com/)). Site actuel : [tscmazan.com](https://www.tscmazan.com/) (IONOS, daté, à remplacer).

## 1. Principes directeurs

- **Référence visuelle** : Tennis Club de Lyon — hiérarchie claire, chiffres clés en bande, sections partenaires distinctes, ton institutionnel.
- **Différence assumée** : TSCM n'est pas un club historique à prestige → on aère davantage, on insiste sur la convivialité et la proximité (ADN du brief).
- **Mobile-first obligatoire** : conception et maquettes à partir de 375px, puis desktop. Les licenciés consultent majoritairement sur mobile.
- **PWA à conserver** : `django-pwa` déjà installé (manifest + icônes 72→512 + theme #2057b2) — ne pas régresser, garder le site installable.
- **Identité** : palette bleu `#2057b2` / or / sable conservée, typos Bebas Neue (display) + DM Sans (body).
- **Composant-first** : décomposer les templates monolithiques (home_page.html = 302 lignes actuellement) en includes réutilisables avant de toucher au design.
- **Admins = bénévoles non techniques avec peu de temps** : le back-office `/gestion/` doit rester ultra-simple (labels en français clair, pas de champs techniques, aide contextuelle, prévisualisation, pas de possibilité de casser le site). Ne jamais exposer l'admin Wagtail brut. Une action courante (publier une actu, ajouter une photo) doit être faisable en moins de 5 minutes.
- **Pas de corpus photo neuf dispo** : les visuels existants sont en basse résolution. Le design doit compenser par la typo, la couleur, les dégradés, les cartes graphiques, les illustrations SVG (raquette, balle, court stylisé). Prévoir une stratégie "low-photo" (voir §9).

## 2. Arborescence cible

```
/                       Home (refondue)
/le-club/               Présentation, valeurs, histoire, équipe dirigeante
/ecole-de-tennis/       Formation, encadrement, stages
/tarifs/                Grille + inscription Tenup
/resultats/             Équipes + Tournoi Open (sync Tenup)
/actualites/            Liste + détail
/galerie/               Albums + lightbox
/partenaires/           NOUVELLE — offres sponsoring
/contact/               Infos + formulaire
```

### Menu principal (avec sous-menus façon TCL)

- **Le Club** : Présentation / Histoire / Bureau & équipe
- **Tennis** : École / Résultats / Tarifs
- **Vie du club** : Actualités / Galerie
- **Partenaires**
- **Contact**

## 3. État de l'existant (code)

- **Stack** : Django + Wagtail (CMS), Tailwind CDN, CKEditor (back-office maison `/gestion/`), django-pwa, intégration API Tenup FFT (sync tournois/rencontres/actus).
- **Apps** : `home`, `club`, `actualites`, `galerie`, `contact`, `gestion`, `search`, `tscmazan`.
- **Éditable via `/gestion/`** : articles, palmarès, albums, pages Wagtail, menu dynamique, paramètres site.
- **Édition live** : 3 champs seulement (hero_titre, hero_sous_titre, presentation_titre) — à étendre.
- **Dette visuelle** : CSS dispersé (base.html inline + `welcome_page.css` legacy), templates longs, Tailwind non bundlé, base_gestion.html avec palette partiellement divergente.

## 4. Lots de livraison

### Lot 0 — Fondation design system

- Extraire Tailwind du CDN vers un build local (tokens centralisés dans `tailwind.config`).
- Variables CSS partagées front + `/gestion/` (palette, spacing, shadows) pour cohérence back-office.
- Bibliothèque de composants Django (`{% include %}`) : `hero.html`, `stat_band.html`, `section_header.html`, `card.html`, `cta_band.html`, `sponsor_card.html`.
- Nettoyer `welcome_page.css` (couleurs obsolètes #308282 / #ea1b10).
- Vérifier que le bundling Tailwind local ne casse pas le service worker PWA.

### Lot 1 — Home refondue (mobile-first)

Ordre des sections :

1. **Hero** : image/visuel fort, titre + sous-titre + 2 CTA (Devenir membre / Découvrir le club). Viewport mobile plein, CTA empilés en mobile.
2. **Bande chiffres clés** : 150+ licenciés, 4 courts, 15+ équipes, 40+ ans FFT, Club Formateur. Grille 2×2 sur mobile, 4 col sur desktop.
3. **Convivialité** — la signature du club, texte fort + visuel.
4. **École de tennis** — teaser + CTA.
5. **Dernières actualités** (3 cards).
6. **Encart Partenaires** — teaser visuel → CTA "Devenir partenaire".
7. **CTA final** — réserver un court Tenup / prendre contact.

Audit Lighthouse PWA à passer après ce lot.

### Lot 2 — Page Partenaires (NOUVELLE)

- Hero "Devenez partenaire du TSCM".
- "Votre soutien sert à…" — 6 puces du brief avec icônes :
  - Mettre à disposition 50+ raquettes école de tennis
  - Nouveau matériel pédagogique et équipements
  - Tenues complètes pour équipes « élite »
  - Déplacements des équipes
  - Rénovation des cours
  - Animations (Loto, Soirée Paella, Journées jeunes, Stages…)
- **4 offres en cards** avec prix + visuel, empilement vertical en mobile :
  - Logo en action (t-shirts ASTON) — **150 €**
  - Tableaux des scores (4 tableaux, ~100 matchs/saison) — **180 €**
  - Logos sur filets (90×60 cm) — **200 € (2 filets) / 250 € (4 filets)**
  - Bâches publicitaires (env. 2×1.5 m) — sur devis
- Bloc **Offre personnalisée** (pied de filet, bâche de filet, panneau score, terrain à l'effigie).
- Bloc **Inclus dans toutes nos offres** : magnet 22×15 cm tableau partenaires extérieur + communication site + réseaux sociaux.
- CTA contact sponsoring.

### Lot 3 — Pages institutionnelles

- **Le Club** : histoire (40+ ans FFT), valeurs, **bureau & équipe pédagogique** (récupération de l'actuelle page Dirigeants), installations (4 courts + mini-tennis + pickleball + club house), citation du président (récupération et retraitement du message actuel).
- **École de tennis** : tranches d'âge, encadrement, stages, inscription.
- **Tarifs** : tableau propre + CTA inscription Tenup.

### Lot 4 — Actualités & Résultats

- **Actualités** : grille + filtre éventuel (maison / Tenup).
- **Article** : sobre, partage, image de une.
- **Résultats** :
  - Sous-rubrique **Équipes** — tableaux par équipe/saison (sync Tenup existante).
  - Sous-rubrique **Tournoi Open** — historique et palmarès (événement clé du club).

### Lot 5 — Galerie & Contact

- **Galerie** : lightbox récente à conserver, rafraîchir cover albums pour cohérence.
- **Contact** : carte + formulaire + infos pratiques (coordonnées officielles) + horaires si disponibles.
- Lien **Shop ASTON** à caser (footer + encart Partenaires).

### Lot 6 — Back-office `/gestion/` (critique — admins = bénévoles)

- Aligner palette et typos sur le front.
- Étendre l'édition live (`data-edit-field`) au-delà des 3 champs actuels.
- Ajouter édition du nouveau contenu Partenaires.
- Simplifier les formulaires : labels en français, aide contextuelle, valeurs par défaut sensées, pas de champs techniques exposés.
- Prévisualisation avant publication sur actus et pages principales.
- Tester chaque parcours courant (publier actu, ajouter photo, modifier tarif, ajouter partenaire) sur un utilisateur non technique → objectif < 5 min.

### Lot 7 — Migration de contenu (en parallèle du Lot 3)

- Récupérer depuis `tscmazan.com` : message du président, palmarès, page Dirigeants, photos potentiellement réutilisables (vérifier résolution).
- Audit des visuels existants → liste des photos à refaire.

### Lot 8 — SEO (transverse, démarre au Lot 1 et se termine au Lot 5)

**Objectif** : faire ressortir le TSCM sur les requêtes locales ("tennis Mazan", "club tennis Vaucluse", "école de tennis Carpentras"…), condition nécessaire pour l'objectif "augmenter la notoriété" du brief.

**On-page** :
- HTML sémantique propre (un seul `<h1>` par page, hiérarchie `h2/h3` cohérente, `<main>`, `<article>`, `<nav>`).
- `<title>` et `<meta description>` uniques par page, éditables depuis `/gestion/` avec valeurs par défaut intelligentes si admin ne remplit pas (Wagtail le fait via `SEO fields` sur `Page`).
- URLs propres (slugs FR, pas de paramètres inutiles) — déjà en partie via Wagtail.
- Alt text obligatoire sur images (mais avec **placeholder par défaut contextualisé** : "Court de tennis du TSCM Mazan" — les bénévoles n'iront pas le renseigner).
- Canonical URLs, `lang="fr"` explicite.
- Interlinking : liens internes entre pages (home → école → tarifs → contact).

**Structured data (Schema.org)** :
- `SportsClub` + `LocalBusiness` sur la home et Contact (adresse, téléphone, horaires, coordonnées GPS).
- `Event` sur le Tournoi Open et les stages.
- `BreadcrumbList` sur les pages profondes.
- `Article` sur les actualités.

**Référencement local** :
- Google Business Profile à créer/mettre à jour (hors-site mais critique — je documente la démarche).
- Cohérence NAP (Name / Address / Phone) exacte sur toutes les pages et annuaires.
- Inscription ligue FFT PACA, annuaires tennis locaux.

**Technique** :
- `sitemap.xml` (Wagtail fournit `wagtail.contrib.sitemaps`) — activer et exposer `/sitemap.xml`.
- `robots.txt` propre.
- Open Graph + Twitter Card sur toutes les pages pour partage réseaux (image de partage par défaut = logo club).
- Performances Lighthouse > 90 sur mobile (mobile-first + Tailwind local + images en renditions Wagtail).
- HTTPS, compression, cache (déjà en place normalement).

**Contenu** :
- Rédaction (par moi) avec mots-clés locaux naturellement intégrés — jamais de bourrage.
- Actualités régulières (signal de fraîcheur) — c'est là que le back-office simplifié devient vital : si les bénévoles n'alimentent pas, le SEO stagne.
- Page dédiée par intention de recherche : `/ecole-de-tennis/`, `/tarifs/`, `/tournoi-open/` (argument fort pour page racine `/open/` plutôt que sous-rubrique).

## 5. Ordre de livraison proposé

`Lot 0 → Lot 1 → Lot 2` en priorité (fondation + impact visible max pour le commanditaire).
Puis Lots 3 à 6 par itérations. Lot 7 en parallèle.
**Lot 8 (SEO) : transverse, démarre dès le Lot 1 — chaque nouveau template intègre directement les bonnes pratiques SEO (sémantique, meta, schema.org). Pas un lot séparé à la fin.**

## 6. Coordonnées officielles (à utiliser partout)

- **Tennis Sporting Club Mazanais**
- Chemin du Bigourd, Site du COSEC, 84380 Mazan
- Tél : 04 90 69 86 45
- Email : tscm@bbox.fr

## 7. Décisions prises

- **Tailwind** : build **local** via Tailwind CLI (binaire, pas de toolchain Node lourde). Sortie compilée dans `/static/css/tailwind.css`, servie via `collectstatic`. Fin du CDN.
- **Wagtail** : **on conserve**. Coût de sortie disproportionné (tous les modèles héritent de `Page`, URLs, search Wagtail). En contrepartie, on s'en sert mieux :
  - Exploiter `StreamField` pour les sections composables (home, page Partenaires) — mais **4-6 blocs max** par page, avec libellés FR clairs.
  - Utiliser Wagtail Images + renditions pour l'image responsive (critique mobile-first).
  - Avant de créer un modèle/pattern custom dans `/gestion/`, vérifier que Wagtail ne le fait pas déjà — éviter de dupliquer l'admin.
  - **Ne jamais exposer l'admin Wagtail aux admins du site** — tout passe par `/gestion/` simplifié.
- **Admins = bénévoles peu tech** : back-office `/gestion/` pensé pour être utilisable en < 5 min par action courante, sans formation. Labels FR, aide contextuelle, prévisualisation.
- **Pas de corpus photo neuf** : direction "low-photo" (voir §9).
- **Rédaction des textes** : je produis le contenu éditorial (accroches, présentations, textes de sections, CTA, page Partenaires…). Le bureau / président relira et ajustera depuis `/gestion/`. Ton : institutionnel chaleureux, aéré, phrases courtes, signature "Convivialité".
- **SEO local comme objectif transverse** : le club veut augmenter sa notoriété → on vise les requêtes type "tennis Mazan", "tennis Vaucluse", "club de tennis 84380", "école de tennis Mazan", "cours de tennis Carpentras". Techniques mises en œuvre détaillées au Lot 8.

## 8. Questions à trancher avant le Lot 0

1. **Logo Club Formateur FFT** : dispo en SVG / PNG haute définition ?
2. **Sponsoring — "Offre personnalisée"** : formulaire dédié, ou simple `mailto:tscm@bbox.fr` ?
3. **Périmètre restaurant / salles** : ignoré (le TCL a ces sections, pas le TSCM). À confirmer.
4. **Tournoi Open** : sous-rubrique de `/resultats/` ou page racine `/open/` dédiée ?
5. **Shop ASTON** : visibilité souhaitée — footer + page Partenaires uniquement, ou aussi en CTA home ?

## 9. Stratégie design "low-photo"

Pas de corpus photo neuf dispo, visuels actuels en basse résolution. Le design compense par :

- **Typographie forte** : gros titres Bebas Neue, traitements éditoriaux soignés (citations, chiffres XXL).
- **Palette riche** : variations du bleu #2057b2 en dégradés, or doré en accent, sable en respiration.
- **Cartes graphiques & blocs colorés** : chaque section a une identité chromatique, pas besoin de photo pour porter le sens.
- **Illustrations SVG** : raquette, balle, court vu de dessus, filet stylisé, trophée — utilisés en motifs de fond, en icônes de section, en éléments décoratifs. Cohérent, léger, infini scalable.
- **Photos en accents** : quand une photo est utilisée, elle est **recadrée serrée**, **masquée** (forme circulaire, triangulaire, écran split) ou **traitée** (duotone bleu/sable, noir et blanc + accent or). Jamais de photo pleine largeur basse déf qui pixelise.
- **Hero home** : pas de photo pleine page ; plutôt composition graphique (titre massif + dégradé + illustration SVG + photo masquée en accent).
- **Cards actus/galerie** : si la photo est faible, utiliser un crop carré + filtre, ou un fond coloré uni si pas d'image.
- **Long terme** : une fois le site en place, proposer au bureau un shooting simple (un samedi avec un bénévole photographe amateur) pour alimenter progressivement la bibliothèque.

## Annexes

- **Brief source** : `TSCM MAZAN.docx` (racine du projet)
- **Référence visuelle** : https://www.tennisclublyon.com/
- **Site actuel** : https://www.tscmazan.com/
