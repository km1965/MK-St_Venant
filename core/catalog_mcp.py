"""Catalogue MCP — ventouses automatiques doubles orifices 3 fonctions.

Données extraites de ``Tableau_Recapitulatif_Debits_Ventouses_MCP.xlsx``
(feuilles « Synthèse Débits par DN », « Courbes Grand Orifice » et
« Petit Orifice & Dimensions ») placé à la racine du projet.

Conventions retenues pour le dimensionnement (afin de comparer les bases
catalogue sur des hypothèses homogènes) :
- admission : débit « optimal » du catalogue à ΔP = 0,3 bar ≈ 3 mCE
  (référence NF EN 805 utilisée par les autres bases) ;
- évacuation au remplissage : débit de la courbe grand orifice à
  ΔP = 0,1 bar ≈ 1 mCE ;
- les débits « critiques » (admission -0,5 bar / évacuation +0,9 bar) sont
  conservés en information et dans l'onglet d'affichage du catalogue.

Les montages en chandelier (conduites DN > 900 mm) et la réduction par
vanne papillon (-20 %) sont également tracés, conformément aux notes du
classeur d'origine.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

SOURCE_XLSX = "Tableau_Recapitulatif_Debits_Ventouses_MCP.xlsx"
PRESSION_ADMISSION_REFERENCE = "0,3 bar (≈ 3 mCE)"
PRESSION_EVACUATION_REFERENCE = "0,1 bar (≈ 1 mCE)"


@dataclass(frozen=True)
class VentouseMCP:
    """Une ventouse MCP du tableau récapitulatif (lignes de synthèse)."""

    dn_label: str
    dn_mm: int
    serie_conduite: str      # plage DN conduite indiquée par le catalogue
    dimensions_mm: str       # L × H × M
    poids_kg: float
    admission_opt_m3h: float     # ΔP = -0,3 bar (~3 mCE)
    admission_crit_m3h: float    # ΔP = -0,5 bar
    evacuation_opt_m3h: float    # ΔP = +0,3 bar
    evacuation_crit_m3h: float   # ΔP = +0,9 bar
    courbe: str
    notes: str

    @property
    def admission_3mce_m3s(self) -> float:
        return self.admission_opt_m3h / 3600.0

    @property
    def admission_crit_m3s(self) -> float:
        return self.admission_crit_m3h / 3600.0

    @property
    def evacuation_1mce_m3h(self) -> float:
        """Capacité d'évacuation à 0,1 bar lue sur la courbe grand orifice."""
        return COURBES_EVACUATION_M3MIN.get(self.courbe_key, {}).get(0.1, 0.0) * 60.0

    @property
    def courbe_key(self) -> str:
        """Normalise le libellé de courbe (les DN 200/300 portent un astérisque)."""
        label = self.courbe.replace("*", "").strip().lower()
        if "100" in label and "150" in label:
            return "100/150 mm"
        if "80" in label:
            return "80 mm"
        return "50 mm"


# Courbes caractéristiques du classeur MCP (Std m³/min).
COURBES_ADMISSION_M3MIN: dict[str, dict[float, float]] = {
    "50 mm": {-0.1: 11.0, -0.2: 17.0, -0.3: 21.0, -0.4: 23.0, -0.5: 24.5},
    "80 mm": {-0.1: 20.0, -0.2: 31.0, -0.3: 40.0, -0.4: 45.0, -0.5: 49.0},
    "100/150 mm": {-0.1: 39.0, -0.2: 59.0, -0.3: 74.0, -0.4: 83.0, -0.5: 91.0},
}

