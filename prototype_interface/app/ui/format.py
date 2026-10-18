"""Formatage partagé de la couche interface (Rôle 3).

Un seul endroit définit comment un montant, une date ou un entier
s'affichent — et comment un montant saisi est relu. Toutes les vues et
tous les composants importent d'ici : cohérence garantie.

Conventions d'affichage (françaises, sans limite de taille) :
    1 234 567,89 €      espace = milliers, virgule = décimale
    18/10/2026 14:32    les dates de la base converties

Grammaire de saisie acceptée par ``extraire_montant`` (tolérante mais
sans ambiguïté dangereuse) :
    1 250,50            français standard ;
    1250.5              point décimal (habitudes pavé numérique) ;
    1000000             nombre brut, sans séparateur ;
    1.000               point seul suivi de 3 chiffres -> milliers ;
    1.000.000           points seuls multiples -> milliers ;
    1.000.000,50        les deux : le séparateur le PLUS À DROITE est
    1,000,000.50        la décimale, l'autre est ignoré (milliers) ;
    1 234 €             suffixe € toléré, espaces de toute sorte ignorés.
Toute saisie ambiguë (ex. « 12,34,56 ») ou non numérique est refusée
avec un message français prêt à afficher.
"""
from __future__ import annotations

import re

from app.services.exceptions import EntreeInvalideError

# Nombre « propre » après normalisation : 1234 ou 1234.56 (ou .5).
_MOTIF_VALIDE = re.compile(r"\d+(\.\d+)?|\.\d+")

_EXEMPLES = "Exemples acceptés : 1 250,50 — 1 234 567,89 €"

# Espaces à ignorer dans une saisie : normale, insécable, fine insécable,
# fine — les copier-coller depuis un document en contiennent souvent.
_ESPACES = (" ", "\u00a0", "\u202f", "\u2009")


def fmt_montant(valeur: float | int | None) -> str:
    """``1500.0`` -> ``« 1 500,00 € »`` ; ``1234567.89`` ->
    ``« 1 234 567,89 € »`` (aucune limite de taille)."""
    try:
        nombre = float(valeur or 0)
    except (TypeError, ValueError):
        nombre = 0.0
    return (f"{nombre:,.2f}".replace(",", " ").replace(".", ",") + " €")


def fmt_entier(valeur: float | int | None) -> str:
    """``1234`` -> ``« 1 234 »`` (sans décimale ni devise)."""
    try:
        return f"{int(valeur or 0):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def fmt_date(texte: str | None) -> str:
    """``« 2026-10-18 14:32:05 »`` -> ``« 18/10/2026 14:32 »``.

    Tolérant : ``« — »`` si absent, texte brut si le format stocké
    n'est pas reconnu.
    """
    if not texte:
        return "—"
    brut = str(texte)
    date, _, heure = brut.partition(" ")
    morceaux = date.split("-")
    if len(morceaux) != 3:
        return brut
    annee, mois, jour = morceaux
    affichage = f"{jour}/{mois}/{annee}"
    if heure:
        affichage += f" {heure[:5]}"
    return affichage


def extraire_montant(texte: str, zero_autorise: bool = False) -> float:
    """Relit un montant saisi « à la main » et le valide (> 0).

    ``zero_autorise=True`` accepte en plus la valeur 0 (soldes initiaux
    d'un compte) ; par défaut, zéro est refusé.

    Lève ``EntreeInvalideError`` (message français, prêt à afficher)
    au lieu de laisser fuiter l'erreur technique de ``float()``.
    La grammaire complète est décrite dans l'en-tête du module.
    """
    # 1. Nettoyage : devise et espaces de toute sorte disparaissent.
    brut = str(texte or "").replace("€", "")
    for espace in _ESPACES:
        brut = brut.replace(espace, "")
    propre = brut.strip()
    if not propre:
        raise EntreeInvalideError("Saisissez un montant.")

    # 2. Normalisation des séparateurs décimaux / de milliers.
    if "," in propre and "." in propre:
        # Les deux séparateurs présents : le plus À DROITE est la
        # décimale ; l'autre est un séparateur de milliers à retirer.
        if propre.rfind(",") > propre.rfind("."):
            propre = propre.replace(".", "").replace(",", ".")
        else:
            propre = propre.replace(",", "")
    elif "," in propre:
        morceaux = propre.split(",")
        if len(morceaux) > 2:
            # « 1,000,000 » : milliers à l'anglaise — accepté seulement
            # si chaque groupe fait exactement 3 chiffres.
            if any(len(m) != 3 or not m.isdigit() for m in morceaux[1:]):
                raise EntreeInvalideError(
                    f"Montant invalide : « {texte} ». {_EXEMPLES}")
            propre = "".join(morceaux)
        else:
            entier, _, decimale = propre.partition(",")
            propre = f"{entier}.{decimale}"
    elif "." in propre:
        morceaux = propre.split(".")
        if len(morceaux) > 2:
            if any(len(m) != 3 or not m.isdigit() for m in morceaux[1:]):
                raise EntreeInvalideError(
                    f"Montant invalide : « {texte} ». {_EXEMPLES}")
            propre = "".join(morceaux)
        else:
            entier, _, decimale = propre.partition(".")
            if (len(decimale) == 3 and entier.isdigit()
                    and entier.lstrip("0")):
                # « 1.000 » / « 12.500 » : point de milliers.
                # (mais « 0.500 » reste 0,5 : le zéro de tête tranche)
                propre = entier + decimale
            else:
                propre = f"{entier}.{decimale}"

    # 3. Validation stricte puis conversion.
    if not _MOTIF_VALIDE.fullmatch(propre):
        raise EntreeInvalideError(
            f"Montant invalide : « {texte} ». {_EXEMPLES}")
    valeur = float(propre)
    if valeur < 0 or (valeur == 0 and not zero_autorise):
        raise EntreeInvalideError(
            "Le montant ne peut pas être négatif." if zero_autorise
            else "Le montant doit être strictement positif.")
    return valeur
