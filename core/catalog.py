"""
Catalogue des équipements hydrauliques standards pour points hauts et points bas.
Inclut les ventouses triple fonction (type PAM), clapets d'entrée d'air (type SNH),
purgeurs soniques et séries de diamètres normalisés.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AirValveSpec:
    """Spécification d'une ventouse ou clapet d'admission."""
    model: str
    dn_mm: int
    valve_type: str  # "triple_function", "air_inlet_valve", "sonic_purger"
    admission_flow_3m_m3s: float  # Débit d'admission sous dépression 3 mCE (m3/s)
    exhaust_flow_1m_m3h: float    # Débit d'évacuation sous surpression 1 mCE (m3/h)
    description: str

    @property
    def admission_flow_3m_m3h(self) -> float:
        return self.admission_flow_3m_m3s * 3600.0

    @property
    def exhaust_flow_1m_m3s(self) -> float:
        return self.exhaust_flow_1m_m3h / 3600.0


# Ventouses triple fonction (type Pont-à-Mousson PAM ou équivalent)
PAM_TRIPLE_FUNCTION_VALVES: Dict[int, AirValveSpec] = {
    100: AirValveSpec(
        model="PAM DN100",
        dn_mm=100,
        valve_type="triple_function",
        admission_flow_3m_m3s=0.925,  # 3330 m3/h
        exhaust_flow_1m_m3h=1298.0,
        description="Ventouse 3 fonctions PAM DN100 (admission 0.925 m3/s, évacuation 1298 m3/h)"
    ),
    150: AirValveSpec(
        model="PAM DN150",
        dn_mm=150,
        valve_type="triple_function",
        admission_flow_3m_m3s=2.270,  # 8173 m3/h
        exhaust_flow_1m_m3h=3338.0,
        description="Ventouse 3 fonctions PAM DN150 (admission 2.270 m3/s, évacuation 3338 m3/h)"
    ),
    200: AirValveSpec(
        model="PAM DN200",
        dn_mm=200,
        valve_type="triple_function",
        admission_flow_3m_m3s=4.165,  # 14994 m3/h (ou 14454 selon notice)
        exhaust_flow_1m_m3h=5300.0,
        description="Ventouse 3 fonctions PAM DN200 (admission 4.165 m3/s, évacuation 5300 m3/h)"
    ),
}

# Clapets d'entrée d'air grand débit (type SNH ou équivalent)
SNH_AIR_INLET_VALVES: Dict[int, AirValveSpec] = {
    100: AirValveSpec(
        model="Clapet SNH DN100",
        dn_mm=100,
        valve_type="air_inlet_valve",
        admission_flow_3m_m3s=2.600,  # 9360 m3/h
        exhaust_flow_1m_m3h=0.0,
        description="Clapet d'entrée d'air grand débit DN100 (admission 2.60 m3/s)"
    ),
    150: AirValveSpec(
        model="Clapet SNH DN150",
        dn_mm=150,
        valve_type="air_inlet_valve",
        admission_flow_3m_m3s=4.550,  # 16380 m3/h
        exhaust_flow_1m_m3h=0.0,
        description="Clapet d'entrée d'air grand débit DN150 (admission 4.55 m3/s)"
    ),
    200: AirValveSpec(
        model="Clapet SNH DN200",
        dn_mm=200,
        valve_type="air_inlet_valve",
        admission_flow_3m_m3s=7.800,  # 28080 m3/h
        exhaust_flow_1m_m3h=0.0,
        description="Clapet d'entrée d'air grand débit DN200 (admission 7.80 m3/s)"
    ),
    250: AirValveSpec(
        model="Clapet SNH DN250",
        dn_mm=250,
        valve_type="air_inlet_valve",
        admission_flow_3m_m3s=13.000,  # 46800 m3/h
        exhaust_flow_1m_m3h=0.0,
        description="Clapet d'entrée d'air grand débit DN250 (admission 13.00 m3/s)"
    ),
}

# Purgeur sonique (ex: PSA250 - dégazage sous pression)
SONIC_PURGERS: Dict[str, AirValveSpec] = {
    "PSA250": AirValveSpec(
        model="Purgeur sonique PSA250",
        dn_mm=25,
        valve_type="sonic_purger",
        admission_flow_3m_m3s=0.0,
        exhaust_flow_1m_m3h=250.0,
        description="Purgeur sonique PSA250 pour dégazage sous pression de service"
    )
}

# Diamètres standards normalisés de vidange (en mm)
STANDARD_DRAIN_DIAMETERS_MM: List[int] = [
    80, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000
]

# Matériaux usuels et modules d'élasticité (Pa)
PIPE_MATERIALS: Dict[str, Dict[str, float]] = {
    "PRV (Polyester Renforcé Verre)": {
        "E_Pa": 20.0e9,
        "Ks": 104.0,
        "default_thickness_ratio": 0.0175,  # e = 35mm pour DN2000
        "default_roughness_m": 0.00003
    },
    "Fonte ductile": {
        "E_Pa": 170.0e9,
        "Ks": 100.0,
        "default_thickness_ratio": 0.010,
        "default_roughness_m": 0.0001
    },
    "Acier": {
        "E_Pa": 210.0e9,
        "Ks": 95.0,
        "default_thickness_ratio": 0.008,
        "default_roughness_m": 0.00005
    },
    "PEHD (Polyéthylène Haute Densité)": {
        "E_Pa": 1.0e9,
        "Ks": 110.0,
        "default_thickness_ratio": 0.05,
        "default_roughness_m": 0.00002
    },
    "Béton armé": {
        "E_Pa": 30.0e9,
        "Ks": 80.0,
        "default_thickness_ratio": 0.08,
        "default_roughness_m": 0.0005
    }
}


def get_standard_dn_drain(d_calc_mm: float) -> int:
    """Retourne le DN normalisé immédiatement supérieur ou égal au diamètre calculé."""
    for dn in STANDARD_DRAIN_DIAMETERS_MM:
        if dn >= d_calc_mm:
            return dn
    return STANDARD_DRAIN_DIAMETERS_MM[-1]


def recommend_air_valve_equipment(
    q_air_req_m3s: float,
    dn_conduite_m: float,
    v_filling_ms: float = 0.5
) -> Dict[str, any]:
    """
    Détermine la combinaison d'équipements recommandée pour un point haut :
    - Au moins 1 ventouse triple fonction DN200 (ou 2 pour DN conduite >= 2.0 m
      pour assurer l'évacuation de l'air au remplissage)
    - Complément par clapets d'entrée d'air DN250, DN200 ou DN150 pour couvrir
      100% du débit de casse franche Qair_req_m3s.
    """
    # Débit d'air au remplissage à évacuer (m3/h)
    section_conduite = 3.1415926535 * (dn_conduite_m ** 2) / 4.0
    q_rempl_m3h = v_filling_ms * section_conduite * 3600.0

    # Débit évacuable par une ventouse PAM DN200 sous 1 mCE = 5300 m3/h
    # Si q_rempl_m3h > 5300 m3/h (cas DN >= 2000 mm à 0.5 m/s -> 5655 m3/h), il faut 2 ventouses DN200
    if dn_conduite_m >= 2.0 or q_rempl_m3h > 5300.0:
        nb_ventouses_dn200 = 2
    else:
        nb_ventouses_dn200 = 1

    q_admis_ventouses = nb_ventouses_dn200 * PAM_TRIPLE_FUNCTION_VALVES[200].admission_flow_3m_m3s
    q_evac_ventouses = nb_ventouses_dn200 * PAM_TRIPLE_FUNCTION_VALVES[200].exhaust_flow_1m_m3h

    # Débit d'admission restant à couvrir pour casse franche
    q_restant = max(0.0, q_air_req_m3s - q_admis_ventouses)

    nb_clapets_dn250 = 0
    nb_clapets_dn200 = 0
    nb_clapets_dn150 = 0

    if q_restant > 0:
        # Priorité aux clapets DN250 (13 m3/s chacun)
        nb_clapets_dn250 = int(q_restant // 13.0)
        q_restant_apres_250 = q_restant - (nb_clapets_dn250 * 13.0)

        if q_restant_apres_250 > 7.8:
            nb_clapets_dn250 += 1
        elif q_restant_apres_250 > 4.55:
            nb_clapets_dn200 += 1
        elif q_restant_apres_250 > 0.001:
            nb_clapets_dn150 += 1

    total_admission = (
        nb_ventouses_dn200 * 4.165 +
        nb_clapets_dn250 * 13.0 +
        nb_clapets_dn200 * 7.8 +
        nb_clapets_dn150 * 4.55
    )

    parts = []
    if nb_ventouses_dn200 > 0:
        parts.append(f"{nb_ventouses_dn200} Ventouse{'s' if nb_ventouses_dn200>1 else ''} DN200")
    if nb_clapets_dn250 > 0:
        parts.append(f"{nb_clapets_dn250} Clapet{'s' if nb_clapets_dn250>1 else ''} DN250")
    if nb_clapets_dn200 > 0:
        parts.append(f"{nb_clapets_dn200} Clapet{'s' if nb_clapets_dn200>1 else ''} DN200")
    if nb_clapets_dn150 > 0:
        parts.append(f"{nb_clapets_dn150} Clapet{'s' if nb_clapets_dn150>1 else ''} DN150")

    equip_str = " + ".join(parts) if parts else "1 Ventouse DN200"

    is_compliant_filling = q_evac_ventouses >= q_rempl_m3h
    is_compliant_intake = total_admission >= q_air_req_m3s

    return {
        "equipment_str": equip_str,
        "nb_ventouses_dn200": nb_ventouses_dn200,
        "nb_clapets_dn250": nb_clapets_dn250,
        "nb_clapets_dn200": nb_clapets_dn200,
        "nb_clapets_dn150": nb_clapets_dn150,
        "total_admission_flow_m3s": round(total_admission, 2),
        "total_exhaust_flow_m3h": round(q_evac_ventouses, 1),
        "filling_flow_m3h": round(q_rempl_m3h, 1),
        "is_compliant_intake": is_compliant_intake,
        "is_compliant_filling": is_compliant_filling,
        "coverage_pct": round((total_admission / q_air_req_m3s * 100.0) if q_air_req_m3s > 0 else 100.0, 1)
    }
