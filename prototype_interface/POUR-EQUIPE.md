# Pour l'équipe — prototype d'interface (Rôle 3)

> **Rôle 3 — prototype d'interface, exécutable tout de suite.**
> Tout ce dossier est **à revoir puis à porter** : `views/`, `services/` et `dao/`
> de la structure cible ne sont pas touchés. Bonne lecture !

## En 30 secondes

- **Ce que c'est** : l'application côté interface — espace **Administrateur** et
  espace **Client**, charte graphique maison (pas de TTK par défaut), navigation,
  formulaires, modales, tableaux, notifications *toast*.
- **Comment lancer** (stdlib uniquement, rien à installer) :
  - Linux : `cd prototype_interface && ./lancer.sh`
  - Sinon : `python3 main.py` (Windows : `python main.py`)
- La base de démonstration **`banque.db` se crée et se peuple toute seule** au
  premier lancement (elle n'est pas versionnée). Pour repartir de zéro :
  supprimer `banque.db` puis relancer.

## Démo de 5 minutes (ce qu'il faut regarder)

1. **Administrateur** : Tableau de bord → Clients → Comptes → Opérations.
   - « Comptes » : choisir un titulaire → **« Ouvrir un compte… »** → modale
     complète (type, solde initial, validation, erreurs inline).
2. **Bascule client** : bouton « Changer de vue » (en haut à droite) → choisir
   un client → Mes comptes → Mes opérations → **Nouvelle opération**.
   - Y faire un **dépôt** (ex. `1 250,50`) puis un **virement** vers un autre compte.
3. **Retour administrateur** → Opérations : le dépôt et les **deux écritures** du
   virement sont là → *une opération saisie côté client est visible côté admin,
   même service, même base.* C'est le scénario de soutenance.

![Tableau de bord](captures/dashboard.png)

![Ouverture d'un compte](captures/comptes-ouverture.png)

## Vérifications automatiques

```bash
python3 -m unittest discover -s tests      # 66 tests unitaires
python3 outils/verif_fonctionnelle.py      # parcours de bout en bout : 80/80
```

## Où lire le code

| Fichier | Contenu |
| :--- | :--- |
| `docs/interface.md` | tout, **fichier par fichier, fonction par fonction** (support de soutenance) |
| `README.md` | le rapport complet du prototype (avec les captures) |
| `captures/` | les écrans en images |

## Important : l'échafaudage `app/`

Pour que l'interface tourne **sans dépendre de personne**, le prototype embarque une
implémentation de démonstration (`app/db/`, `app/dao/`, `app/models/`, `app/services/`).
L'interface ne consomme que **`BankService`** (+ les dataclasses) — le contrat utilisé
est celui que les écrans attendent. **La version finale branche le service de l'équipe** :
c'est tout l'objet du portage ci-dessous.

## Suite proposée (portage vers la structure cible)

| Prototype (ici) | Cible (`docs/project-architecture.md` §11) |
| :--- | :--- |
| `app/ui/shell.py` | `main.py` (navigation, en-tête, barre d'état) |
| `app/ui/dashboard_view.py` | `views/dashboard_view.py` |
| `app/ui/clients_view.py` | `views/clients_view.py` |
| `app/ui/comptes_view.py` | `views/comptes_view.py` |
| `app/ui/operations_view.py` | `views/operations_view.py` |
| `app/ui/mes_comptes_view.py`, `mes_operations_view.py`, `nouvelle_operation_view.py` | espace client (`views/…`) |
| `app/ui/theme.py`, `format.py`, `components/`, `base_view.py` | kit partagé de l'interface |

Il reste à couvrir côté interface : accueil, authentification, inscription, profil,
historique filtré, rapports, paramètres (la suite du planning Rôle 3).
