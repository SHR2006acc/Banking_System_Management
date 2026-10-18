"""Composants de retour utilisateur : modales et notifications.

Remplacent avantageusement ``messagebox`` (fenêtre native, hors charte
et bloquante sans contrôle) :

  * ``Modale``              : fenêtre modale centrée, Échap pour fermer ;
  * ``ConfirmationModale``  : question Confirmer/Annuler -> ``bool`` ;
  * ``afficher_toast``      : notification non bloquante en bas à
    droite, qui disparaît seule après quelques secondes.
"""
from __future__ import annotations

import tkinter as tk

from app.ui import theme as T
from app.ui.utilitaires import lier_recursif


class Modale(tk.Toplevel):
    """Base des fenêtres modales de la charte.

    * ``transient``  : la fenêtre reste au-dessus de sa mère ;
    * ``grab_set``   : les clics sur la mère sont bloqués (modalité) ;
    * ``Échap``, ✕, ou fermeture système -> ``fermer()``.

    Cycle de vie type ::

        boite = MaModale(parent, ...)   # construite, encore invisible
        boite.afficher()                # centrée, visible, focus
        boite.attendre()                # bloque jusqu'à fermeture
        resultat = boite.resultat
    """

    def __init__(self, parent, titre: str) -> None:
        super().__init__(parent)
        self.withdraw()                 # construite cachée : zéro clignotement
        self.title(titre)
        self.configure(bg=T.SURFACE, highlightthickness=1,
                       highlightbackground=T.LINE)
        self.resizable(False, False)
        self._mere = parent.winfo_toplevel()
        self.transient(self._mere)
        self.resultat = None

        entete = tk.Frame(self, bg=T.SURFACE)
        entete.pack(fill="x", padx=18, pady=(14, 0))
        tk.Label(entete, text=titre, bg=T.SURFACE, fg=T.NAVY,
                 font=T.police(13, True)).pack(side="left")
        fermer = tk.Label(entete, text="✕", bg=T.SURFACE, fg=T.MUTED,
                          font=T.police(12), cursor="hand2")
        fermer.pack(side="right")
        fermer.bind("<Button-1>", lambda _e: self.fermer())
        tk.Frame(self, bg=T.LINE, height=1).pack(fill="x", padx=18, pady=(10, 0))

        self.corps = tk.Frame(self, bg=T.SURFACE)
        self.corps.pack(fill="both", expand=True, padx=18, pady=(12, 0))
        self.pied = tk.Frame(self, bg=T.SURFACE)
        self.pied.pack(fill="x", padx=18, pady=(16, 14))

        self.protocol("WM_DELETE_WINDOW", self.fermer)
        self.bind("<Escape>", lambda _e: self.fermer())

    # ------------------------------------------------------------------ #
    #  Cycle de vie                                                       #
    # ------------------------------------------------------------------ #
    def afficher(self, largeur: int | None = None) -> None:
        """Centre sur la fenêtre mère, rend visible et prend le focus."""
        self.update_idletasks()
        if largeur:
            self.geometry(f"{largeur}x{self.winfo_reqheight()}")
            self.update_idletasks()
        x = self._mere.winfo_rootx() + (self._mere.winfo_width()
                                        - self.winfo_reqwidth()) // 2
        y = self._mere.winfo_rooty() + (self._mere.winfo_height()
                                        - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.deiconify()
        # Prise de focus DIFFÉRÉE : on n'utilise pas wait_visibility(),
        # qui peut bloquer si le gestionnaire de fenêtres tarde à afficher
        # la fenêtre (session verrouillée, machine chargée…). Le rappel
        # part 40 ms plus tard, sans jamais figer l'appelant.
        self.after(40, self._prendre_focus)

    def _prendre_focus(self) -> None:
        """Pose le grab modal et le focus, en tolérant les refus du WM."""
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def attendre(self) -> None:
        """Bloque l'appelant jusqu'à la fermeture (comme ``wait_window``)."""
        self.wait_window()

    def fermer(self) -> None:
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()


class ConfirmationModale(Modale):
    """Question modale « Confirmer / Annuler » -> ``True`` / ``False``.

    Utilisation en une ligne ::

        if ConfirmationModale.demander(
                self, "Clôture",
                "Clôturer définitivement CPT-0004 ?",
                texte_confirmer="Clôturer"):
            ...
    """

    def __init__(self, parent, titre: str, message: str,
                 texte_confirmer: str = "Confirmer", danger: bool = True) -> None:
        super().__init__(parent, titre)
        tk.Label(self.corps, text=message, bg=T.SURFACE, fg=T.INK,
                 font=T.police(11), justify="left", anchor="w",
                 wraplength=400).pack(fill="x")

        from tkinter import ttk
        ttk.Button(self.pied, text="Annuler", style="Secondaire.TButton",
                   command=lambda: self._conclure(False)
                   ).pack(side="right", padx=(8, 0))
        style = "Danger.TButton" if danger else "Primaire.TButton"
        ttk.Button(self.pied, text=texte_confirmer, style=style,
                   command=lambda: self._conclure(True)).pack(side="right")
        self.bind("<Return>", lambda _e: self._conclure(True))

    def _conclure(self, valeur: bool) -> None:
        self.resultat = valeur
        self.fermer()

    @classmethod
    def demander(cls, parent, titre: str, message: str,
                 texte_confirmer: str = "Confirmer",
                 danger: bool = True) -> bool:
        boite = cls(parent, titre, message, texte_confirmer, danger)
        boite.afficher()
        boite.attendre()
        return bool(boite.resultat)


# ---------------------------------------------------------------------- #
#  Notifications « toast »                                                #
# ---------------------------------------------------------------------- #
_TOASTS: dict[str, list[tk.Toplevel]] = {}
_DUREE_MS = 3600


def afficher_toast(parent, message: str, ton: str = "succes",
                   duree: int = _DUREE_MS) -> None:
    """Notification non bloquante, en bas à droite de la fenêtre.

    Tons : ``succes`` (vert), ``erreur`` (rouge), ``info`` (bleu),
    ``avertissement`` (ambre). Un clic ferme immédiatement.
    """
    accent, fond = {
        "succes": (T.POS, T.POS_TINT),
        "erreur": (T.NEG, T.NEG_TINT),
        "info": (T.NAVY, T.NAVY_TINT),
        "avertissement": (T.WARN, T.WARN_TINT),
    }.get(ton, (T.NAVY, T.NAVY_TINT))

    racine = parent.winfo_toplevel()
    cle = str(racine)
    fenetre = tk.Toplevel(racine)
    fenetre.withdraw()
    fenetre.overrideredirect(True)      # aucune décoration système
    fenetre.configure(bg=T.LINE)        # sert de filet 1 px autour
    cadre = tk.Frame(fenetre, bg=fond)
    cadre.pack(fill="both", expand=True, padx=1, pady=1)
    tk.Frame(cadre, bg=accent, width=3).pack(side="left", fill="y")
    tk.Label(cadre, text=message, bg=fond, fg=T.INK, font=T.police(11),
             justify="left", anchor="w", wraplength=330,
             padx=12, pady=10).pack(side="left", fill="both")

    def fermer(_event=None) -> None:
        try:
            fenetre.destroy()
        except tk.TclError:
            pass
        _TOASTS[cle] = [f for f in _TOASTS.get(cle, [])
                        if f.winfo_exists()]

    # Clic n'importe où sur le toast = fermeture immédiate.
    lier_recursif(fenetre, "<Button-1>", fermer)

    # Empilement vertical : chaque nouveau toast se pose au-dessus
    # des précédents encore visibles.
    fenetre.update_idletasks()
    pile = [f for f in _TOASTS.get(cle, []) if f.winfo_exists()]
    _TOASTS[cle] = pile + [fenetre]
    decalage = sum(f.winfo_reqheight() + 8 for f in pile)

    x = racine.winfo_rootx() + racine.winfo_width() \
        - fenetre.winfo_reqwidth() - 22
    y = racine.winfo_rooty() + racine.winfo_height() \
        - fenetre.winfo_reqheight() - 52 - decalage
    fenetre.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    fenetre.deiconify()
    try:
        fenetre.attributes("-topmost", True)
    except tk.TclError:
        pass
    fenetre.after(duree, fermer)
