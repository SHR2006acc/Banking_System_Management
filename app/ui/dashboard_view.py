"""Onglet « Tableau de bord » (Rôle 3) : indicateurs + derniers mouvements."""
from __future__ import annotations

from tkinter import ttk

from app.ui.base_view import VueBase, fmt_montant
from app.ui.format import fmt_date


class DashboardView(VueBase):
    titre_onglet = "Tableau de bord"

    def _construire(self) -> None:
        # ---- cartes d'indicateurs (SI : population / encours / volume) --
        zone_cartes = ttk.Frame(self)
        zone_cartes.pack(fill="x", pady=(0, 12))
        self._cartes: dict[str, ttk.Label] = {}
        definitions = (
            ("nb_clients", "Clients"),
            ("nb_comptes_actifs", "Comptes actifs"),
            ("encours_total", "Encours total"),
            ("volume_operations", "Volume des opérations"),
        )
        for colonne, (cle, libelle) in enumerate(definitions):
            carte = ttk.LabelFrame(zone_cartes, text=libelle,
                                   style="Carte.TLabelframe", padding=(12, 10))
            carte.grid(row=0, column=colonne, sticky="nsew", padx=6)
            etiquette = ttk.Label(carte, text="—", style="Indicateur.TLabel")
            etiquette.pack()
            self._cartes[cle] = etiquette
            zone_cartes.columnconfigure(colonne, weight=1)

        # ---- derniers mouvements (tous comptes, via le service) --------
        cadre = ttk.LabelFrame(self, text="Derniers mouvements",
                               style="Carte.TLabelframe", padding=(10, 10))
        cadre.pack(fill="both", expand=True)
        barre = ttk.Scrollbar(cadre, orient="vertical")
        self.arbre = ttk.Treeview(
            cadre, columns=("date", "compte", "type", "montant"),
            show="headings", height=9, yscrollcommand=barre.set)
        for colonne, texte, largeur, ancre in (
            ("date", "Date", 180, "w"),
            ("compte", "Compte", 110, "w"),
            ("type", "Type", 110, "w"),
            ("montant", "Montant brut", 130, "e"),
        ):
            self.arbre.heading(colonne, text=texte)
            self.arbre.column(colonne, width=largeur, anchor=ancre)
        barre.configure(command=self.arbre.yview)
        barre.pack(side="right", fill="y")
        self.arbre.pack(side="left", fill="both", expand=True)

    def rafraichir(self) -> None:
        stats = self.service.statistiques()
        cartes = {
            "nb_clients": str(stats["nb_clients"]),
            "nb_comptes_actifs": str(stats["nb_comptes_actifs"]),
            "encours_total": fmt_montant(stats["encours_total"]),
            "volume_operations": fmt_montant(stats["volume_operations"]),
        }
        for cle, etiquette in self._cartes.items():
            etiquette.config(text=cartes[cle])

        self.vider(self.arbre)
        for ligne in self.service.operations_recentes(limite=10):
            self.arbre.insert(
                "", "end", values=(
                    fmt_date(ligne["date_op"]), ligne["numero_compte"],
                    ligne["type"],
                    fmt_montant(float(ligne["montant"]))))