COURBES_EVACUATION_M3MIN: dict[str, dict[float, float]] = {
    "50 mm": {0.1: 14.0, 0.2: 21.0, 0.3: 26.0, 0.4: 31.0, 0.5: 35.0, 0.6: 39.0, 0.7: 43.0, 0.8: 47.0, 0.9: 51.0},
    "80 mm": {0.1: 25.0, 0.2: 38.0, 0.3: 48.0, 0.4: 57.0, 0.5: 65.0, 0.6: 73.0, 0.7: 81.0, 0.8: 89.0, 0.9: 96.0},
    "100/150 mm": {0.1: 48.0, 0.2: 71.0, 0.3: 91.0, 0.4: 108.0, 0.5: 122.0, 0.6: 136.0, 0.7: 150.0, 0.8: 164.0, 0.9: 177.0},
    "100/150 mm - papillon -20%": {0.1: 38.4, 0.2: 56.8, 0.3: 72.8, 0.4: 86.4, 0.5: 97.6, 0.6: 108.8, 0.7: 120.0, 0.8: 131.2, 0.9: 141.6},
    "Chandelier DN 1200 (2 × DN100)": {0.1: 96.0, 0.3: 182.0, 0.9: 354.0},
    "Chandelier DN 1600 (3 × DN100)": {0.1: 144.0, 0.3: 273.0, 0.9: 531.0},
}

# Lignes de la feuille « Synthèse Débits par DN » (colonnes 1 à 14).
VENTOUSES_MCP: tuple[VentouseMCP, ...] = (
    VentouseMCP("DN 40", 40, "60 - 250", "228 × 280 × 166", 17.0, 1260.0, 1470.0, 1560.0, 3060.0, "Courbe 50 mm", "Corps série 400 avec bride réduite DN 40/65"),
    VentouseMCP("DN 50", 50, "60 - 250", "228 × 280 × 166", 17.0, 1260.0, 1470.0, 1560.0, 3060.0, "Courbe 50 mm", "Dimension standard de référence courbe 50 mm"),
    VentouseMCP("DN 60/65", 65, "60 - 250", "228 × 280 × 166", 20.5, 1260.0, 1470.0, 1560.0, 3060.0, "Courbe 50 mm", "Corps commun série 400 (H = 280 mm)"),
    VentouseMCP("DN 80", 80, "250 - 400", "228 × 280 × 166", 21.0, 2400.0, 2940.0, 2880.0, 5760.0, "Courbe 80 mm", "Existe aussi en série 600 (H = 350 mm, 33 kg)"),
    VentouseMCP("DN 100 (série 400)", 100, "250 - 400", "228 × 280 × 166", 31.0, 2400.0, 2940.0, 2880.0, 5760.0, "Courbe 80 mm", "Version série 400 (H = 280 mm)"),
    VentouseMCP("DN 100 (série 600/900)", 100, "400 - 900", "253 × 420 × 265", 40.0, 4440.0, 5460.0, 5460.0, 10620.0, "Courbe 100/150 mm", "Corps grand débit ; montage chandelier pour DN conduite > 900"),
    VentouseMCP("DN 125", 125, "400 - 600", "253 × 420 × 265", 32.0, 4440.0, 5460.0, 5460.0, 10620.0, "Courbe 100/150 mm", "Corps grand débit (H = 420 mm, M = 265 mm)"),
    VentouseMCP("DN 150", 150, "400 - 600", "253 × 420 × 265", 35.0, 4440.0, 5460.0, 5460.0, 10620.0, "Courbe 100/150 mm", "Dimension standard de référence courbe 100/150 mm"),
    VentouseMCP("DN 200", 200, "600 - 900", "253 × 420 × 265", 50.0, 4440.0, 5460.0, 5460.0, 10620.0, "Courbe 100/150 mm", "Même corps que DN 150, bride DN 200"),
    VentouseMCP("DN 250", 250, "600 - 900", "253 × 420 × 265", 60.0, 4440.0, 5460.0, 5460.0, 10620.0, "Courbe 100/150 mm", "Même corps que DN 150, bride DN 250"),
    VentouseMCP("DN 300", 300, "600 - 900", "253 × 420 × 265", 75.0, 4440.0, 5460.0, 5460.0, 10620.0, "Courbe 100/150 mm", "Même corps que DN 150, bride DN 300"),
)

# Notes d'ingénierie du classeur MCP (reprises telles quelles).
NOTES_MCP: tuple[str, ...] = (
    "Réduction vanne papillon : un isolement papillon en amont réduit le débit d'air d'environ 20 % "
    "(DN 100/150 : ~91 → ~73 Std m³/min à 0,3 bar).",
    "Montages en chandelier (DN conduite > 900 mm) : DN 1200 → 1 sortie DN 150 + 2 ventouses DN 100 (série 900) ; "
    "DN 1600 → 1 sortie DN 150 + 3 ventouses DN 100 (série 900).",
    "Équivalence corps/orifice : DN 200, DN 250 et DN 300 partagent la géométrie du DN 150 "
    "(L = 253, H = 420, M = 265 mm) ; seule la bride diffère.",
)

