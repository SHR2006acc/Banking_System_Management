# Rapport 3 — Couche interface : guide complet

> Ce document explique **chaque fichier** de la couche interface,
> **chaque fonction** qu'il contient, et **comment tout s'emboîte**.
> Il sert à la fois de documentation de code, de support de
> présentation orale et de mémo pour toute modification future.

---

## 0. Lancer l'application

```bash
cd "bank system"
./lancer.sh                                   # recommandé : rendu optimal
~/micromamba/envs/ai_env/bin/python main.py   # équivalent direct
```

`lancer.sh` choisit l'interpréteur dont Tk voit les **polices lissées**
via fontconfig (~750 familles sur cette machine) et retombe sur `ai_env`
sinon ; le code est identique dans les deux cas (voir piège n° 13).

| Raccourci | Effet |
| :--- | :--- |
| `Ctrl+1` … `Ctrl+9` | Aller à l'écran n° 1 à 9 de l'espace courant (5 écrans admin, 3 écrans client) |
| `F5` | Recharger l'écran affiché depuis la base |
| `Échap` | Fermer la modale ouverte |
| `Entrée` | Confirmer dans une modale de confirmation |
| `Ctrl+Q` | Quitter proprement (ferme la base avant la fenêtre) |

---

## 1. Vue d'ensemble

### 1.1 Où se situe la couche interface

```
   main.py                    ← assemble les trois couches
      │
      ├── DatabaseManager     (données : SQLite, transactions)
      ├── BankService         (métier : règles de gestion, exceptions)
      └── AppShell            (interface : cette couche)
```

Règle d'or : **une vue ne fait jamais de SQL**. Elle appelle le service,
attrape les `ErreurMetier` et les affiche telles quelles.

### 1.2 Carte des fichiers de la couche interface

```
app/ui/
├── theme.py            ← LA charte : couleurs, polices, styles ttk
├── format.py           ← formatage (montants, dates) + relecture saisie
├── utilitaires.py      ← helpers tk génériques
├── base_view.py        ← bus d'événements + classe mère des écrans
├── session.py          ← session (rôle + client) + sélecteur de vue
├── shell.py            ← coquille : barre latérale + en-tête + routeur
│
├── components/         ← kit de composants réutilisables
│   ├── cartes.py       │  Carte, CarteKPI
│   ├── tableaux.py     │  Tableau (Treeview habillé)
│   ├── champs.py       │  Champ, ChampMontant, Badge
│   ├── retours.py      │  Modale, ConfirmationModale, toasts
│   ├── graphiques.py   │  GraphiqueBarres (Canvas)
│   └── defilement.py   │  ZoneDefilante (conteneur scrollable)
│
├── galerie_view.py     ← vitrine du design system (écran de dév)
│
├── Écrans ADMIN (roles=("admin",))
│   ├── dashboard_view.py        ← tableau de bord
│   ├── clients_view.py          ← CRUD clients
│   ├── comptes_view.py          ← comptes
│   └── operations_view.py       ← dépôt / retrait / virement
│
└── Écrans CLIENT (roles=("client",))
    ├── mes_comptes_view.py        ← ses comptes
    ├── mes_operations_view.py     ← son relevé
    └── nouvelle_operation_view.py ← déposer / retirer / virer
```

### 1.3 Qui dépend de qui (jamais l'inverse)

```
main.py
  └─ shell.py ──────────► base_view.py ──► format.py
       │                     │
       │                     ├──► services/exceptions.py
       │                     └──► session.py (rôle + client)
       ├─ components/*  ──► theme.py (jetons + helpers)
       └─ *_view.py     ──► base_view.py, format.py, components/*
```

`theme.py` ne connaît personne ; tout le monde connaît `theme.py`.

---

## 2. Le système de design (`theme.py`)

### 2.1 Les jetons (tokens)

Toutes les couleurs du projet vivent **ici et nulle part ailleurs**.
Changer la teinte de la marque = changer une ligne ici, l'application
entière suit.

| Famille | Jeton | Valeur | Rôle |
| :--- | :--- | :--- | :--- |
| Texte | `INK` | `#0E1B2C` | texte principal |
| | `INK_SOFT` | `#55657A` | texte secondaire |
| | `MUTED` | `#6E7F92` | légendes discrètes |
| Fonds | `BG` | `#F3F5F7` | fond de page |
| | `SURFACE` | `#FFFFFF` | cartes, en-têtes, tableaux |
| | `SURFACE_ALT` | `#FAFBFC` | lignes zébrées |
| | `SURVOL` | `#F1F5F9` | survol de ligne |
| Filets | `LINE` | `#E3E8EE` | filet 1 px des cartes |
| | `LINE_STR` | `#CBD4DE` | bordure des champs |
| Marque | `NAVY` | `#123C6B` | actions primaires, titres |
| | `NAVY_HOVER` / `NAVY_PRESSED` | `#0E3058` / `#0A2545` | états du bouton |
| | `NAVY_DEEP` | `#0F2743` | fond barre latérale |
| | `NAVY_ITEM` | `#16375B` | item survolé/actif |
| | `NAVY_TINT` | `#E9F0F7` | teinte claire (sélection) |
| Sémantique | `POS` / `POS_TINT` | `#12703C` / `#E7F4EC` | crédit, succès |
| | `NEG` / `NEG_TINT` | `#B3261E` / `#FBEAE9` | débit, danger |
| | `WARN` / `WARN_TINT` | `#8A5A00` / `#FCF3E3` | avertissement |
| Technique | `FOCUS` | `#1E66C9` | anneau de focus clavier |
| | `DESACTIVE` / `SURFACE_NEUTRE` | `#9FB3C8` / `#EAEEF3` | désactivé / secondaire |

