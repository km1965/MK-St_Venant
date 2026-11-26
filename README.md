# MK-St_Venant — Automatisation & Vérifications Hydrauliques des Ventouses et Vidanges

> **Version courante : 1.2.0** — voir [CHANGELOG.md](CHANGELOG.md).

Application Python 3.10 – 3.14 avec interface graphique moderne **CustomTkinter** dédiée au dimensionnement, à la vérification et à l'audit hydraulique des organes de sécurité (points hauts et points bas) pour les adductions d'eau (BR3_LOT 8 et tout projet d'adduction sous pression).

L'application intègre les **formules physiques exactes corrigées**, rectifiant l'ensemble des erreurs décelées dans les notes d'entreprises antérieures (coefficients de vidange erronés, célérité d'Allievi, loi compressible de Saint-Venant, calculs de dépression motrice en casse franche).

---

## 🚀 Fonctionnalités Principales

### 1. 🌬️ Points Hauts (Ventouses & Clapets d'admission)
- **Fonction 1 — Dégazage en service continu** : Débit d'air dissous à évacuer sous pression de service ($2\%$ du débit d'eau nominal). Vérification du claquage de la bille pour limiter les surpressions locales ($\Delta H \le 10\text{ mCE}$) selon la célérité d'onde d'Allievi exacte.
- **Fonction 2 — Remplissage de la conduite** : Contrôle du débit d'air refoulé à vitesse contrôlée ($V = 0,5\text{ m/s}$, soit $5\,655\text{ m}^3/\text{h}$ pour DN 2000 mm). Vérification sous surpression de 1 mCE et proposition automatique d'un équipement suffisant (ex: 2 ventouses PAM DN 200 pour couvrir le débit).
- **Fonction 3 — Casse franche / Vidange d'urgence (Strickler-Bernoulli)** : Calcul de la dénivelée motrice active $H = \max(0\,;\, \text{Cote}_{ventouse} - \Delta P_{admiss} - \text{Cote}_{vidange})$ sous dépression maximale de 3 mCE. Débit d'air d'admission gravitationnel pour les branches amont et aval.
- **Algorithme d'optimisation d'équipements** : Proposition automatique de la combinaison optimale (ventouses triple fonction type PAM + clapets d'entrée d'air grand débit type SNH DN 100 à DN 250) garantissant 100% de conformité.
- **Trois bases catalogue permutables** : CEAI/SNH (référence), PAM/SNH (existant) et **MCP** (`Tableau_Recapitulatif_Debits_Ventouses_MCP.xlsx`, ventouses doubles orifices 3 fonctions). Les débits MCP sont exploités à 0,3 bar pour l'admission (≈ 3 mCE) et 0,1 bar pour l'évacuation (≈ 1 mCE) ; débits critiques, courbes, dimensions, poids et montages en chandelier sont également affichés dans l'onglet Catalogue.

### 2. 💧 Points Bas (Ouvrages de vidange)
- **Formule exacte corrigée, recalculée pour le temps cible saisi** ($t$ en heures, $K = 0{,}70$) :
  $$d\text{ (mm)} = \underbrace{\frac{1000}{\sqrt{t \cdot 3600 \cdot K \cdot \sqrt{2g}}}}_{\text{6,693 pour 2 h ; 9,465 pour 1 h}} \times D \times \sqrt{\frac{L_{am} + L_{av}}{\sqrt{h_{moy}}}}$$
  *(Correction du coefficient 13,39 de l'ancienne note qui correspondait à une vidange en 30 min. Aucun coefficient n'est figé à 2 h : le temps cible modifie bien le diamètre exigé.)*
- **Hauteur moyenne pondérée des deux branches** :
  $$h_{moy} = \frac{L_{am} \frac{H_{am}}{2} + L_{av} \frac{H_{av}}{2}}{L_{am} + L_{av}}$$
- **DN retenu imposé égal au DN recommandé (mode auto)** : dès que le temps cible change, le diamètre normalisé est recalculé et appliqué à tous les points bas. Un mode manuel reste disponible dans la boîte de dialogue d'un point bas (case « Imposer le DN recommandé ») et via « Tester DN 400 Uniformisé ». Anciens projets : un DN manuel existant est préservé.
- **Calcul du temps réel de vidange** $t_{reel} = t \times (d_{exact} / DN_{retenu})^2$ selon le DN réellement posé, avec détection des sous-dimensionnements.

### 3. ⚡ Laboratoire & Simulateurs Unitaires
- Calculateur de célérité d'Allievi en temps réel pour tous matériaux (PRV, PVC, Fonte ductile, Acier, PEHD, Béton).
- Simulateur thermodynamique de Saint-Venant (orifice, débit volumique/massique, transition subsonique/sonique).
- Simulateur de casse franche unitaire avec recommandation immédiate d'équipement.
- Simulateur de vidange unitaire avec table comparative de durées selon tous les diamètres standards.

