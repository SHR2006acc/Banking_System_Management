"""Vérification fonctionnelle complète (M0-M2 + Espace client).

Recrée une base de démonstration TEMPORAIRE (jamais touché à banque.db),
assemble l'application hors écran et déroule 60+ vérifications :

  * charte appliquée (styles, polices, jetons) ;
  * relecture des montants (milliers, millions, séparateurs) ;
  * 5 écrans admin construits et remplis ;
  * bascule de session Admin <-> Client (registre filtré, en-tête,
    bus purgé/ré-abonné, navigation reconstruite) ;
  * les 3 écrans client ; dépôt + virement RÉELS depuis l'espace
    client, puis contrôle côté administrateur (même base).

Lancement :  cd "bank system" && ~/micromamba/envs/ai_env/bin/python \
            outils/verif_fonctionnelle.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, os.getcwd())

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from app.db.db_manager import DatabaseManager
from app.models.models import STATUT_CLIENT_SUSPENDU, TYPE_EPARGNE
from app.services.bank_service import BankService
from app.services.exceptions import ErreurMetier
from app.ui import theme as T
from app.ui.base_view import BusRafraichissement
from app.ui.shell import AppShell
from app.ui.session import SelecteurSession, Session
from app.ui.comptes_view import _DialogueOuverture
from app.ui.format import extraire_montant, fmt_montant
from app.ui.nouvelle_operation_view import _DialogueVirement
from main import NAVIGATION

VERTS: list[str] = []
ROUGES: list[tuple[str, str]] = []


def verifier(nom: str, condition: bool, detail: str = "") -> None:
    if condition:
        VERTS.append(nom)
    else:
        ROUGES.append((nom, detail or "condition fausse"))


def principal() -> None:
    # ------------------------------------------------------------------ #
    # Base temporaire + assemblage
    # ------------------------------------------------------------------ #
    dossier = tempfile.mkdtemp(prefix="banque_verif_")
    chemin = Path(dossier) / "banque.db"
    db = DatabaseManager(chemin)
    db.init_schema()
    db.seed_demo_data()
    service = BankService(db)

    racine = tk.Tk()
    racine.withdraw()
    T.appliquer_theme(racine)

    # --- 1. Charte : polices et styles --------------------------------
    famille = tkfont.nametofont("TkDefaultFont").actual("family")
    verifier("police Tk par défaut issue de la charte",
             famille.lower() in {f.lower() for f in T.FAMILLES}, famille)
    verifier("taille de base lisible (>= 11)",
             int(tkfont.nametofont("TkDefaultFont").actual("size")) >= 11,
             str(tkfont.nametofont("TkDefaultFont").actual("size")))
    style = ttk.Style(racine)
    for nom_style in ("Titre.TLabel", "SousTitre.TLabel", "Indicateur.TLabel",
                      "Carte.TLabelframe", "Carte.TLabelframe.Label",
                      "CarteTitre.TLabel", "Primaire.TButton",
                      "Succes.TButton", "Danger.TButton",
                      "Secondaire.TButton", "Lien.TButton", "Treeview",
                      "Treeview.Heading", "TCombobox", "TEntry",
                      "Vide.TLabel", "Nav.TFrame"):
        try:
            style.lookup(nom_style, "background")
            ok = True
        except tk.TclError:
            ok = False
        verifier(f"style {nom_style} résolu", ok)
    verifier("Primaire.TButton = bleu NAVY",
             style.lookup("Primaire.TButton", "background") == T.NAVY)
    verifier("filet de table chant 1 px",
             style.lookup("Treeview.Heading", "background") == T.SURFACE)

    # --- 2. Relecture des montants -------------------------------------
    verifier("saisie 1 250,50", extraire_montant("1 250,50") == 1250.5)
    verifier("saisie 1 000 000,50 (million)",
             extraire_montant("1 000 000,50") == 1_000_000.5)
    verifier("saisie 1.000.000,50 (points milliers)",
             extraire_montant("1.000.000,50") == 1_000_000.5)
    verifier("saisie 1000000 (brut)", extraire_montant("1000000") == 1e6)
    verifier("affichage million", fmt_montant(1_234_567.891)
             == "1 234 567,89 €")
    try:
        extraire_montant("12,34,56")
        verifier("saisie ambiguë refusée", False, "pas d'exception")
    except ErreurMetier:
        verifier("saisie ambiguë refusée", True)

    # --- 3. Écrans admin ------------------------------------------------
    bus = BusRafraichissement()
    shell = AppShell(racine, service, bus, NAVIGATION,
                     session=Session("admin"), info_base="verif.db")
    shell.pack(fill="both", expand=True)
    bus.abonner(shell)

    cles_admin = list(shell._registre)
    verifier("registre admin = 5 écrans",
             cles_admin == ["dashboard", "clients", "comptes", "operations",
                            "galerie"], str(cles_admin))
    verifier("nav admin : 5 items construits", len(shell._items_nav) == 5)

    for cle in cles_admin:
        shell.afficher(cle)
        vue = shell._vues.get(cle)
        attendu = shell._registre[cle].classe.__name__
        verifier(f"écran {cle} construit ({attendu})",
                 vue is not None and type(vue).__name__ == attendu)
        verifier(f"écran {cle} packé",
                 vue is not None and vue.winfo_manager() == "pack")
    verifier("titre d'en-tête = page Galerie",
             shell._titre_page.cget("text") == "Galerie de style")

    # Tableaux admin remplis depuis le service
    vue_clients = shell._vues["clients"]
    verifier("Clients : lignes = clients en base",
             len(vue_clients.arbre.get_children())
             == len(service.read_clients()))
    vue_galerie = shell._vues["galerie"]
    vue_galerie._remplir_tableau()
    verifier("Galerie : 4 lignes de démo",
             vue_galerie._tableau.nombre() == 4)
    vue_galerie._vider_tableau()
    verifier("Galerie : état vide", vue_galerie._tableau.nombre() == 0)

    stats_admin_avant = service.statistiques()
    verifier("barre d'état synchronisée",
             shell._etat_donnees.cget("text") ==
             f"{stats_admin_avant['nb_clients']} clients · "
             f"{stats_admin_avant['nb_comptes']} comptes · "
             f"{stats_admin_avant['nb_operations']} opérations",
             shell._etat_donnees.cget("text"))

    # --- 3bis. Ouverture de compte via sa modale -------------------------
    # (Bug historique : un ttk.Label recevait « bg » — option inconnue de
    #  ttk — l'exception figeait la modale à mi-parcours, sans champ
    #  « Solde initial » ni boutons. Vérifié de bout en bout désormais.)
    vue_comptes = shell._vues["comptes"]
    titulaire = next(c for c in service.read_clients()
                     if c.statut == "ACTIF")
    vue_comptes._var_client.set(
        f"{titulaire.nom_complet} — CIN {titulaire.cin}")
    vue_comptes._rafraichir_tableau()
    verifier("Comptes : filtre titulaire appliqué",
             vue_comptes._client_selectionne() is not None)

    nb_comptes = len(service.read_comptes())
    boite = _DialogueOuverture(vue_comptes, service, titulaire)
    boite._var_type.set(TYPE_EPARGNE)
    boite._solde.definir("2 500,50")
    boite._sur_valider()
    verifier("Modale ouverture : compte créé (solde initial crédité)",
             boite.resultat is not None
             and len(service.read_comptes()) == nb_comptes + 1)
    verifier("Modale ouverture : type et solde appliqués",
             boite.resultat is not None
             and boite.resultat.type == TYPE_EPARGNE
             and abs(boite.resultat.solde - 2500.50) < 0.001)

    # Solde initial nul : explicitement autorisé.
    boite_nul = _DialogueOuverture(vue_comptes, service, titulaire)
    boite_nul._solde.definir("0")
    boite_nul._sur_valider()
    verifier("Modale ouverture : solde initial 0 accepté",
             boite_nul.resultat is not None
             and boite_nul.resultat.solde == 0.0)

    # Saisie invalide -> erreur inline, la modale reste ouverte.
    boite_mal = _DialogueOuverture(vue_comptes, service, titulaire)
    boite_mal._solde.definir("12,34,56")
    boite_mal._sur_valider()
    verifier("Modale ouverture : saisie invalide refusée inline",
             boite_mal.resultat is None and boite_mal.winfo_exists())
    boite_mal.destroy()

    # Client suspendu -> refus du métier (R4b), rien en base.
    suspendu = next(c for c in service.read_clients()
                    if c.statut == STATUT_CLIENT_SUSPENDU)
    nb_avant_refus = len(service.read_comptes())
    boite_refus = _DialogueOuverture(vue_comptes, service, suspendu)
    boite_refus._sur_valider()
    verifier("Modale ouverture : client suspendu refusé (R4b)",
             boite_refus.resultat is None and boite_refus.winfo_exists()
             and len(service.read_comptes()) == nb_avant_refus)
    boite_refus.destroy()

    vue_comptes.rafraichir()
    attendu = len(service.read_comptes_par_client(titulaire.id_client))
    verifier("Comptes : tableau rechargé (nouveaux comptes visibles)",
             len(vue_comptes.arbre.get_children()) == attendu,
             f"{len(vue_comptes.arbre.get_children())} vs {attendu}")

    # --- 4. Sélecteur de session ----------------------------------------
    selecteur = SelecteurSession(shell, service, Session("admin"))
    attendus = 1 + 1 + len(service.read_clients())   # libellé + admin + clients
    verifier("sélecteur : une ligne par espace",
             len(selecteur.corps.winfo_children()) == attendus,
             str(len(selecteur.corps.winfo_children())))
    selecteur.destroy()

    # --- 5. Bascule côté client ------------------------------------------
    client = None
    for candidat in service.read_clients():
        if len(service.read_comptes_par_client(candidat.id_client)) >= 2:
            client = candidat
            break
    verifier("client de démonstration (>= 2 comptes)", client is not None)
    shell.changer_session(Session("client", client))

    cles_client = list(shell._registre)
    verifier("registre client = 3 écrans",
             cles_client == ["mes_comptes", "mes_operations",
                             "nouvelle_operation"], str(cles_client))
    verifier("nav client reconstruite (3 items)",
             len(shell._items_nav) == 3)
    verifier("en-tête : nom du client",
             shell._etiquette_nom.cget("text") == client.nom_complet)
    verifier("en-tête : rôle client",
             "client" in shell._etiquette_role.cget("text").lower())
    verifier("pastille = initiales",
             shell._puce_initiales.cget("text")
             == (client.nom[:1] + client.prenom[:1]).upper())
    verifier("bus purgé des vues admin détruites",
             all(getattr(abonne, "winfo_exists", lambda: False)()
                 for abonne in bus._abonnes if abonne is not shell))

    vue_comptes = shell._vues["mes_comptes"]
    attendu = len(service.read_comptes_par_client(client.id_client))
    verifier("Mes comptes : lignes = comptes du client",
             vue_comptes._tableau.nombre() == attendu, str(attendu))
    verifier("Mes comptes : KPI renseigné",
             vue_comptes._kpi_actifs._valeur.cget("text") != "—")

    shell.afficher("mes_operations")
    vue_ops = shell._vues["mes_operations"]
    compte_ops = vue_ops._compte_selectionne()
    verifier("Mes opérations : compte sélectionné",
             compte_ops is not None)
    verifier("Mes opérations : lignes = relevé du service",
             vue_ops._tableau.nombre() == len(
                 service.releve(compte_ops.id_compte)),
             f"{vue_ops._tableau.nombre()} vs "
             f"{len(service.releve(compte_ops.id_compte))}")

    shell.afficher("nouvelle_operation")
    vue_new = shell._vues["nouvelle_operation"]
    actifs = [c for c in service.read_comptes_par_client(client.id_client)
              if c.statut == "ACTIF"]
    verifier("Nouvelle opération : comptes ACTIFS listés",
             len(vue_new._comptes) == len(actifs))

    # --- 6. Dépôt réel depuis l'espace client -----------------------------
    compte = vue_new._compte_selectionne()
    solde_avant = compte.solde
    nb_ops_avant = service.statistiques()["nb_operations"]
    vue_new._montant.var.set("1 250,50")
    vue_new._simple("depot")
    solde_apres = service.obtenir_compte(compte.id_compte).solde
    verifier("Dépôt client : 1 250,50 € crédités",
             abs(solde_apres - (solde_avant + 1250.50)) < 0.001,
             f"{solde_avant} -> {solde_apres}")
    verifier("Dépôt client : historisé",
             service.statistiques()["nb_operations"] == nb_ops_avant + 1)
    verifier("Dépôt client : vues re-synchronisées (bus)",
             vue_new._compte_selectionne().solde == solde_apres)

    # Montant invalide -> erreur inline, rien en base
    nb_ops = service.statistiques()["nb_operations"]
    vue_new._montant.var.set("")
    vue_new._simple("retrait")
    verifier("Retrait sans montant : refusé proprement",
             service.statistiques()["nb_operations"] == nb_ops)

    # Solde insuffisant -> message du métier affiché sous le champ
    vue_new._montant.var.set("99999999")
    vue_new._simple("retrait")
    verifier("Retrait > solde : refusé proprement",
             service.statistiques()["nb_operations"] == nb_ops
             and service.obtenir_compte(compte.id_compte).solde == solde_apres)

    # --- 7. Virement depuis l'espace client (écriture double) -------------
    source = vue_new._compte_selectionne()
    tous_comptes = service.read_comptes()
    cible = next(c for c in tous_comptes
                 if c.statut == "ACTIF" and c.id_compte != source.id_compte)
    solde_cible_avant = cible.solde

    boite = _DialogueVirement(shell, service, client, source)
    boite._beneficiaire.definir(cible.numero)
    boite._montant.var.set("100")
    boite._valider()
    verifier("Virement client : message de succès",
             isinstance(boite.resultat, str) and "effectué" in boite.resultat,
             str(boite.resultat))
    derniere = service.releve(source.id_compte)[0]
    verifier("Virement : dernière ligne du relevé = VIREMENT",
             derniere.type == "VIREMENT")
    jambes = service.jambes_virement(derniere.id_virement)
    verifier("Virement : DEUX jambes liées (source + cible)",
             len(jambes) == 2
             and {j.id_compte for j in jambes}
             == {source.id_compte, cible.id_compte})
    verifier("Virement : cible créditée de 100 €",
             abs(service.obtenir_compte(cible.id_compte).solde
                 - (solde_cible_avant + 100)) < 0.001)

    # Virement impossible -> erreur inline, modale non fermée
    boite2 = _DialogueVirement(shell, service, client, source)
    boite2._beneficiaire.definir("CPT-9999")
    boite2._montant.var.set("10")
    boite2._valider()
    verifier("Virement compte inconnu : erreur inline, modale ouverte",
             boite2.resultat is None and boite2.winfo_exists())
    boite2.destroy()
    boite3 = _DialogueVirement(shell, service, client, source)
    boite3._beneficiaire.definir(cible.numero)
    boite3._montant.var.set("99999999")
    boite3._valider()
    verifier("Virement solde insuffisant : erreur inline, modale ouverte",
             boite3.resultat is None and boite3.winfo_exists())
    boite3.destroy()

    # --- 8. Retour admin : les opérations client sont visibles -------------
    stats = service.statistiques()
    shell.changer_session(Session("admin"))
    verifier("retour admin : registre complet (5)",
             len(shell._registre) == 5)
    verifier("retour admin : en-tête Administrateur",
             shell._etiquette_nom.cget("text") == "Administrateur")
    texte_etat = shell._etat_donnees.cget("text")
    verifier("admin voit les opérations du client",
             f"{stats['nb_operations']} opérations" in texte_etat,
             texte_etat)
    shell.afficher("operations")
    vue_ops_admin = shell._vues["operations"]
    verifier("Opérations (admin) : relevé rempli",
             hasattr(vue_ops_admin, "arbre")
             and len(vue_ops_admin.arbre.get_children()) > 0)

    # --- 9. Finitions -------------------------------------------------------
    shell._rafraichir_actif()
    verifier("F5 (rafraîchissement) sans erreur", True)
    racine.update_idletasks()
    racine.destroy()
    db.close()


try:
    principal()
except Exception:
    traceback.print_exc()
    ROUGES.append(("script interrompu", "voir traceback ci-dessus"))

print()
for nom in VERTS:
    print(f"  ✔ {nom}")
for nom, detail in ROUGES:
    print(f"  ✘ {nom}  [{detail}]")
print()
print(f"{len(VERTS)} vérifications vertes, {len(ROUGES)} rouges")
sys.exit(1 if ROUGES else 0)