CHANDELIERS_MCP: dict[int, str] = {
    1200: "1 sortie DN 150 + 2 ventouses DN 100 (série 900)",
    1600: "1 sortie DN 150 + 3 ventouses DN 100 (série 900)",
}

# Nombre de ventouses DN100 (série 900) par chandelier, selon les notes du catalogue.
CHANDELIER_UNITS: dict[int, int] = {1200: 2, 1600: 3}


def _parse_serie(serie: str) -> tuple[float, float]:
    """Convertit « 400 - 900 » en bornes numériques (mm)."""
    parties = [float(p.strip()) for p in serie.replace("–", "-").split("-") if p.strip()]
    if len(parties) >= 2:
        return parties[0], parties[1]
    return 0.0, 10000.0


def ventouses_pour_conduite(dn_conduite_m: float) -> tuple[VentouseMCP, ...]:
    """Filtre les ventouses MCP compatibles avec le DN de conduite."""
    if dn_conduite_m <= 0:
        return VENTOUSES_MCP

    dn_mm = dn_conduite_m * 1000.0
    compatibles = tuple(
        v for v in VENTOUSES_MCP
        if _parse_serie(v.serie_conduite)[0] <= dn_mm <= _parse_serie(v.serie_conduite)[1]
    )
    if compatibles:
        return compatibles

    # Au-delà de DN 900, le catalogue prescrit un montage en chandelier à
    # partir des ventouses série 900 (DN 100 à DN 300).
    if dn_mm > 900:
        return tuple(v for v in VENTOUSES_MCP if v.serie_conduite == "400 - 900")
    return VENTOUSES_MCP