### 4. 📈 Visualisations Graphiques Intégrées
- **Profil en long hydraulique interactif** : tracé altimétrique complet de l'adduction, positionnement des ventouses et vidanges géoréférencées avec codes couleur de conformité (vert / rouge).
- **Diagramme comparatif des débits d'air** : Débit requis vs Débit admis équipé.
- **Diagramme des temps réels de vidange** : Comparaison directe au temps cible contractuel saisi.
- **Courbe d'écoulement de Saint-Venant**.

### 5. 📥 Imports & 📤 Exports Professionnels
- **Import XLSX** : Lecture automatique de fichiers Excel avec détection intelligente des colonnes.
- **Export XLSX** : Classeur Excel de calculs complet à 5 feuilles stylisées (Synthèse, Données Projet, Ventouses, Vidanges, Catalogue MCP inclus).
- **Export DOCX** : Rapport officiel d'ingénierie et d'expertise complet (identité du projet, préambule, introduction, justifications théoriques, tableaux recalculés, figures graphiques insérées en haute résolution).
- **Export Graphiques HD** : Pack d'images PNG 300 DPI ou PDF prêt pour impression.
- **Gabarit Vierge** : Génération en un clic d'un template Excel type `Template_Import_Hydraulique.xlsx`.

### 6. 📋 Données du Projet & Rapports
- **Onglet « Données du Projet »** : Maître d'Ouvrage (MO), maîtrise d'œuvre, BET, lieu/commune/province/pays, marché, responsable, date, référence, ainsi que les textes libres d'**introduction** et de **préambule**.
- Ces informations sont reprises automatiquement dans le rapport Word (section 1) et dans la feuille « Données Projet » du classeur Excel exporté ; un texte standard est généré si les champs sont vides.

### 7. 💾 Projet, Menu & Aide
- **Sauvegarde/Ouverture de projet** natif `.mkst.json` : conserve paramètres, identité du projet, base catalogue air, points importés/saisis et choix retenus (DN/équipements), puis recalcule à l’ouverture.
- **Barre de menu** Fichier/Affichage/Aide avec raccourcis (`Ctrl+N/O/S/Shift+S/I/Q`) et indicateur de modifications non enregistrées (`*`).
- **Onglet À propos & Aide utilisateur** intégré (workflow, catalogues, bonnes pratiques anti-perte, dépannage).

---

## 📂 Structure du Projet

```
MK-St_Venant/
├── assets/                                    # Icône application (PNG/ICO) et ressources visuelles
│   ├── mk-st-venant-icon.ico
│   ├── mk-st-venant-icon.png
│   └── mk-st-venant-icon-512.png
├── core/                                      # Moteurs de calculs et gestion des données
│   ├── __init__.py
│   ├── hydraulic_models.py                    # Allievi, Saint-Venant, Strickler-Bernoulli, Vidange pondérée
│   ├── catalog.py                             # Spécifications PAM, SNH, PVC et diamètres normalisés
│   ├── catalog_mcp.py                         # Catalogue MCP (Excel) : courbes, DN, débits et recommandation
│   ├── catalogues_ceai_snh.py                 # Catalogue/référence CEAI/SNH et sélection d'équipements
│   ├── tables.py                              # Tables de compatibilité catalogue
│   ├── project_data.py                        # Modèles de données (dont ProjectIdentity), calculs, sauvegarde/ouverture projet (.mkst.json)
│   ├── sample_data.py                         # Jeu de données de référence issu de l'audit BR3_LOT 8
│   ├── excel_manager.py                       # Import et export XLSX stylisés (openpyxl)
│   ├── chart_generator.py                     # Profil en long et graphiques (matplotlib)
│   └── word_report_generator.py               # Rapport technique complet (.docx)
├── ui/                                        # Interface graphique CustomTkinter
│   ├── __init__.py
│   ├── app.py                                 # Fenêtre principale, menu, navigation et persistance projet
│   ├── dashboard_view.py                      # Tableau de bord KPIs et paramètres généraux
│   ├── air_valves_view.py                     # Tableau interactif des points hauts (ventouses)
│   ├── drains_view.py                         # Tableau interactif des points bas (vidanges)
│   ├── simulator_view.py                      # Simulateur interactif unitaire (laboratoire)
│   ├── profile_view.py                        # Canvas interactif du profil en long
│   ├── catalog_view.py                        # Catalogue des matériels standards (dont onglet MCP)
│   ├── project_info_view.py                   # Données du projet (MO, BET, lieu, intro, préambule)
│   ├── report_view.py                         # Gestionnaire d'import et d'export
│   └── about_view.py                          # À propos & aide utilisateur
├── main.py                                    # Script de démarrage principal (icône fenêtre)
├── run.bat                                    # Lanceur rapide Windows (source)
├── build_exe.bat                              # Script de build de l'exécutable Windows
├── Mk_Stvenant_Allievi_Strickler-Bernoulli.spec  # Spécification PyInstaller
├── requirements.txt                           # Dépendances Python
├── .gitignore                                 # Exclusions Git (env, build, dist, caches, etc.)
└── README.md                                  # Documentation
```

