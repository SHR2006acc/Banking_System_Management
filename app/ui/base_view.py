"""Socle des vues (Rôle 3) : bus d'événements + classe mère + outils.

``BusRafraichissement`` : pattern observé/observateur minimal — après
une modification, toutes les vues se re-synchronisent (le dashboard
recalcule ses stats, les listes se rechargent, la barre d'état du shell
met à jour ses compteurs).

``VueBase`` : classe mère de tous les écrans. Le constructeur reçoit le
service (couche métier), le bus d'événements et la session (rôle +
client éventuel) — jamais de SQL, jamais d'accès direct à la base
depuis une vue.
"""
from __future__ import annotations

from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.services.exceptions import ErreurMetier, EntreeInvalideError
from app.services.bank_service import BankService

if TYPE_CHECKING:  # import uniquement pour les annotations (pas de cycle)
    from app.ui.session import Session

# Ré-export : les vues existantes importent ``fmt_montant`` depuis ce
# module ; l'implémentation vit désormais dans ``app.ui.format``.
from app.ui.format import fmt_montant  # noqa: F401  (ré-export volontaire)


@runtime_checkable
class Rafraichissable(Protocol):
    """Tout objet capable de se re-synchroniser sur l'état de la base.

    Les vues (VueBase) et le shell (barre d'état) l'implémentent : le
    bus ne connaît que ce contrat, pas les classes concrètes.
    """

    def rafraichir(self) -> None: ...


class BusRafraichissement:
    """Distribue « la base a changé » aux abonnés (vues + shell)."""

    def __init__(self) -> None:
        self._abonnes: list[Rafraichissable] = []

    def abonner(self, abonne: Rafraichissable) -> None:
        self._abonnes.append(abonne)

    def publier(self) -> None:
        """Appelé après CHAQUE modification réussie de la base."""
        for abonne in self._abonnes:
            abonne.rafraichir()

    def reinitialiser(self) -> None:
        """Vide la liste des abonnés (changement de session).

        Les vues détruites lors d'une bascule Admin <-> Client ne
        doivent plus être appelées : le shell purge le bus puis s'y
        ré-abonne, et les nouvelles vues s'abonnent à leur création.
        """
        self._abonnes.clear()


class VueBase(ttk.Frame):
    """Classe mère des écrans. Injecte service + bus.

    Attributs de classe à spécialiser :
      * ``titre_onglet`` : libellé (héritage Notebook, anciens écrans) ;
      * ``titre_page``   : titre affiché dans l'en-tête du shell ;
      * ``sous_titre``   : phrase d'aide sous le titre (optionnelle).
    """

    titre_onglet = ""
    titre_page = ""
    sous_titre = ""

    def __init__(self, parent, service: BankService,
                 bus: BusRafraichissement,
                 session: Session | None = None) -> None:
        super().__init__(parent, padding=12)
        self.service = service
        self.bus = bus
        # ``session`` : rôle + client éventuel (espaces Admin / Client).
        # Les écrans d'administration l'ignorent ; les écrans client
        # s'en servent pour restreindre leur périmètre de données.
        self.session = session
        self._construire()
        self.rafraichir()

    # --- à spécialiser                                        ----------
    def _construire(self) -> None:
        raise NotImplementedError

    def rafraichir(self) -> None:
        """Rechargement après modification (appelé par le bus)."""

    # --- outils partagés                                      ----------
    def signaler_erreur(self, err: Exception) -> None:
        """Boîte d'erreur unique : mapping exception métier -> message.

        L'utilisateur ne voit JAMAIS une trace technique : la couche
        métier lève des ``ErreurMetier`` dont le message est prêt.
        """
        titre = ("Saisie invalide"
                 if isinstance(err, EntreeInvalideError) else "Opération refusée")
        messagebox.showerror(titre, str(err), parent=self)

    @staticmethod
    def vider(arbre: ttk.Treeview) -> None:
        """Vide complètement un Treeview."""
        arbre.delete(*arbre.get_children())