### 2.2 `detecter_famille(root) -> str`

Parcourt `FAMILLES = ("Segoe UI", "Inter", "Noto Sans", "Cantarell",
"Liberation Sans", "Ubuntu", "DejaVu Sans")` et renvoie la **première
famille installée**. La comparaison est **insensible à la casse** : Tk
renvoie les familles en minuscules sur X11 (« liberation sans ») et
sans cette tolérance la détection échoue — Tk peint alors sa police
bitmap « fixed », illisible (c'était le bug « police moche » du
18/10 ; voir piège n° 13). Windows → Segoe UI, KDE → Noto Sans /
Cantarell, sinon Liberation / DejaVu. L'interface reste « native » sur
toutes les machines, sans configuration.

### 2.3 `police(taille, gras=False) -> tuple`

Renvoie un descripteur de police `(famille, taille, "bold"/"normal")`
utilisable partout. Pourquoi un tuple et pas un style ttk ? Parce que
les widgets Tk purs (`tk.Label`, `tk.Canvas`…) **ignorent les styles
ttk** : sans ce helper, il faudrait recopier la famille partout.

### 2.4 `appliquer_theme(root) -> ttk.Style` — la séquence exacte

1. `_FAMILLE = detecter_famille(root)` → mémorise la famille globale ;
2. configure les **polices nommées** (`TkDefaultFont`, `TkTextFont`,
   `TkMenuFont`, `TkHeadingFont`) : les widgets qui n'ont pas de style
   explicite, les listes déroulantes et les dialogues `messagebox`
   héritent ainsi de la charte ;
3. `theme_use("clam")` : le seul moteur ttk qui honore réellement
   couleurs et bordures sur les trois plateformes ;
4. configure le style `"."` : **valeurs par défaut de tous les styles** ;
5. déclare les styles nommés (voir tableau 2.5).