---

## 🛠️ Installation & Lancement

### Prérequis
- Python 3.10, 3.11, 3.12, 3.13 ou 3.14 (64-bit recommandé).

### Installation des dépendances
Ouvrez un terminal dans le répertoire du projet et exécutez :
```bash
pip install -r requirements.txt
```

### Lancement de l'application (depuis le code source)
- **Sous Windows (double-clic)** : Exécutez le fichier `run.bat`.
- **En ligne de commande** :
```bash
python main.py
```

### Build de l'exécutable Windows (.exe)
Un exécutable autonome (mode *one-folder*) est fourni via PyInstaller, avec l'icône `assets/mk-st-venant-icon.ico` :
- **Nom** : `Mk_Stvenant_Allievi_Strickler-Bernoulli.exe`
- **Build (recommandé, Windows)** : double-cliquez sur `build_exe.bat`, ou exécutez :
```bash
python -m PyInstaller --noconfirm --clean Mk_Stvenant_Allievi_Strickler-Bernoulli.spec
```
- **Résultat** : dossier `dist\Mk_Stvenant_Allievi_Strickler-Bernoulli\` contenant l'exécutable et ses dépendances.

> Les dossiers `build/` et `dist/` sont exclus par `.gitignore`. Pour partager l'application sur GitHub, publiez le code source et, si besoin, joignez le dossier `dist\...` compressé (ZIP) dans une Release GitHub.

---

## 📊 Cas de Référence Intégré : Adduction BR3_LOT 8

L'application charge par défaut les données auditées et recalculées du Lot 8 :
- **10 Points Hauts (Ventouses)** : PM 50 529,89 à PM 58 961,59.
- **9 Points Bas (Vidanges)** : PM 50 741,59 à PM 59 701,59.
- Conduite principale DN 2000 mm et DN 1600 mm en PRV ($E = 20\text{ GPa}$, $e = 35\text{ mm}$, $K_s = 104$).
- Célérité exacte d'Allievi calculée : $a = 548{,}4\text{ m/s}$.

Un bouton **« 🔄 Recharger Cas BR3_LOT 8 »** dans la barre latérale permet de réinitialiser instantanément le projet à ce cas étalon.

---

## 📜 Formules Mathématiques Exactes Utilisées

### 1. Vidanges (Points Bas)
$$h_{moy} = \frac{L_{am} \frac{H_{am}}{2} + L_{av} \frac{H_{av}}{2}}{L_{am} + L_{av}}$$
$$d\text{ (mm)} = \frac{1000}{\sqrt{t \cdot K \cdot \sqrt{2g}}} \cdot D \cdot \sqrt{\frac{L_{tot}}{\sqrt{h_{moy}}}} \approx 6{,}69 \cdot D \cdot \sqrt{\frac{L_{tot}}{\sqrt{h_{moy}}}}\quad (t = 2\text{ h},\; K = 0{,}7)$$
$$t_{reel}\text{ (h)} = 2{,}0 \times \left(\frac{d_{theorique}}{DN_{retenu}}\right)^2$$

### 2. Célérité d'Allievi (Conduite élastique)
$$a = \frac{1}{\sqrt{\rho \cdot \left(\frac{1}{K_{eau}} + \frac{D}{E \cdot e}\right)}}$$

### 3. Casse Franche (Strickler-Bernoulli)
$$H = \max(0\,;\, \text{Cote}_{ventouse} - 3{,}0\text{ m} - \text{Cote}_{vidange})$$
$$Q_{air} = \frac{\pi D^2}{4} \sqrt{\frac{H}{0{,}000587 \cdot \frac{L}{D^{4/3}} + 0{,}102}}$$

### 4. Loi d'Échappement d'Air de Saint-Venant
- Si $P_2 < 19{,}55\text{ mCE}$ (Subsonique) :
  $$Q_{air} = 499 \cdot C_d \cdot s \cdot \left(\frac{P_1}{P_2}\right)^{0{,}714} \sqrt{1 - \left(\frac{P_1}{P_2}\right)^{0{,}286}}$$
- Si $P_2 \ge 19{,}55\text{ mCE}$ (Sonique bloqué) :
  $$Q_{air} = 129 \cdot C_d \cdot s$$

---

## 📝 Licence & Auteur

**Licence MIT** — voir le fichier [`LICENSE`](LICENSE).

**Auteur** : Mostafa Karim Soussi — [@km1965](https://github.com/km1965)  
E-mail : mostafakarimsoussi1965@gmail.com  
Dépôt : https://github.com/km1965/MK-St_Venant

Développé dans le cadre des études d'ingénierie et d'adduction d'eau potable. Conforme aux prescriptions du CCTG et des règles de l'art hydraulique.
