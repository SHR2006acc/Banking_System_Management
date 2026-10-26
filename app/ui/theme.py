"""Charte graphique de l'interface (Rôle 3) — LE système de design.

Règle d'or du projet : ce fichier est le SEUL autorisé à contenir des
valeurs hexadécimales. Toutes les autres couches importent les jetons
définis ici (couleurs, police, helpers) : une seule source de vérité
garantit une interface cohérente sur tous les écrans.

Direction artistique — « flat institutionnel » :
  * aucun dégradé, aucun arrondi : des aplats, des filets de 1 px ;
  * le bleu marine porte la marque ; vert / rouge / ambre ne servent
    QU'À signaler un sens (crédit, débit, état, alerte) ;
  * la hiérarchie vient de la typographie et de l'espacement,
    jamais de la décoration.

Plan du fichier :
  1. Jetons de couleur (constantes)
  2. Police : détection de famille + helper ``police()``
  3. ``appliquer_theme()`` : polices nommées puis feuille de styles
  4. Helpers tolérants ``_configurer`` / ``_mapper`` : certaines options
     ttk n'existent que sur les Tk récents ; on les ignore proprement
     plutôt que de planter au démarrage.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# ---------------------------------------------------------------------- #
# 1. Jetons de couleur                                                     #
# ---------------------------------------------------------------------- #
# Textes
INK = "#0E1B2C"          # texte principal
INK_SOFT = "#55657A"     # texte secondaire (libellés de formulaire…)
MUTED = "#6E7F92"        # légendes, textes discrets
# Fonds
BG = "#F3F5F7"           # fond applicatif (gris très clair)
SURFACE = "#FFFFFF"      # cartes, tableaux, en-têtes
SURFACE_ALT = "#FAFBFC"  # ligne « zébrée » d'un tableau
SURVOL = "#F1F5F9"       # survol d'une ligne de tableau
# Bordures
LINE = "#E3E8EE"         # filet 1 px (cartes, séparateurs)
LINE_STR = "#CBD4DE"     # bordure de champ de saisie
# Marque (bleu institutionnel)
NAVY = "#123C6B"
NAVY_HOVER = "#0E3058"
NAVY_PRESSED = "#0A2545"
NAVY_DEEP = "#0F2743"    # fond de la barre latérale
NAVY_ITEM = "#16375B"    # survol / actif dans la barre latérale
NAVY_TINT = "#E9F0F7"    # teinte claire (sélection, bannières)
NAVY_TINT_PRESSED = "#DCE7F3"
# Sémantique
POS = "#12703C"          # crédit, succès
POS_HOVER = "#0D5A30"
POS_PRESSED = "#0A4A28"
POS_TINT = "#E7F4EC"
NEG = "#B3261E"          # débit, danger
NEG_HOVER = "#941E17"
NEG_PRESSED = "#7E1913"
NEG_TINT = "#FBEAE9"
WARN = "#8A5A00"         # avertissement, compte suspendu
WARN_TINT = "#FCF3E3"
# États techniques
DESACTIVE = "#9FB3C8"    # bouton principal désactivé
SURFACE_NEUTRE = "#EAEEF3"  # fond bouton secondaire
SURFACE_NEUTRE_HOVER = "#E0E6ED"
SURFACE_NEUTRE_PRESSED = "#D6DEE8"
BADGE_NEUTRE_TINT = "#EEF1F4"
FOCUS = "#1E66C9"        # anneau de focus clavier
# Barre latérale
TEXTE_SIDEBAR = "#B7C6D6"    # item inactif
TITRE_SIDEBAR = "#7A93AC"    # étiquette de section

# ---------------------------------------------------------------------- #
# 2. Police                                                                #
# ---------------------------------------------------------------------- #
FAMILLES = ("Segoe UI", "Inter", "Noto Sans", "Cantarell",
            "Liberation Sans", "Ubuntu", "DejaVu Sans")
_FAMILLE: str = "DejaVu Sans"   # remplacée par appliquer_theme()


def detecter_famille(root: tk.Misc) -> str:
    """Première famille installée dans ``FAMILLES`` (sinon DejaVu Sans).

    Windows -> « Segoe UI », KDE -> « Noto Sans » / « Cantarell », sinon
    « Liberation Sans » / « DejaVu Sans » : la même base de code reste
    native partout.

    Comparaison INSENSIBLE à la casse : Tk renvoie les familles en
    minuscules sur X11 (« liberation sans ») alors que la charte les
    écrit en capitales — sans cette tolérance, la détection échoue et
    Tk retombe sur son affreuse police bitmap « fixed ».
    """
    installees = {famille.lower() for famille in tkfont.families(root)}
    for famille in FAMILLES:
        if famille.lower() in installees:
            return famille
    return "DejaVu Sans"


def police(taille: int = 11, gras: bool = False) -> tuple:
    """Descripteur de police prêt à l'emploi : ``police(12, gras=True)``.

    Utilisé par les composants tk (Label, Canvas…) qui n'ont pas de
    style ttk et doivent tout de même respecter la charte.
    """
    return (_FAMILLE, taille, "bold" if gras else "normal")


# ---------------------------------------------------------------------- #
# 3. Feuille de styles                                                     #
# ---------------------------------------------------------------------- #
def _configurer(style: ttk.Style, nom: str, **options) -> None:
    """``style.configure`` tolérant : une option inconnue de ce Tk est
    ignorée au lieu de faire échouer le démarrage."""
    for option, valeur in options.items():
        try:
            style.configure(nom, **{option: valeur})
        except tk.TclError:
            pass


def _mapper(style: ttk.Style, nom: str, **options) -> None:
    """``style.map`` tolérant (mêmes raisons que ``_configurer``)."""
    for option, valeur in options.items():
        try:
            style.map(nom, **{option: valeur})
        except tk.TclError:
            pass


def _bouton_plein(style: ttk.Style, nom: str, fond: str, survol: str,
                  presse: str, desactive: str) -> None:
    """Bouton « plein » : fond coloré, texte blanc, 3 états visibles."""
    _configurer(style, nom, background=fond, foreground=SURFACE,
                borderwidth=0, focuscolor=fond, padding=(16, 8))
    _mapper(style, nom,
            background=[("pressed", presse), ("active", survol),
                        ("disabled", desactive)],
            foreground=[("disabled", "#E8EEF4")])


def appliquer_theme(root: tk.Misc) -> ttk.Style:
    """Applique la charte complète et renvoie l'objet ``ttk.Style``.

    À appeler UNE fois, juste après la création de la fenêtre racine et
    AVANT de construire les widgets.
    """
    global _FAMILLE
    _FAMILLE = detecter_famille(root)

    # -- polices nommées : tout widget ttk hérite de ces réglages --------
    for nom in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
        tkfont.nametofont(nom).configure(family=_FAMILLE, size=11)
    tkfont.nametofont("TkHeadingFont").configure(
        family=_FAMILLE, size=11, weight="bold")

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass    # moteur clam absent (platelage rare) : thème natif conservé

    # -- racine : valeurs par défaut de TOUS les styles ------------------
    _configurer(style, ".", font=police(11), background=BG, foreground=INK)

    # -- textes -----------------------------------------------------------
    _configurer(style, "Titre.TLabel", font=police(16, True),
                foreground=NAVY, background=BG)
    _configurer(style, "Champ.TLabel", foreground=INK_SOFT, background=BG)
    _configurer(style, "SousTitre.TLabel", font=police(11),
                foreground=INK_SOFT, background=BG)
    _configurer(style, "Indicateur.TLabel", font=police(24, True),
                foreground=INK, background=SURFACE)
    _configurer(style, "CarteTitre.TLabel", font=police(10, True),
                foreground=MUTED, background=SURFACE)
    _configurer(style, "Vide.TLabel", font=police(11),
                foreground=MUTED, background=SURFACE)

    # -- cartes (panneaux blancs posés sur le fond gris) ------------------
    _configurer(style, "Carte.TLabelframe", background=SURFACE,
                borderwidth=1, relief="solid", bordercolor=LINE)
    _configurer(style, "Carte.TLabelframe.Label", font=police(12, True),
                foreground=NAVY, background=SURFACE)
    _configurer(style, "Carte.TFrame", background=SURFACE)
    _configurer(style, "Carte.TLabel", background=SURFACE)
    _configurer(style, "Carte.TCheckbutton", background=SURFACE)

    # -- formulaires -------------------------------------------------------
    _configurer(style, "Formulaire.TLabel", foreground=INK_SOFT,
                background=SURFACE)
    _configurer(style, "Formulaire.TEntry", fieldbackground=SURFACE)
    _configurer(style, "Formulaire.TCombobox", fieldbackground=SURFACE)

    # -- champs de saisie : filet 1 px + anneau de focus bleu --------------
    _configurer(style, "TEntry", fieldbackground=SURFACE, foreground=INK,
                insertcolor=INK, padding=(8, 6),
                bordercolor=LINE_STR, lightcolor=LINE_STR,
                darkcolor=LINE_STR)
    _mapper(style, "TEntry",
            bordercolor=[("focus", FOCUS)],
            lightcolor=[("focus", FOCUS)],
            darkcolor=[("focus", FOCUS)])
    _configurer(style, "TCombobox", fieldbackground=SURFACE,
                foreground=INK, padding=(8, 4), arrowsize=14,
                bordercolor=LINE_STR, lightcolor=LINE_STR,
                darkcolor=LINE_STR)
    _mapper(style, "TCombobox",
            fieldbackground=[("readonly", SURFACE)],
            foreground=[("readonly", INK)],
            bordercolor=[("focus", FOCUS)])
    # La liste déroulante d'un Combobox est une ListBox Tk classique :
    # elle ignore les styles ttk, seul l'option_add la contrôle.
    for motif, valeur in (
        ("*TCombobox*Listbox.background", SURFACE),
        ("*TCombobox*Listbox.foreground", INK),
        ("*TCombobox*Listbox.selectBackground", NAVY),
        ("*TCombobox*Listbox.selectForeground", SURFACE),
        ("*TCombobox*Listbox.selectBorderWidth", 0),
        ("*TCombobox*Listbox.font", "TkDefaultFont"),
    ):
        root.option_add(motif, valeur)

    # -- boutons ------------------------------------------------------------
    _configurer(style, "TButton", padding=(14, 7), font=police(11))
    _bouton_plein(style, "Primaire.TButton", NAVY, NAVY_HOVER,
                  NAVY_PRESSED, DESACTIVE)
    # « Action » : ancien nom conservé pour les écrans existants.
    _bouton_plein(style, "Action.TButton", NAVY, NAVY_HOVER,
                  NAVY_PRESSED, DESACTIVE)
    _bouton_plein(style, "Succes.TButton", POS, POS_HOVER,
                  POS_PRESSED, "#A9C8B4")
    _bouton_plein(style, "Danger.TButton", NEG, NEG_HOVER,
                  NEG_PRESSED, "#DDA9A5")
    _configurer(style, "Secondaire.TButton", background=SURFACE_NEUTRE,
                foreground=INK, borderwidth=0, focuscolor=SURFACE_NEUTRE,
                padding=(14, 8))
    _mapper(style, "Secondaire.TButton",
            background=[("pressed", SURFACE_NEUTRE_PRESSED),
                        ("active", SURFACE_NEUTRE_HOVER),
                        ("disabled", "#F1F3F6")],
            foreground=[("disabled", MUTED)])
    _configurer(style, "Lien.TButton", background=SURFACE,
                foreground=NAVY, borderwidth=0, focuscolor=SURFACE,
                padding=(10, 6))
    _mapper(style, "Lien.TButton",
            background=[("pressed", NAVY_TINT_PRESSED),
                        ("active", NAVY_TINT)])

    # -- badges d'état (étiquette teintée, coins francs) --------------------
    for nom, avant, fond in (
        ("BadgeActif.TLabel", POS, POS_TINT),
        ("BadgeSuspendu.TLabel", WARN, WARN_TINT),
        ("BadgeCloture.TLabel", INK_SOFT, BADGE_NEUTRE_TINT),
        ("BadgeNeutre.TLabel", NAVY, NAVY_TINT),
        ("BadgeDanger.TLabel", NEG, NEG_TINT),
    ):
        _configurer(style, nom, foreground=avant, background=fond,
                    font=police(10, True), padding=(9, 4))

    # -- tableaux (Treeview) --------------------------------------------------
    _configurer(style, "Treeview", rowheight=32, font=police(11),
                background=SURFACE, fieldbackground=SURFACE,
                foreground=INK, borderwidth=0)
    _configurer(style, "Treeview.Heading", font=police(10, True),
                background=SURFACE, foreground=INK_SOFT,
                relief="flat", padding=(8, 6), borderwidth=0)
    # Sans cette carte de sélection, clam applique son bleu par défaut —
    # c'est CE réglage qui rend les tableaux « haut de gamme ».
    _mapper(style, "Treeview",
            background=[("selected", NAVY_TINT)],
            foreground=[("selected", INK)])
    _mapper(style, "Treeview.Heading",
            background=[("active", SURVOL)])

    # -- barres de défilement ---------------------------------------------------
    _configurer(style, "Vertical.TScrollbar", troughcolor=BG,
                background=LINE_STR, bordercolor=BG, relief="flat",
                arrowsize=12)
    _mapper(style, "Vertical.TScrollbar",
            background=[("active", MUTED)])

    # -- séparateur ---------------------------------------------------------------
    _configurer(style, "TSeparator", background=LINE)

    # -- onglets (héritage : encore utilisés tant que le shell n'est pas en place)
    _configurer(style, "TNotebook", background=BG, borderwidth=0)
    _configurer(style, "TNotebook.Tab", padding=(16, 8), font=police(11))
    _mapper(style, "TNotebook.Tab",
            background=[("selected", SURFACE)],
            foreground=[("selected", NAVY)])

    return style