def recommander_equipement_mcp(
    debit_m3s: float,
    dn_conduite_m: float = 0.0,
    v_filling_ms: float = 0.5,
) -> dict:
    """Recommande un nombre de ventouses MCP couvrant admission et remplissage.

    Le dimensionnement retient la capacité d'admission à 0,3 bar (≈ 3 mCE)
    et la capacité d'évacuation à 0,1 bar (≈ 1 mCE). Le nombre d'unités est
    le plus petit nombre couvrant simultanément les deux besoins.
    """
    debit_m3s = max(0.0, float(debit_m3s or 0.0))
    q_rempl_m3h = (
        v_filling_ms * (math.pi * (dn_conduite_m ** 2) / 4.0) * 3600.0
        if dn_conduite_m > 0 else 0.0
    )

    dn_conduite_mm = int(round(dn_conduite_m * 1000.0)) if dn_conduite_m > 0 else 0
    chandelier = CHANDELIERS_MCP.get(dn_conduite_mm, "")
    is_chandelier = dn_conduite_mm > 900
    units_per_chandelier = CHANDELIER_UNITS.get(dn_conduite_mm, 3)
    ventouse_chandelier = next(
        (v for v in VENTOUSES_MCP if v.dn_label == "DN 100 (série 600/900)"),
        VENTOUSES_MCP[-1],
    )

    # Au-delà de DN 900, le catalogue impose un chandelier : on dimensionne
    # par nombre de chandeliers, chacun portant plusieurs ventouses DN100.
    candidats = (ventouse_chandelier,) if is_chandelier else ventouses_pour_conduite(dn_conduite_m)
    meilleur = None
    for ventouse in candidats:
        cap_admission = ventouse.admission_3mce_m3s
        cap_evacuation = ventouse.evacuation_1mce_m3h
        if cap_admission <= 0:
            continue
        facteur = units_per_chandelier if is_chandelier else 1
        cap_admission *= facteur
        cap_evacuation *= facteur

        n_admission = math.ceil(debit_m3s / cap_admission) if debit_m3s > 0 else 0
        n_remplissage = math.ceil(q_rempl_m3h / cap_evacuation) if q_rempl_m3h > 0 and cap_evacuation > 0 else 0
        groupes = max(n_admission, n_remplissage, 1 if (debit_m3s > 0 or q_rempl_m3h > 0) else 0)
        if groupes == 0:
            continue

        total_admission = groupes * cap_admission
        total_evacuation = groupes * cap_evacuation
        if total_admission + 1e-9 < debit_m3s or total_evacuation + 1e-9 < q_rempl_m3h:
            continue

        surdim = (total_admission - debit_m3s) + (total_evacuation - q_rempl_m3h) / 3600.0
        # Priorité au plus petit nombre d'organes/chandeliers, puis au
        # surdimensionnement le plus faible ; les petits DN sont favorisés à
        # capacité égale (moindre coût).
        score = (groupes, surdim, ventouse.dn_mm, groupes * facteur)
        if meilleur is None or score < meilleur[0]:
            meilleur = (score, ventouse, groupes, total_admission, total_evacuation)

    if meilleur is None:
        derniere = candidats[-1] if candidats else VENTOUSES_MCP[-1]
        facteur = units_per_chandelier if is_chandelier else 1
        groupes = max(
            math.ceil(debit_m3s / (derniere.admission_3mce_m3s * facteur)) if derniere.admission_3mce_m3s > 0 else 1,
            math.ceil(q_rempl_m3h / (derniere.evacuation_1mce_m3h * facteur)) if derniere.evacuation_1mce_m3h > 0 else 1,
            1,
        )
        meilleur = (
            (groupes, 0.0, derniere.dn_mm, groupes * facteur), derniere, groupes,
            groupes * derniere.admission_3mce_m3s * facteur,
            groupes * derniere.evacuation_1mce_m3h * facteur,
        )

    _, ventouse, groupes, total_admission, total_evacuation = meilleur
    plural = "s" if groupes > 1 else ""

    if is_chandelier:
        nb_ventouses = groupes * units_per_chandelier
        configuration = chandelier or (
            f"1 sortie DN 150 + {units_per_chandelier} ventouses DN 100 (série 900) — à confirmer selon le DN conduite"
        )
        equipment = (
            f"{groupes} Chandelier{plural} MCP — {configuration} "
            f"({nb_ventouses} ventouses DN 100 au total)"
        )
        ventouse_dn = f"Chandelier DN100 ×{units_per_chandelier}"
        ventouse_nombre = nb_ventouses
        chandelier_info = configuration
    else:
        equipment = f"{groupes} Ventouse{plural} MCP {ventouse.dn_label} ({ventouse.courbe})"
        ventouse_dn = ventouse.dn_label
        ventouse_nombre = groupes
        chandelier_info = ""

    couvert = debit_m3s <= 0 or total_admission + 1e-9 >= debit_m3s
    remplissage_ok = q_rempl_m3h <= 0 or total_evacuation + 1e-9 >= q_rempl_m3h

    result = {
        "equipment_str": equipment,
        "total_admission_flow_m3s": round(total_admission, 4),
        "q_admis_m3s": round(total_admission, 4),
        "is_compliant_intake": bool(couvert),
        "is_compliant_filling": bool(remplissage_ok),
        "total_exhaust_flow_m3h": round(total_evacuation, 1),
        "filling_flow_m3h": round(q_rempl_m3h, 1),
        "coverage_pct": round((total_admission / debit_m3s * 100.0) if debit_m3s > 0 else 100.0, 1),
        "ventouse": {
            "famille": "Ventouse MCP double orifice 3 fonctions",
            "dn": ventouse_dn,
            "nombre": ventouse_nombre,
            "capacite_unitaire_m3s": round(ventouse.admission_3mce_m3s, 4),
            "capacite_totale_m3s": round(total_admission, 4),
            "couvert": bool(couvert),
        },
        "catalog_config": "MCP",
        "config_label": "MCP (catalogue Excel)",
        "reference": SOURCE_XLSX,
        "admission_reference": PRESSION_ADMISSION_REFERENCE,
        "evacuation_reference": PRESSION_EVACUATION_REFERENCE,
        "admission_crit_m3s": round(ventouse.admission_crit_m3s, 4),
        "chandelier": chandelier_info,
    }
    if is_chandelier:
        result["nb_chandeliers"] = groupes
    return result
