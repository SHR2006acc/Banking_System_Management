# Couche interface — documentation technique (Rôle 3)

Ce document décrit l'implémentation de la couche interface : l'organisation
des fichiers, la responsabilité de chaque module, le contrat de chaque
classe et le cheminement des données à l'écran. Il complète
`docs/project-architecture.md` (architecture générale du système) et
`docs/user-interface.md` (maquettes et écrans cibles).

---

## 1. Position et règles de dépendance

L'interface est le troisième sous-système du projet (données → traitements →
interface). Elle s'assemble dans `main.py` :

```
   main.py                        assemble les trois couches
      │
      ├── DatabaseManager         (rôle 1 : SQLite, transactions)
      ├── BankService             (rôle 2 : règles de gestion, exceptions)
      └── AppShell                (rôle 3 : la couche décrite ici)
```

Deux règles structurent tout le code de la couche :

1. **Une vue ne contacte jamais la base directement.** Elle appelle
   `BankService`, attrape les exceptions métier (`ErreurMetier` et filles)
   et les affiche. Aucun SQL, aucun import de `sqlite3` dans `app/ui/`.
2. **Les couleurs ne vivent que dans `theme.py`.** Tout autre fichier
   importe les jetons (`T.NAVY`, `T.SURFACE`…) : la charte a une source
   unique.

Arborescence de `app/ui/` :

```
app/ui/
├── theme.py              charte : jetons de couleur, polices, styles ttk
├── format.py             formatage des montants/dates + relecture de saisie
├── utilitaires.py        helpers Tk génériques
├── base_view.py          bus d'événements + classe mère des écrans
├── session.py            session (rôle + client) + sélecteur d'espace
├── shell.py              coquille : barre latérale, en-tête, routeur
│
├── components/           bibliothèque de composants réutilisables
│   ├── cartes.py         Carte, CarteKPI
│   ├── tableaux.py       Tableau (Treeview habillé)
│   ├── champs.py         Champ, ChampMontant, Badge
│   ├── retours.py        Modale, ConfirmationModale, toasts
│   ├── graphiques.py     GraphiqueBarres (Canvas)
│   └── defilement.py     ZoneDefilante (conteneur défilant)
│
├── écrans administrateur (roles=("admin",))
│   ├── dashboard_view.py         tableau de bord
│   ├── clients_view.py           CRUD clients
│   ├── comptes_view.py           comptes (filtre, ouverture, clôture)
│   └── operations_view.py        dépôt / retrait / virement + relevé
│
└── écrans client (roles=("client",))
    ├── mes_comptes_view.py       comptes du client connecté
    ├── mes_operations_view.py    relevé du compte sélectionné
    └── nouvelle_operation_view.py déposer / retirer / virer
```

Dépendances (aucune dépendance inverse) :

```
main.py
  └─ shell.py ──────────► base_view.py ──► format.py
       │                     │
       │                     ├──► services/exceptions.py
       │                     └──► session.py (rôle + client)
       ├─ components/*  ──► theme.py (jetons + helpers)
       └─ *_view.py     ──► base_view.py, format.py, components/*
```

`theme.py` n'importe aucun autre module de l'interface ; tous les autres
en dépendent.

---

## 2. Design system — `theme.py`

### 2.1 Jetons de couleur

Table complète des constantes. Changer une valeur ici se propage à toute
l'application.

