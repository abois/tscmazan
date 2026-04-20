import re
from datetime import datetime

from django import template
from django.utils.dates import MONTHS
from django.utils.safestring import mark_safe

register = template.Library()

# Mots gardés en minuscules dans les noms de clubs/villes (typographie française)
_MINOR_WORDS = {
    "de", "du", "des", "d",
    "la", "le", "les", "l",
    "et", "aux", "au", "à", "a",
    "sur", "sous", "en", "sous",
}


@register.filter
def titlecase_fr(value):
    """Met en Title Case un nom de club/ville, en gardant de/du/la/… en minuscule.

    Exemples :
        TENNIS CLUB DE ST ETIENNE DU GRES 2 → Tennis Club de St Etienne du Gres 2
        A.S. BEDARRIDES 2 → A.S. Bedarrides 2
    """
    if not value:
        return value
    # On passe d'abord tout en minuscules puis on capitalise mot par mot
    tokens = re.split(r"(\s+|-)", value.lower())
    out = []
    seen_first_word = False
    for tok in tokens:
        if not tok or tok.isspace() or tok == "-":
            out.append(tok)
            continue
        # Préserve les tokens avec points (A.S., F.C. …) : uppercase
        if "." in tok and len(tok) <= 6:
            out.append(tok.upper())
            seen_first_word = True
            continue
        # Chiffres seuls
        if tok.isdigit():
            out.append(tok)
            continue
        stripped = tok.strip("'’")
        if seen_first_word and stripped in _MINOR_WORDS:
            out.append(tok)
        else:
            out.append(tok[:1].upper() + tok[1:])
        seen_first_word = True
    return "".join(out)


DATE_TOUR_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\s*[—–-]\s*(.*)$")


@register.filter
def split_date_tour(value):
    """Parse '2026-03-15 — PHASE PRELIMINAIRE (POULE J)' en dict date/tour.

    Retourne un dict {date, tour} — date formatée « 15 mars », tour en casse
    normale avec capitale initiale. Si le format ne matche pas, retourne
    {date: '', tour: value}.
    """
    if not value:
        return {"date": "", "tour": ""}
    match = DATE_TOUR_RE.match(value.strip())
    if not match:
        return {"date": "", "tour": _capfirst_fr(value)}
    year, month, day, tour = match.groups()
    try:
        dt = datetime(int(year), int(month), int(day))
        # Formatage "15 mars"
        date_str = f"{dt.day} {MONTHS[dt.month]}"
    except ValueError:
        date_str = f"{day}/{month}/{year}"
    return {"date": date_str, "tour": _capfirst_fr(tour.strip())}


# Correctifs d'accents pour les exports Tenup (qui suppriment les accents)
_ACCENT_FIXES = {
    r"\bpreliminaire\b": "préliminaire",
    r"\bpreliminaires\b": "préliminaires",
    r"\bdepartemental\b": "départemental",
    r"\bdepartementale\b": "départementale",
    r"\bregional\b": "régional",
    r"\bregionale\b": "régionale",
    r"\bdeuxieme\b": "deuxième",
    r"\bpremiere\b": "première",
    r"\btroisieme\b": "troisième",
    r"\bfinale\b": "finale",  # déjà ok, placeholder
    r"\bdemi finale\b": "demi-finale",
    r"\bdemi finales\b": "demi-finales",
    r"\bquart de finale\b": "quart de finale",
    r"\bequipe\b": "équipe",
    r"\bequipes\b": "équipes",
}


def _apply_accent_fixes(value):
    for pattern, replacement in _ACCENT_FIXES.items():
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    return value


def _capfirst_fr(value):
    """Capitalise la première lettre, passe le reste en minuscule, remet les
    parenthèses type « (Poule J) » en casse propre."""
    if not value:
        return value
    s = _apply_accent_fixes(value.lower())
    # Capitalise la première lettre
    s = s[:1].upper() + s[1:]
    # Capitalise les mots dans les parenthèses (poule j → Poule J)
    def _paren(match):
        inner = match.group(1)
        return "(" + " ".join(
            w.upper() if len(w) <= 2 else w[:1].upper() + w[1:]
            for w in inner.split()
        ) + ")"
    s = re.sub(r"\(([^)]+)\)", _paren, s)
    return s