Deux helpers tolérants : `_configurer(style, nom, **options)` et
`_mapper(style, nom, **options)` appliquent chaque option
individuellement et **ignorent celles que ce Tk ne connaît pas**
(`bordercolor`, `focuscolor`… n'existent que depuis Tk 8.6.10). Résultat :
la même base de code fonctionne de Tk 8.6 à Tk 9 sans plantage.

### 2.5 Les styles ttk déclarés

| Style | Rôle | États (`map`) définis |
| :--- | :--- | :--- |
| `Titre.TLabel` / `Champ.TLabel` / `SousTitre.TLabel` | titres et libellés | — |
| `Indicateur.TLabel` | grand chiffre KPI | — |
| `CarteTitre.TLabel` / `Vide.TLabel` | légende de carte / état vide | — |
| `Carte.TLabelframe(+«.Label »)` | carte héritage (écrans existants) | — |
| `Carte.TFrame` / `Carte.TLabel` / `Carte.TCheckbutton` | fond blanc des cartes | — |
| `Formulaire.TLabel/TEntry/TCombobox` | formulaires (écrans existants) | — |
| `TEntry` / `TCombobox` | champ de saisie | `focus` → bordure `FOCUS` |
| `Primaire.TButton` / `Action.TButton` | action principale (navy) | `active`/`pressed`/`disabled` |
| `Succes.TButton` / `Danger.TButton` | valider (vert) / destructif (rouge) | idem |
| `Secondaire.TButton` | action neutre (gris) | idem |
| `Lien.TButton` | lien discret | `active`/`pressed` |
| `BadgeActif/Suspendu/Cloture/Neutre/Danger.TLabel` | badges d'état | — |
| `Treeview` / `Treeview.Heading` | tableaux | `selected` → bleu clair |
| `Vertical.TScrollbar` / `TSeparator` | finitions | `active` |
| `TNotebook(.Tab)` | héritage des anciens onglets | `selected` |

### 2.6 Pourquoi `option_add` pour les Combobox ?

La liste déroulante d'un `ttk.Combobox` est une **Listbox Tk classique**
invisible aux styles ttk. On la configure via la base d'options :

```python
root.option_add("*TCombobox*Listbox.background", SURFACE)
root.option_add("*TCombobox*Listbox.selectBackground", NAVY)
```

Sans ces lignes, la liste s'ouvre en gris système — incohérence visible.

---

## 3. Fichier par fichier, fonction par fonction

### 3.1 `app/ui/format.py` — formatage et relecture

Un seul endroit décide comment un montant s'écrit et comment une saisie
est relue : les 8 écrans restent cohérents par construction.

| Fonction | Rôle |
| :--- | :--- |
| `fmt_montant(valeur)` | `1500.0` → `« 1 500,00 € »` (espace milliers, virgule) |
| `fmt_entier(valeur)` | `1234` → `« 1 234 »` (sans devise) |
| `fmt_date(texte)` | `« 2026-10-18 14:32:05 »` → `« 18/10/2026 14:32 »` ; tolérant (renvoie `« — »` ou le texte brut) |
| `extraire_montant(texte, zero_autorise=False)` | relit une saisie humaine → `float`, **valide > 0** (`zero_autorise=True` : ≥ 0, pour le solde initial d'un compte), lève une `EntreeInvalideError` au message français prêt à afficher (grammaire ci-dessous) |

C'est `extraire_montant` qui corrige l'ancien défaut « fuite du
message d'erreur de `float()` ».

Grammaire de relecture (tolérante, jamais ambiguë) : `1 250,50`,
`1250.5`, `1000000`, `1.000` (= 1 000 : point seul suivi de 3 chiffres
= milliers), `1.000.000` (= 1 000 000), `1.000.000,50` ou
`1,000,000.50` (les deux séparateurs présents : **le plus à droite
est la décimale**, l'autre est ignoré comme séparateur de milliers),
suffixe `€` et espaces de toute sorte tolérés. Aucune limite de
taille : millions et milliards s'affichent et se relisent. 19 tests
unitaires dédiés : `tests/test_formats.py`.

### 3.2 `app/ui/utilitaires.py` — helpers Tk génériques

| Fonction | Rôle |
| :--- | :--- |
| `lier_recursif(fenetre, sequence, rappel)` | lie un événement au widget **et à tous ses descendants** — indispensable pour un item de navigation composé de 3 widgets (cadre + barre + étiquette) : sans cela, le survol « clignote » quand la souris passe d'un enfant à l'autre |
| `centrer_fenetre(fenetre, largeur, hauteur)` | calcule la position de centrage écran (léger décalage vers le haut) |

### 3.3 `app/ui/base_view.py` — socle et bus d'événements

| Élément | Rôle |
| :--- | :--- |
| `Rafraichissable` (Protocol) | le **contrat** : tout objet qui sait se re-synchroniser (`rafraichir()`). Contrainte de typage sans héritage — le shell s'y conforme sans être une vue |
| `BusRafraichissement.abonner(abonne)` | inscrit un abonné (vue ou shell) |
| `BusRafraichissement.publier()` | appelle `rafraichir()` de **tous** les abonnés — après chaque modification de la base |
| `BusRafraichissement.reinitialiser()` | vide la liste d'abonnés — utilisé à la bascule de session : les vues détruites ne doivent plus être appelées |
| `VueBase.__init__(parent, service, bus, session=None)` | stocke service + bus + **session** (rôle + client éventuel ; `None` pour les écrans d'administration), appelle `_construire()` puis `rafraichir()` |
| `VueBase._construire()` | abstraite : chaque écran construit ses widgets |
| `VueBase.rafraichir()` | recharge l'écran depuis le service (vide par défaut) |
| `VueBase.signaler_erreur(err)` | boîte d'erreur unique : `EntreeInvalideError` → « Saisie invalide », sinon « Opération refusée » ; **le message affiché est `str(err)`** |
| `VueBase.vider(arbre)` | vide un `Treeview` en une ligne |

Attributs de classe : `titre_onglet` (héritage), `titre_page` et
`sous_titre` (affichés par l'en-tête du shell).

### 3.4 `app/ui/components/cartes.py` — les panneaux

**`Carte(parent, titre=None, accent=None, padding=16)`**

Le panneau blanc, brique de base de toutes les mises en page. Coins
francs, filet 1 px via `highlightthickness=1` (astuce : les `tk.Frame`
savent encadrer, pas les `ttk.Frame`). Structure :

```
┌─ barre d'accent 2 px (optionnelle, couleur du sens) ─┐
│ Titre                                  [zone actions] │
│ ─────────────── filet 1 px ───────────────            │
│ corps : les widgets du développeur                    │
└───────────────────────────────────────────────────────┘
```

- `carte.corps` : la frame blanche où ranger le contenu ;
- `carte.actions` : la frame d'en-tête à droite (boutons « Ajouter »…).

**`CarteKPI(parent, libelle, valeur, accent)`** — carte d'indicateur :
légende 10 pt majuscules grises, **grand chiffre 24 pt gras**, sous-texte.
`definir(valeur, sous=None)` met à jour le contenu sans reconstruire.

### 3.5 `app/ui/components/tableaux.py` — le tableau haut de gamme

**`Tableau(parent, colonnes, hauteur=10, texte_vide=…)`** où chaque
colonne est `(cle, entete, largeur, ancre)`. La dernière colonne
s'étire ; le tableau **ne formate rien** (les valeurs arrivent déjà
formatées via `format.py`).

| Méthode | Rôle |
| :--- | :--- |
| `remplir(lignes, id_cle=None, tags_fn=None)` | remplace tout ; `id_cle` fige l'iid (ex. `"numero"` → sélection stable entre deux rechargements) ; `tags_fn(ligne)` teinte certaines lignes (`credit`, `debit`, `desactive`) |
| `vider()` | tout supprimer + afficher l'état vide |
| `selection()` / `ligne_selectionnee()` | iid / **dict de la ligne** sélectionnée |
| `nombre()` / `contenu()` | comptage / liste des dicts |
| `sur_selection(rappel)` | callback à chaque changement de sélection |
| `sur_double_clic(rappel)` | callback `rappel(dict_ligne)` au double-clic |

Détails d'ingénierie :

- **zébrures** : tag `paire` (fond `SURFACE_ALT`) sur une ligne sur deux ;
- **survol** : `_sur_survol(event)` identifie la ligne sous la souris
  (`identify_row`) et pose le tag `survol` **en premier** dans la liste ;
  en Treeview, à options égales, **le premier tag de la liste l'emporte**
  — c'est le piège n° 5 de la section 5 ;
- **état vide** : une étiquette posée par-dessus le tableau, affichée
  par `_maj_etat_vide()` uniquement quand il n'y a aucune ligne.

### 3.6 `app/ui/components/champs.py` — saisie et états

**`Champ(parent, libelle, obligatoire=False, valeur="", largeur=28)`**
— libellé + `ttk.Entry` + **ligne d'erreur inline** masquée (l'erreur
s'affiche sous le champ, l'utilisateur corrige sans perdre le contexte,
contrairement à une boîte de dialogue). L'astérisque du libellé marque
les champs obligatoires.

| Méthode | Rôle |
| :--- | :--- |
| `lire()` | texte saisi, espaces rognés |
| `definir(valeur)` / `vider()` | remplir / vider par code |
| `est_vide()` | test « obligatoire » |
| `afficher_erreur(message)` / `effacer_erreur()` | montre/cache la ligne rouge (`grid` / `grid_remove`) |
| `donner_focus()` | place le curseur dans la saisie |

**`ChampMontant(Champ)`** — champ de montant : aligné à droite,
suffixe « € », filtre de frappe (`_filtrer_frappe` ne laisse passer que
chiffres/espaces/séparateurs) et `valeur()` qui relit en français et
valide via `extraire_montant`. Le dialogue « Ouvrir un compte » lit
`lire()` avec `zero_autorise=True` : un solde initial nul est permis.

**`Badge(parent, texte, ton)`** — étiquette d'état en majuscules, fond
teinté, coins francs. Tons : `actif`, `suspendu`, `cloture`, `neutre`,
`danger`. `definir(texte, ton)` met à jour.
**`ton_pour_statut(statut)`** fait la correspondance métier → ton
(`"ACTIF"` → `"actif"`…) : source unique de vérité.

### 3.7 `app/ui/components/retours.py` — modales et notifications

**`Modale(parent, titre)`** — base des fenêtres modales de la charte
(`messagebox` étant hors charte et sans contrôle) :

- `transient` + `grab_set` : la fenêtre mère est bloquée tant que la
  modale vit (vraie modalité) ;
- `afficher(largeur=None)` : centrage sur la mère, puis **prise de
  focus différée** (`after(40, _prendre_focus)`). On n'utilise PAS
  `wait_visibility()`, qui peut geler l'application si le gestionnaire
  de fenêtres tarde (session verrouillée, machine chargée) ;
- `attendre()` : boucle locale jusqu'à fermeture (`wait_window`) ;
- `fermer()` : libère le grab puis détruit.

**`ConfirmationModale(...)`** — question Confirmer/Annuler :

```python
if ConfirmationModale.demander(self, "Clôture",
        "Clôturer définitivement CPT-0004 ?", texte_confirmer="Clôturer"):
    ...
```

`_conclure(True/False)` mémorise `resultat` puis ferme ; `Entrée`
confirme, `Échap` annule.

Patron commun aux modales à formulaire : **sous-classer `Modale`**, puis
remplir `self.corps` (libellés `tk.Label`, champs `Champ`/`ChampMontant`)
et `self.pied` (boutons), et mémoriser le verdict dans `self.resultat`
avant de `fermer()`. Le constructeur ne bloque jamais : l'appelant
enchaîne `afficher()` puis `attendre()`, et relit `resultat`. Exemples :
`ConfirmationModale`, `_DialogueVirement` (espace client),
`_DialogueOuverture` (création de compte, admin — erreurs qui s'affichent
sous le champ concerné, la modale reste ouverte).

**`afficher_toast(parent, message, ton="succes", duree=3600)`** —
notification non bloquante en bas à droite : filet 1 px autour, barre
d'accent 3 px colorée selon le ton, empilement vertical automatique,
**disparition seule** après `duree` ms, clic pour fermer plus tôt.
C'est le retour d'information utilisé pour les succès (« 4 lignes
affichées », « Saisie valide »…).

### 3.8 `app/ui/components/graphiques.py` — histogramme Canvas

**`GraphiqueBarres(parent, hauteur=150, couleur=NAVY)`** — 100 %
bibliothèque standard (pas de matplotlib) : rectangles pleins, filet
d'axe, zéro décoration, cohérent avec la charte.

- `definir(donnees)` : `[(etiquette, valeur), …]` ;
- `_tracer()` : (re)dessine — marges réservées aux légendes, barre la
  plus haute = hauteur disponible, valeurs affichées seulement si
  ≤ 8 barres (sinon illisible) ;
- redessin **automatique** sur `<Configure>` : l'histogramme s'adapte
  quand la fenêtre change de taille (étirement de la fenêtre pendant la
  démo = effet garanti).

### 3.9 `app/ui/components/defilement.py` — zone défilante

Tk n'a pas de « frame scrollable » : la recette fait le lien entre un
`Canvas`, une `Scrollbar` et une frame interne.

**`ZoneDefilante(parent)`** — ranger le contenu dans `zone.contenu` :

- `_quand_contenu_change` : la zone défilante épouse la hauteur réelle
  du contenu (`scrollregion`) ;
- `_quand_canvas_change` : la frame interne garde la largeur du canvas ;
- **molette** : `_installer_molette` pose UN gestionnaire global unique
  (`bind_all`) qui remonte la hiérarchie du widget survolé pour trouver
  la `ZoneDefilante` marquée (attribut `_zone_defilante`) et la fait
  défiler. Sous Linux/X11, la molette émet `<Button-4>` / `<Button-5>`
  et **pas** `<MouseWheel>` — piège n° 6 de la section 5.

### 3.10 `app/ui/shell.py` — la coquille (navigation + routeur)

**`EntreeNav(cle, libelle, classe, roles=("admin",))`** — dataclass
*frozen* : la **source unique** de la navigation. Ajouter un écran =
une ligne dans le registre de `main.py`. `roles` prépare le
cloisonnement Client/Administrateur du projet d'équipe : le shell ne
construit que les entrées dont le rôle courant fait partie.

**`AppShell(parent, service, bus, registre, session=None, info_base="")`**
— assemblage complet :

```
┌───────────┬───────────────────────────────────────┐
│           │  en-tête : titre de page + utilisateur │
│  barre    ├───────────────────────────────────────┤
│  latérale │                                       │
│  (navy)   │   zone des écrans (routeur)            │
│           │                                       │
│           ├───────────────────────────────────────┤
│           │  barre d'état : base + compteurs live  │
└───────────┴───────────────────────────────────────┘
```

| Méthode | Rôle |
| :--- | :--- |
| `_registre` (propriété) | le registre complet **filtré par le rôle de la session** : c'est lui qui cloisonne Admin/Client |
| `_construire_barre_laterale()` | marque, label « NAVIGATION », les items du registre, pied « Déconnexion » |
| `_reconstruire_nav()` | vide puis recrée les items — appelée à chaque bascule de session |
| `changer_session(session)` | **la bascule** : détruit les écrans en cache, purge le bus (`reinitialiser()`) puis s'y ré-abonne, reconstruit nav + en-tête, ré-affiche le premier écran |
| `_choisir_session()` | ouvre `SelecteurSession` ; bascule si le choix a changé |
| `_maj_identite()` | pastille/nom/rôle de l'en-tête depuis la session |
| `_creer_item_nav(parent, entree)` | un item = cadre + **barre d'accent 3 px** (blanche à l'état actif) + étiquette ; survol/clic liés **récursivement** |
| `_maj_nav(survol_cle=None)` | recolore tous les items : actif (fond `NAVY_ITEM`, accent blanc, gras), survolé, normal |
| `_construire_zone_droite()` | en-tête + zone d'écrans + barre d'état (grille 3 lignes) |
| `_construire_entete(parent)` | titre + sous-titre de la page courante, puce utilisateur (initiales, nom, rôle), bouton **« Changer de vue »** (bascule d'espace), bouton Déconnexion |
| `_construire_barre_etat(parent)` | « ● Base : banque.db » à gauche, compteurs à droite |
| `afficher(cle)` | **le routeur** : crée l'écran à sa première visite (paresseux, avec `session=`), l'abonne au bus, masque le précédent, affiche le nouveau, met à jour titre/sous-titre/nav |
| `rafraichir()` | le shell **est abonné au bus** : met à jour les compteurs de la barre d'état après chaque modification |
| `_construire_raccourcis()` | `Ctrl+1..9` + `F5` ; les raccourcis résolvent l'écran **à l'index au moment de l'appui** (`_ouvrir_par_index`) : ils suivent les bascules de session sans re-binding |
| `_rafraichir_actif()` | recharge l'écran affiché + la barre d'état |
| `_sur_deconnexion()` | placeholder honnête : toast « reliera le module d'authentification » |

### 3.11 `app/ui/galerie_view.py` — la vitrine (écran de dév)

**`GalerieView(VueBase)`** — empile dans une `ZoneDefilante` sept
sections qui montrent **tous les composants dans tous leurs états** :
boutons (toutes variantes + désactivés), badges, cartes KPI, tableau
(remplir/vider/sélection/double-clic), saisie (erreurs inline, montant
1200,50 relu), retours (les 4 toasts + confirmation modale
autopilotée), graphique 14 jours.

Elle sert de **harnais de test visuel** : tout composant futur est
d'abord validé ici avant d'entrer dans un écran métier. À retirer (ou
réserver au rôle développeur) une fois les écrans définitifs.

### 3.12 `main.py` — l'assemblage

| Élément | Rôle |
| :--- | :--- |
| `NAVIGATION` | le **registre** : 8 `EntreeNav` — la seule liste d'écrans du projet (5 admin + 3 client), cloisonnés par `roles` |
| `Application.__init__` | données (`DatabaseManager`, schéma, seed au 1er lancement) → métier (`BankService`) → interface (`Tk`, `appliquer_theme`, `AppShell` avec `Session("admin")`, abonnement du shell au bus, affichage de l'accueil) |
| `Application.fermer()` | fermeture propre : **la base d'abord**, puis la fenêtre |
| `Application.demarrer()` | `mainloop()` |

Ordre imposé : `appliquer_theme(root)` **avant** tout widget, sinon les
premiers widgets naissent sans charte.

### 3.13 `app/ui/session.py` — les deux espaces (Admin / Client)

| Élément | Rôle |
| :--- | :--- |
| `Session(role, client=None)` | dataclass *frozen* : l'identité courante ; propriétés `libelle` (nom affiché), `sous_libelle` (rôle), `initiales` (pastille) |
| `SelecteurSession(parent, service, courante)` | modale « Changer de vue » : une ligne cliquable par espace (administrateur + un par client), badge « actuelle », teinte de survol ; choix dans `.resultat` |

La bascule détruit et reconstruit les écrans (voir `changer_session`
dans `shell.py`) : chaque espace ne voit que SES données — le client
lit via `read_comptes_par_client`, jamais la liste globale — mais les
deux espaces partagent le même `BankService` et la même base : une
opération saisie côté client est visible côté admin dès la bascule.
C'est le scénario de démonstration de la soutenance. Quand le module
d'authentification de l'équipe arrivera, il produira une `Session` à la
place du sélecteur : ni le shell ni les écrans ne changeront.

### 3.14 Écrans de l'espace client

| Fichier | Classe | Contenu |
| :--- | :--- | :--- |
| `mes_comptes_view.py` | `MesComptesView` | KPI (comptes actifs, encours) + tableau des comptes du client (comptes clôturés grisés) |
| `mes_operations_view.py` | `MesOperationsView` | combo des comptes + relevé complet : date française, type, détail (« Vers/Depuis CPT-xxxx » résolu par `jambes_virement`), montant **signé et coloré** (tags `credit`/`debit`), commentaire |
| `nouvelle_operation_view.py` | `NouvelleOperationView` + `_DialogueVirement` | combo des comptes ACTIFS, champ montant, boutons Déposer / Retirer, modale de virement (bénéficiaire désigné par **numéro**, résolu localement, erreurs inline) |

Toutes les actions passent par `BankService` (dépôt, retrait, virement)
puis `bus.publier()` : relevé, soldes et barre d'état se remettent à
jour instantanément — y compris côté admin dès qu'on rebascule.

---

## 4. Le trajet d'une action (traces complètes)

### 4.1 Modification de données — exemple d'un dépôt

```
Clic « Dépôt » (operations_view)
   └─► BankService.depot(numero, montant)
          ├─ validation métier (compte actif, montant > 0…)
          ├─ DatabaseManager.transaction() : INSERT opération + UPDATE solde
          └─ en cas d'erreur : rollback total + ErreurMetier
   └─► bus.publier()
          ├─ dashboard_view.rafraichir()   → KPI recalculés
          ├─ clients_view.rafraichir()     → listes rechargées
          ├─ comptes_view.rafraichir()     → soldes à jour
          ├─ operations_view.rafraichir()  → relevé à jour
          ├─ galerie_view.rafraichir()     → (rien, vitrine)
          └─ AppShell.rafraichir()         → compteurs barre d'état
   └─► toast de succès (« Dépôt effectué »)
```

**Aucune vue ne parle à une autre vue** : le bus est le seul canal.

### 4.2 Navigation — clic sur « Comptes »

```
Clic item barre latérale
   └─► AppShell.afficher("comptes")
          ├─ écran déjà construit ? sinon EntreeNav.classe(...) + abonnement
          ├─ pack_forget() de l'écran précédent / pack() du nouveau
          ├─ vue.rafraichir()
          └─ titre + sous-titre + recoloration de la nav (item actif)
```

### 4.3 Démonstration croisée Admin ↔ Client

```
« Changer de vue » → espace client (Alice)
   └─ Session("client", alice) → changer_session(session)
        ├─ destruction des 5 écrans admin + bus.reinitialiser()
        ├─ _reconstruire_nav() : 3 items client
        └─ afficher("mes_comptes")

Dépôt de 1 250,50 € (nouvelle_operation_view)
   └─ BankService.depot(id_compte, 1 250.50) → transaction
        ├─ INSERT opération + UPDATE solde
        └─ bus.publier() → mes_comptes, mes_operations, barre d'état

Retour « Administrateur »
   └─ changer_session(Session("admin")) → dashboard relu depuis la base :
      nb_operations +1, volume +1 250,50 € — MÊME base, aucun transfert.
```

---

## 5. Recettes ttk & pièges (les questions pièges de soutenance)

1. **`configure` vs `map`** : `configure` = apparence par défaut ;
   `map("TButton", background=[("pressed", …), ("active", …)])` =
   apparence **par état**. Un style sans `map` n'a pas d'états visuels.
2. **Grammaire des noms de style** : `"Primaire.TButton"` — la partie
   après le dernier point (`TButton`) est la **classe du widget** ;
   avant, c'est un nom libre. `TLabel`→`TLabel`, `Labelframe`→
   `TLabelframe` (f minuscule !), mais `Treeview` **sans** « T ».
   Une faute de nom = style silencieusement ignoré.
3. **Le style `"."`** configure les descendants : tout style non
   configuré hérite de `"."` (fond, police, couleur de texte).
4. **`clam`** : seul moteur ttk multiplateforme qui respecte
   `background`/`bordercolor` des boutons et champs. `vista`/`aqua`
   imposent le look système.
5. **Priorité des tags Treeview** : quand plusieurs tags définissent la
   même option, **le premier tag de la liste l'emporte**. C'est pourquoi
   le survol est inséré en tête : `["survol", "paire", …]`.
6. **Molette sous Linux** : les événements sont `<Button-4>` /
   `<Button-5>`, pas `<MouseWheel>` (Windows/macOS). Un gestionnaire
   global remonte la hiérarchie pour trouver la zone à faire défiler.
7. **Liste d'un Combobox** : c'est une Listbox Tk, invisible aux styles
   ttk → `root.option_add("*TCombobox*Listbox.background", …)`.
8. **Filets 1 px** : les `ttk.Frame` n'ont pas de bordure fine fiable →
   `tk.Frame(highlightthickness=1, highlightbackground=LINE)`.
9. **Fermetures en boucle** : dans `_creer_item_nav`, `c=cle` fige la
   variable — sans lui, toutes les lambdas partageraient la **dernière**
   clé (même principe pour `i=index - 1` dans les raccourcis).
10. **Modalité sans gel** : `grab_set` posé en différé (`after(40)`),
    jamais `wait_visibility()` — qui bloque si le WM tarde.
11. **ppp/familles** : les polices nommées (`tkfont.nametofont`) sont le
    seul moyen de styler *aussi* les dialogues système.
12. **Transparence de la gestion d'erreur** : `except ErreurMetier` +
    `str(exc)` affiché tel quel — les 9 exceptions spécialisées portent
    des messages français prêts à l'emploi.
13. **Police bitmap « fixed »** : si aucune famille de `FAMILLES`
    n'existe, Tk ne dit rien et peint `fixed`, illisible. Deux
    protections : détection **insensible à la casse** (`liberation
    sans` = `Liberation Sans`) et `lancer.sh` qui préfère un
    interpréteur au rendu lissé (fontconfig). Contrôle en une ligne :
    `tkinter.font.nametofont("TkDefaultFont").actual("family")`.
14. **Option Tk sur un widget ttk** : `ttk.Label(..., bg=…)` lève une
    `TclError` (« unknown option -bg ») *dans le rappel du bouton* — la
    fenêtre reste à moitié construite, sans message d'erreur visible.
    Un widget ttk se colore par **style**, pas par option ; pour un
    libellé posé à la main, on utilise `tk.Label`. C'est précisément ce
    qui cassait la modale « Ouvrir un compte » (champ solde et boutons
    jamais construits), réparé en la rebâtissant sur `Modale`
    (vérifié par le point « Modale ouverture » du parcours).

---

## 6. Feuille de route — les jalons « M0…M6 »

« M » = *milestone*, **jalon de construction** : chaque jalon livre
quelque chose d'utilisable et se vérifie (tests unitaires + parcours
fonctionnel + captures d'écran) avant de passer au suivant.

| Jalon | C'est quoi | Contenu | État |
| :--- | :--- | :--- | :--- |
| M0 | *Les fondations* — aucune fenêtre, seulement la charte | `theme.py` (jetons, polices, styles), `format.py`, `utilitaires.py` | ✅ fait |
| M1 | *La coquille* — l'application existe et navigue | `shell.py`, `base_view.py` (bus), `main.py` ; les 4 anciens écrans tournent dans le shell | ✅ fait |
| M2 | *Le kit* — les briques réutilisables + la vitrine | `components/*`, `galerie_view.py`, corrections (`<<ComboboxSelected>>`) | ✅ fait |
| M2.5 | *Les deux espaces* — Admin/Client et la démo croisée | `session.py`, les 3 écrans client, bascule à chaud, `lancer.sh` | ✅ fait |
| M3 | Redessiner Tableau de bord & Opérations sur le kit | — | prochain |
| M4 | Redessiner Clients & Comptes (fiches, filtres, badges) | — | à faire |
| M5 | Écrans du projet d'équipe : les 11 vues de `docs/user-interface.md` | — | à faire |
| M6 | Portage dans `Banking_System_Management/views/` + service factice | — | à faire |

---

## 7. Questions de soutenance (réponses préparées)

1. **« Pourquoi ttk et pas Qt/Tkinter moderne ? »** — ttk est dans la
   bibliothèque standard (zéro dépendance, déployable partout), clam
   permet une identité visuelle complète, et PySide6/CustomTkinter ont
   été évalués puis écartés : poids, licence, ou charte impossible à
   reproduire exactement (documenté au journal de conception).
2. **« Comment garantissez-vous la cohérence visuelle ? »** — un seul
   fichier de jetons (`theme.py`), un helper de police commun, des
   composants partagés ; les écrans n'ont plus aucun hexadécimal.
3. **« Pourquoi un bus plutôt que des rappels directs ? »** — découplage
   total : j'ajoute un écran sans toucher aux autres ; l'abonnement au
   bus suffit (ouvert/fermé = testable).
4. **« Que se passe-t-il si le service lève une erreur ? »** — elle est
   toujours une sous-classe d'`ErreurMetier` au message rédigé ; la vue
   affiche `str(exc)` ; aucune trace technique ne remonte.
5. **« Comment la sélection survit-elle à un rafraîchissement ? »** —
   l'iid du Treeview fige la clé métier (`id_cle="numero"`), la
   sélection se réapplique après rechargement.
6. **« Votre interface est-elle responsive ? »** — redimensionnement
   complet par grille/pack, colonnes élastiques, histogramme redessiné
   sur `<Configure>`, zone centrale défilante.
7. **« Comment avez-vous géré les différences Windows/Linux ? »** —
   détection de famille de polices, molette `<Button-4/5>`, options de
   style filtrées par helpers tolérants (Tk 8.6 → 9).
8. **« Où est la validation des montants ? »** — `extraire_montant`
   accepte les formats français (milliers, millions, `€`, virgule ou
   point), refuse proprement, et le champ affiche l'erreur sous
   lui-même ; le service revalide (jamais confiance au client).
9. **« Pourquoi des toasts plutôt que des `messagebox` ? »** —
   non bloquants, dans la charte, empilables ; les `messagebox`
   restaient hors identité visuelle et volaient le focus.
10. **« Prouvez que l'écran de dév. n'est pas du code mort. »** — la
    galerie est un harnais : chaque composant y est validé dans tous ses
    états ; elle se retire via le registre (une ligne).
11. **« Comment le rôle Client/Administrateur est-il géré ? »** —
    c'est fait : `Session` (rôle + client éventuel) + `EntreeNav.roles` ;
    le shell filtre le registre, la bascule est à chaud (« Changer de
    vue »), et les deux espaces partagent le même service.
12. **« Testez-vous l'interface ? »** — oui : **66 tests unitaires**
    (données + métier + relecture des montants), plus une vérification
    fonctionnelle de bout en bout (**80 points** : styles résolus,
    parcours des 8 écrans des deux espaces, ouverture de compte par sa
    modale, sélection, validation, toasts, modales, dépôt et virement
    réels côté client puis contrôle côté admin) exécutée à chaque jalon.
13. **« Comment fonctionne l'espace client ? »** — `Session` porte le
    rôle et le client ; le registre est filtré (`EntreeNav.roles`) ;
    `changer_session()` détruit les écrans de l'autre espace, purge le
    bus et reconstruit la navigation. Un client ne lit que ses comptes
    (`read_comptes_par_client`), mais les deux espaces partagent la
    même base : une opération saisie côté client se voit côté admin dès
    la bascule ; le futur module d'authentification produira la
    `Session` à la place du sélecteur.