| Famille | Jeton | Valeur | Usage |
| :--- | :--- | :--- | :--- |
| Texte | `INK` | `#0E1B2C` | texte principal |
| | `INK_SOFT` | `#55657A` | libellés de formulaire |
| | `MUTED` | `#6E7F92` | légendes discrètes |
| Fonds | `BG` | `#F3F5F7` | fond de page |
| | `SURFACE` | `#FFFFFF` | cartes, en-têtes, tableaux |
| | `SURFACE_ALT` | `#FAFBFC` | lignes paires des tableaux |
| | `SURVOL` | `#F1F5F9` | survol de ligne |
| Filets | `LINE` | `#E3E8EE` | filet 1 px des cartes |
| | `LINE_STR` | `#CBD4DE` | bordure des champs |
| Marque | `NAVY` | `#123C6B` | actions primaires, titres |
| | `NAVY_HOVER` / `NAVY_PRESSED` | `#0E3058` / `#0A2545` | états du bouton |
| | `NAVY_DEEP` | `#0F2743` | fond de la barre latérale |
| | `NAVY_ITEM` | `#16375B` | item actif/survolé de la navigation |
| | `NAVY_TINT` | `#E9F0F7` | teinte de sélection |
| Sémantique | `POS` / `POS_TINT` | `#12703C` / `#E7F4EC` | crédit, succès |
| | `NEG` / `NEG_TINT` | `#B3261E` / `#FBEAE9` | débit, danger |
| | `WARN` / `WARN_TINT` | `#8A5A00` / `#FCF3E3` | avertissement, client suspendu |
| Technique | `FOCUS` | `#1E66C9` | anneau de focus clavier |
| | `DESACTIVE` | `#9FB3C8` | bouton désactivé |
| | `SURFACE_NEUTRE` | `#EAEEF3` | bouton secondaire |

Direction artistique : aplats et filets de 1 px, aucun dégradé ni arrondi ;
le bleu marine porte l'identité, les couleurs vert/rouge/ambre signalent
exclusivement un sens métier (crédit, débit, état, alerte).

### 2.2 Détection de police — `detecter_famille(root) -> str`

Parcourt `FAMILLES = ("Segoe UI", "Inter", "Noto Sans", "Cantarell",
"Liberation Sans", "Ubuntu", "DejaVu Sans")` et renvoie la première
famille installée sur la machine. La comparaison est **insensible à la
casse** : Tk retourne les familles en minuscules sous X11
(`liberation sans`), alors que la charte les écrit en capitales — sans
cette normalisation, la détection échoue et Tk retombe sur sa police
bitmap `fixed`, illisible. Résultat : Segoe UI sous Windows, Noto Sans ou
Cantarell sous KDE, Liberation/DejaVu ailleurs, sans configuration.

### 2.3 Helper de police — `police(taille, gras=False) -> tuple`

Renvoie le descripteur `(famille, taille, "bold"/"normal")`. Les widgets
Tk purs (`tk.Label`, `tk.Canvas`…) ignorent les styles ttk : ce helper est
le seul moyen de leur appliquer la même famille que le reste de la charte.

### 2.4 Feuille de styles — `appliquer_theme(root) -> ttk.Style`

Séquence d'application :

1. détection de la famille (`_FAMILLE` global) ;
2. configuration des **polices nommées** (`TkDefaultFont`, `TkTextFont`,
   `TkMenuFont`, `TkHeadingFont`) — les widgets sans style explicite, les
   listes déroulantes et les dialogues système en héritent ;
3. `style.theme_use("clam")` : le moteur ttk qui honore `background` et
   `bordercolor` de façon identique sous Windows, Linux et macOS ;
4. configuration du style racine `"."` (valeurs par défaut de tous les
   styles) ;
5. déclaration des styles nommés ci-dessous.

