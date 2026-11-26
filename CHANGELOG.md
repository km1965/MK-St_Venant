# Changelog — MK-St_Venant

Toutes les versions notables de l'application sont documentées ici.

## v1.2.0 — 2026-11-26

### Catalogue des organes d'air
- **Nouvelle base catalogue MCP** issue de `Tableau_Recapitulatif_Debits_Ventouses_MCP.xlsx` : 11 DN, courbes grand/petit orifice, dimensions, poids, débits critiques et montages en chandelier (DN conduite > 900 mm).
- La base MCP est sélectionnable dans le Tableau de bord, le Simulateur de casse franche et la vue Catalogue, aux côtés de CEAI/SNH et PAM/SNH.
- Dimensionnement MCP à 0,3 bar en admission (≈ 3 mCE) et 0,1 bar en évacuation (≈ 1 mCE) ; les valeurs critiques −0,5 bar / +0,9 bar sont affichées à titre d'information.
- Nouvel onglet « Ventouses MCP (Excel) » et catalogue MCP ajouté à l'export Excel.

### Données du projet & rapports
- Nouvel onglet **« Données du Projet »** : MO, maîtrise d'œuvre, BET, lieu/commune/province/pays, marché, responsable, date, référence, introduction et préambule.
- Ces informations alimentent la section 1 du rapport Word et la feuille « Données Projet » de l'export Excel ; un texte standard est généré si les champs sont vides.
- Persistance `.mkst.json` et import Excel prennent en charge l'identité du projet.

### Matériaux
- Ajout du **PVC (Polychlorure de Vinyle)** : `E = 3 GPa`, `Ks = 100`, disponible dans le dashboard, le simulateur et le catalogue.

### Vidanges — temps cible et DN retenu
- **Suppression de toute valeur figée à 2 h** : le coefficient de la formule de diamètre est recalculé pour le temps cible saisi (6,693 à 2 h, 9,465 à 1 h, 13,386 à 30 min).
- **Le DN recommandé est imposé comme DN retenu en mode auto** : il suit automatiquement le temps cible. Un mode manuel reste disponible (case dans la boîte de dialogue d'un point bas, bouton « Tester DN 400 Uniformisé ») ; les anciens projets avec DN manuel sont préservés.
- Libellés dynamiques dans le tableau de bord, la vue Vidanges, le rapport Word et l'export Excel.
- L'import Excel restaure désormais les paramètres généraux, dont le temps objectif (auparavant réinitialisé à 2 h).

### Livrable
- Exécutable Windows PyInstaller régénéré en v1.2.0, avec catalogue MCP embarqué pour traçabilité.