Les helpers `_configurer(style, nom, **options)` et `_mapper(style, nom,
**options)` appliquent chaque option individuellement et ignorent les
options absentes du moteur Tk courant (`bordercolor`, `focuscolor`…
n'existent que depuis Tk 8.6.10). La même base de code fonctionne de
Tk 8.6 à Tk 9 sans plantage.

| Style | Usage | États (`map`) |
| :--- | :--- | :--- |
| `Titre.TLabel` / `SousTitre.TLabel` / `Champ.TLabel` | titres et libellés | — |
| `Indicateur.TLabel` | grand chiffre KPI | — |
| `CarteTitre.TLabel` / `Vide.TLabel` | légende de carte / état vide | — |
| `Carte.TLabelframe` (+ `.Label`) / `Carte.TFrame` / `Carte.TLabel` | fonds blancs des cartes | — |
| `Formulaire.TLabel` / `.TEntry` / `.TCombobox` | formulaires | — |
| `TEntry` / `TCombobox` | champs de saisie | focus → bordure `FOCUS` |
| `Primaire.TButton` (alias `Action.TButton`) | action principale (navy) | active / pressed / disabled |
| `Succes.TButton` / `Danger.TButton` | valider (vert) / destructif (rouge) | idem |
| `Secondaire.TButton` | action neutre (gris) | idem |
| `Lien.TButton` | lien discret | active / pressed |
| `BadgeActif/Suspendu/Cloture/Neutre/Danger.TLabel` | badges d'état | — |
| `Treeview` / `Treeview.Heading` | tableaux | selected → `NAVY_TINT` |
| `Vertical.TScrollbar` / `TSeparator` | finitions | active |
| `TNotebook` / `TNotebook.Tab` | onglets (héritage) | selected |

Cas particulier : la liste déroulante d'un `ttk.Combobox` est une
`Listbox` Tk classique, hors de portée des styles ttk. Elle se configure
par la base d'options :

```python
root.option_add("*TCombobox*Listbox.background", SURFACE)
root.option_add("*TCombobox*Listbox.selectBackground", NAVY)
```

---

## 3. Socle des vues — `base_view.py`

| Élément | Description |
| :--- | :--- |
| `Rafraichissable` (Protocol) | contrat minimal : un objet qui implémente `rafraichir()`. Les vues et le shell s'y conforment ; le bus ne connaît que ce contrat |
| `BusRafraichissement` | distributeur d'événement « la base a changé » : `abonner()`, `publier()` (appelle `rafraichir()` de tous les abonnés), `reinitialiser()` (vide la liste — utilisé à la bascule de session) |
| `VueBase(ttk.Frame)` | classe mère de tous les écrans. Le constructeur reçoit `(parent, service, bus, session=None)`, appelle `_construire()` puis `rafraichir()` |
| `VueBase.signaler_erreur(err)` | mapping exception → boîte d'erreur : `EntreeInvalideError` → titre « Saisie invalide », sinon « Opération refusée » ; le message affiché est `str(err)` |
| `VueBase.vider(arbre)` | vide un `Treeview` |

Attributs de classe spécialisés par chaque écran : `titre_onglet`,
`titre_page` (en-tête du shell), `sous_titre` (phrase d'aide).

Le bus applique le patron observateur/observé : après chaque modification
réussie, `bus.publier()` resynchronise toutes les vues construites ainsi
que la barre d'état du shell. Aucune vue ne communique avec une autre
directement.

---

## 4. Coquille applicative — `shell.py`

### 4.1 Registre de navigation

`EntreeNav(cle, libelle, classe, roles=("admin",))` — dataclass figée qui
décrit un écran. Le registre complet est déclaré dans `main.py`
(`NAVIGATION`) et constitue la source unique de la navigation : ajouter un
écran revient à y ajouter une ligne. Le champ `roles` implémente le
cloisonnement des espaces.

### 4.2 Structure visuelle

```
┌───────────┬───────────────────────────────────────┐
│           │  en-tête : titre de page + utilisateur │
│  barre    ├───────────────────────────────────────┤
│  latérale │                                       │
│  (navy)   │   zone des écrans (routeur)            │
│           │                                       │
│           ├───────────────────────────────────────┤
│           │  barre d'état : base + compteurs       │
└───────────┴───────────────────────────────────────┘
```

### 4.3 Méthodes principales

| Méthode | Description |
| :--- | :--- |
| `_registre` (propriété) | registre complet filtré par le rôle de la session courante — c'est ce filtre qui cloisonne Admin/Client |
| `afficher(cle)` | routeur : instancie l'écran à sa première visite (instanciation paresseuse, avec `session=`), l'abonne au bus, masque le précédent (`pack_forget`), affiche le nouveau, met à jour titre, sous-titre et navigation |
| `changer_session(session)` | bascule d'espace : détruit les écrans en cache, purge le bus puis s'y ré-abonne, reconstruit la navigation et l'en-tête, affiche le premier écran du nouveau registre |
| `_choisir_session()` | ouvre `SelecteurSession` et bascule si le choix a changé |
| `_maj_nav(survol_cle)` | recolore les items de navigation selon leur état (actif, survolé, normal) |
| `rafraichir()` | abonné au bus : recalcule les compteurs de la barre d'état (`service.statistiques()`) |
| `_construire_raccourcis()` | `Ctrl+1..9` (ouvre le n-ième écran du registre filtré) et `F5` (recharge l'écran affiché) |

La navigation est reconstruite à chaque bascule : les items sont composés
(cadre + barre d'accent 3 px + étiquette) et leurs événements sont liés
récursivement (voir `lier_recursif`) pour que le survol ne s'interrompe
pas entre les sous-widgets.

---

## 5. Session et espaces — `session.py`

| Élément | Description |
| :--- | :--- |
| `Session(role, client=None)` | dataclass figée : identité courante. Propriétés `libelle` (nom affiché dans l'en-tête), `sous_libelle` (rôle), `initiales` (pastille) |
| `SelecteurSession(parent, service, courante)` | modale « Changer de vue » : une ligne par espace (administrateur, puis un par client), badge « actuelle » sur l'espace courant, choix renvoyé dans `.resultat` |

Les écrans client restreignent leur périmètre via la session :
`read_comptes_par_client(self.session.client.id_client)` — jamais la liste
globale. Les deux espaces partagent le même `BankService` et la même base ;
une opération saisie côté client est donc visible côté administrateur dès
la bascule, sans transfert ni synchronisation particulière.

Le futur module d'authentification produira une `Session` à la place du
sélecteur ; ni le shell ni les écrans ne devront changer.

---

## 6. Bibliothèque de composants — `components/`

Chaque classe encapsule une brique de la charte ; les écrans ne
reproduisent jamais ces réglages à la main.

### 6.1 `cartes.py`

**`Carte(parent, titre=None, accent=None, padding=16)`** — panneau blanc à
filet 1 px (`highlightthickness=1`, car un `tk.Frame` sait s'encadrer alors
qu'un `ttk.Frame` non). Expose `carte.corps` (contenu) et `carte.actions`
(zone d'en-tête à droite). Barre d'accent 2 px optionnelle.

**`CarteKPI(parent, libelle, valeur, accent)`** — carte d'indicateur :
légende en majuscules, grande valeur 24 pt gras, sous-texte ;
`definir(valeur, sous=None)` met le contenu à jour sans reconstruction.

### 6.2 `tableaux.py`

**`Tableau(parent, colonnes, hauteur=10, texte_vide=…)`** — habillage d'un
`ttk.Treeview` : lignes zébrées (tag `paire`), survol teinté, sélection
`NAVY_TINT`, état vide intégré. Chaque colonne est un tuple
`(cle, entete, largeur, ancre)` ; la dernière colonne s'étire à la
redimension. Le tableau ne formate rien : les valeurs reçues sont déjà du
texte d'affichage.

| Méthode | Description |
| :--- | :--- |
| `remplir(lignes, id_cle=None, tags_fn=None)` | remplace tout le contenu. `id_cle` fixe l'iid de chaque ligne à une clé métier (`"numero"`…) : la sélection survit aux rechargements. `tags_fn(ligne)` teinte les lignes (`credit`, `debit`, `desactive`) |
| `vider()` | supprime toutes les lignes, affiche l'état vide |
| `selection()` / `ligne_selectionnee()` | iid courant / dictionnaire de données de la ligne sélectionnée |
| `sur_selection(rappel)` / `sur_double_clic(rappel)` | abonnements aux interactions |

Détail d'implémentation : en Treeview, quand plusieurs tags définissent la
même option, le premier de la liste l'emporte. Le tag `survol` est donc
inséré en tête de liste, avant `paire` et les tags sémantiques.

### 6.3 `champs.py`

**`Champ(parent, libelle, obligatoire=False, …)`** — libellé + `ttk.Entry`
+ ligne d'erreur inline (`afficher_erreur` / `effacer_erreur`, masquée par
défaut). L'erreur s'affiche sous le champ : l'utilisateur corrige sans
perdre le contexte, sans boîte de dialogue.

**`ChampMontant(Champ)`** — montant aligné à droite avec suffixe « € »,
filtre de frappe (chiffres, espaces et séparateurs uniquement) et
`valeur()` qui relit et valide via `extraire_montant`.

**`Badge(parent, texte, ton)`** — étiquette d'état en majuscules sur fond
teinté. Tons : `actif`, `suspendu`, `cloture`, `neutre`, `danger`.
`ton_pour_statut(statut)` centralise la correspondance statut métier → ton
(`"ACTIF"` → `"actif"`…).

### 6.4 `retours.py`

**`Modale(parent, titre)`** — base des fenêtres modales de la charte.
`transient` + `grab_set` bloquent la fenêtre mère ; `afficher()` centre sur
la mère puis pose le focus **en différé** (`after(40, …)`) —
`wait_visibility()` n'est pas utilisé car il peut geler l'application si le
gestionnaire de fenêtres tarde ; `attendre()` bloque l'appelant jusqu'à la
fermeture ; `fermer()` libère le grab puis détruit. `Échap`, le bouton `✕`
et la fermeture système passent tous par `fermer()`.

Les modales à formulaire (ouverture de compte, virement client)
sous-classent `Modale`, remplissent `corps` et `pied`, mémorisent leur
verdict dans `self.resultat` avant `fermer()`. Une erreur métier affichée
sous le champ concerné laisse la modale ouverte.

**`ConfirmationModale(parent, titre, message, texte_confirmer,
danger=True)`** — question Confirmer/Annuler renvoyant un booléen, avec
raccourci de classe :

```python
if ConfirmationModale.demander(self, "Clôture",
        "Clôturer définitivement CPT-0004 ?", texte_confirmer="Clôturer"):
    ...
```

**`afficher_toast(parent, message, ton="succes", duree=3600)`** —
notification non bloquante en bas à droite : barre d'accent selon le ton
(`succes`, `erreur`, `info`, `avertissement`), empilement vertical des
toasts encore visibles, disparition automatique, fermeture au clic.

### 6.5 `graphiques.py`

**`GraphiqueBarres(parent, hauteur=150, couleur=NAVY)`** — histogramme
dessiné sur `tk.Canvas`, entièrement en bibliothèque standard (aucune
dépendance graphique externe). `definir([(etiquette, valeur), …])`
remplace les données ; `_tracer()` redessine, valeurs affichées jusqu'à
8 barres ; le redessin est déclenché automatiquement sur `<Configure>`,
donc suit les redimensionnements de la fenêtre.

### 6.6 `defilement.py`

**`ZoneDefilante(parent)`** — conteneur défilant vertical. Tk ne fournit
pas de « frame scrollable » : la recette associe un `tk.Canvas`, une
`ttk.Scrollbar` et une frame interne (`zone.contenu`) dont la largeur suit
celle du canvas (`scrollregion` mise à jour sur `<Configure>`).

La molette est gérée par **un seul gestionnaire global**
(`bind_all` sur `<MouseWheel>`, `<Button-4>`, `<Button-5>`) qui remonte la
hiérarchie du widget survolé jusqu'à la zone défilante le contenant
(attribut marqueur `_zone_defilante`). Sous Linux/X11, la molette émet
`<Button-4>`/`<Button-5>` plutôt que `<MouseWheel>` — les trois séquences
sont donc couvertes.

---

## 7. Formatage — `format.py`

Fonctions partagées par les 8 écrans (cohérence par construction) :

| Fonction | Description |
| :--- | :--- |
| `fmt_montant(valeur)` | `1500.0` → `« 1 500,00 € »` (espace des milliers, virgule décimale) |
| `fmt_entier(valeur)` | `1234` → `« 1 234 »` |
| `fmt_date(texte)` | `« 2026-10-18 14:32:05 »` → `« 18/10/2026 14:32 »` ; renvoie `« — »` si absent, le texte brut si le format n'est pas reconnu |
| `extraire_montant(texte, zero_autorise=False)` | relit une saisie humaine → `float`, valide (`> 0`, ou `≥ 0` avec `zero_autorise=True` pour un solde initial), lève `EntreeInvalideError` avec un message français prêt à afficher |

Grammaire acceptée par `extraire_montant` : `1 250,50`, `1250.5`,
`1000000`, `1.000` (= 1 000), `1.000.000`, `1.000.000,50`,
`1,000,000.50` — quand les deux séparateurs sont présents, le plus à
droite est la décimale et l'autre est traité comme séparateur de milliers.
Suffixe `€` et espaces (y compris insécables) tolérés ; toute saisie
ambiguë (`12,34,56`) est refusée. Une vingtaine de tests dédiés couvrent
cette grammaire (`tests/test_formats.py`).

## 8. Helpers Tk — `utilitaires.py`

| Fonction | Description |
| :--- | :--- |
| `lier_recursif(fenetre, sequence, rappel)` | lie un événement au widget **et à tous ses descendants présents** : indispensable pour les zones cliquables composites (item de navigation = cadre + barre + étiquette), sinon le survol s'interrompt à chaque passage d'un enfant à l'autre |
| `centrer_fenetre(fenetre, largeur, hauteur)` | calcule et applique la géométrie centrée (léger décalage vers le haut) |

---

## 9. Écrans

Chaque écran hérite de `VueBase`, implémente `_construire()` (widgets) et
`rafraichir()` (rechargement depuis le service), publie via `bus.publier()`
après chaque modification réussie.

### 9.1 Espace administrateur

| Fichier | Classe | Contenu |
| :--- | :--- | :--- |
| `dashboard_view.py` | `DashboardView` | quatre indicateurs (clients, comptes actifs, encours, volume) issus de `service.statistiques()` + les 10 derniers mouvements (`service.operations_recentes`) |
| `clients_view.py` | `ClientsView` | fiche de saisie (nom, prénom, CIN, téléphone, email, statut) + tableau complet ; clic sur une ligne → la fiche se recharge ; Ajouter/Modifier/Supprimer passent par le service, erreurs affichées via `signaler_erreur` |
| `comptes_view.py` | `ComptesView` + `_DialogueOuverture` | filtre par titulaire (combobox), ouverture via modale (type + solde initial, erreurs inline, client suspendu refusé par le service), clôture protégée (confirmation modale, refus si solde non nul) |
| `operations_view.py` | `OperationsView` | cartes Dépôt / Retrait / Virement + relevé filtrable par compte ; le relevé distingue les jambes d'un virement (« vers CPT-0002 » / « depuis CPT-0002 ») avec montant signé et coloré |

### 9.2 Espace client

| Fichier | Classe | Contenu |
| :--- | :--- | :--- |
| `mes_comptes_view.py` | `MesComptesView` | KPI (comptes actifs, encours) + tableau des comptes du client, comptes clôturés grisés |
| `mes_operations_view.py` | `MesOperationsView` | combobox des comptes + relevé détaillé : détail résolu par `jambes_virement`, montant signé, tags `credit`/`debit` |
| `nouvelle_operation_view.py` | `NouvelleOperationView` + `_DialogueVirement` | comptes ACTIFS du client, `ChampMontant`, dépôt/retrait, modale de virement désignant le bénéficiaire par numéro de compte (résolution locale, erreurs inline) |

---

## 10. Assemblage — `main.py`

| Élément | Description |
| :--- | :--- |
| `NAVIGATION` | le registre : quatre écrans administrateur + trois écrans client, cloisonnés par `roles` |
| `Application.__init__` | ordre d'assemblage : `DatabaseManager` (schéma + données de démonstration au premier lancement) → `BankService` → fenêtre `Tk` → `appliquer_theme(root)` **avant tout widget** → `AppShell` avec `Session("admin")` → abonnement au bus → affichage du tableau de bord |
| `Application.fermer()` | fermeture propre : la base d'abord, puis la fenêtre (`Ctrl+Q` ou fermeture système) |

---

## 11. Parcours de données

### 11.1 Modification — exemple d'un dépôt

```
Clic « Encaisser » (operations_view)
   └─► BankService.depot(numero, montant)
          ├─ validation métier (compte opérable, montant > 0)
          ├─ DatabaseManager.transaction() : UPDATE solde + INSERT opération
          └─ en cas d'erreur : rollback + ErreurMetier
   └─► bus.publier()
          ├─ dashboard_view.rafraichir()   → KPI recalculés
          ├─ comptes_view.rafraichir()     → soldes à jour
          ├─ operations_view.rafraichir()  → relevé à jour
          └─ AppShell.rafraichir()         → compteurs de la barre d'état
   └─► toast de succès
```

### 11.2 Navigation — clic sur « Comptes »

```
Clic item barre latérale
   └─► AppShell.afficher("comptes")
          ├─ écran déjà construit ? sinon EntreeNav.classe(...) + abonnement au bus
          ├─ pack_forget() de l'écran précédent / pack() du nouveau
          ├─ vue.rafraichir()
          └─ titre + sous-titre + item actif recoloré
```

### 11.3 Bascule Admin ↔ Client

```
« Changer de vue » → espace client
   └─ Session("client", client) → changer_session(session)
        ├─ destruction des écrans admin + bus.reinitialiser()
        ├─ _reconstruire_nav() : 3 items client
        └─ afficher("mes_comptes")

Dépôt côté client
   └─ BankService.depot(id_compte, montant) → transaction → bus.publier()

Retour « Administrateur »
   └─ changer_session(Session("admin")) → écrans reconstruits depuis la
      base : l'opération saisie côté client est dans le relevé admin.
```

---

## 12. Contraintes techniques Tk

Notes de mise en œuvre — chaque point correspond à un comportement
observé du moteur Tk et à la réponse du code :

1. **`configure` vs `map`** : `style.configure()` fixe l'apparence par
   défaut ; `style.map()` fixe l'apparence par état (`active`, `pressed`,
   `disabled`). Un style sans `map` n'a pas d'états visuels.
2. **Noms de styles** : dans `"Primaire.TButton"`, la partie après le
   dernier point est la classe du widget ; une faute dans cette partie
   (`TLabelframe` avec « f », `Treeview` sans « T ») rend le style
   silencieusement inopérant.
3. **Style racine** : tout style non configuré hérite de `"."`.
4. **Moteur `clam`** : seul moteur ttk dont les couleurs et bordures se
   comportent de façon identique sur les trois plateformes.
5. **Priorité des tags Treeview** : à options égales, le premier tag de la
   liste l'emporte.
6. **Molette X11** : `<Button-4>`/`<Button-5>` au lieu de `<MouseWheel>`.
7. **Liste déroulante du Combobox** : Listbox Tk hors des styles ttk →
   `option_add`.
8. **Filets 1 px** : les `ttk.Frame` n'offrent pas de bordure fine fiable ;
   on utilise `tk.Frame(highlightthickness=1, highlightbackground=…)`.

9. **Fermetures en boucle** : dans les lambdas créées en boucle
   (`c=cle`, `i=index-1`), la valeur est figée au moment de la création —
   sans elle, toutes les lambdas partageraient la dernière valeur.
10. **Modalité sans gel** : `grab_set` posé en différé via `after(40)`,
    jamais en dépendant de `wait_visibility()`.
11. **Polices nommées** : `tkfont.nametofont(...)` est le seul moyen de
    styliser aussi les dialogues système.
12. **Option Tk sur widget ttk** : `ttk.Label(..., bg=…)` lève une
    `TclError` au moment de la construction, laissant la fenêtre à moitié
    construite. Un widget ttk se colore par style ; les libellés posés à
    la main utilisent `tk.Label` (option `bg` valide).
13. **Police bitmap `fixed`** : si aucune famille de `FAMILLES` n'est
    trouvée, Tk peint `fixed` sans avertissement. Protections : détection
    insensible à la casse et `lancer.sh`, qui choisit l'interpréteur dont
    Tk voit le plus de polices (fontconfig).

---

## 13. Tests et vérifications

| Outil | Périmètre |
| :--- | :--- |
| `python3 -m unittest discover -s tests` | 66 tests unitaires : DAO (16), règles métier (29), formatage et relecture des montants (21) |
| `python3 outils/verif_fonctionnelle.py` | parcours de bout en bout sur une base temporaire : charte résolue, relecture des montants, les 7 écrans des deux espaces, ouverture de compte par sa modale, bascule de session, dépôt et virement réels côté client puis contrôle côté admin |
| `python3 outils/capture_ecrans.py` | capture des écrans vers `captures/` pour le rapport |

Ces vérifications s'exécutent sans dépendance externe, comme
l'application elle-même.
