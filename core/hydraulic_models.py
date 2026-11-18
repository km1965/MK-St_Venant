"""
Moteur de calculs et de vérifications hydrauliques pour adductions d'eau.
Implémente les formules exactes corrigées selon l'Audit technique :
- Allievi (Célérité exacte des ondes élastiques)
- Saint-Venant (Écoulement d'air compressible subsonique et sonique)
- Remplissage & Dégazage en service
- Strickler-Bernoulli (Admission d'air en cas de casse franche sous dépression admissible)
- Vidange des points bas (Hauteur moyenne pondérée, diamètre exact, temps de vidange réel)
"""

import math
from typing import Dict, Tuple, Optional


# ==============================================================================
# CONSTANTES PHYSIQUES FONDAMENTALES
# ==============================================================================
G = 9.81              # Accélération de la pesanteur (m/s2)
RHO_WATER = 1000.0    # Masse volumique de l'eau douce (kg/m3)
K_WATER_BULK = 2.07e9 # Module de compressibilité de l'eau (Pa = N/m2)
P_ATM_MCE = 10.33     # Pression atmosphérique standard (mCE)
GAMMA_AIR = 1.4       # Indice adiabatique de l'air
R_AIR = 287.05        # Constante spécifique de l'air (J/(kg·K))
T_AIR_K = 293.15      # Température ambiante standard (20 °C = 293.15 K)
RHO_AIR_STD = 1.225   # Masse volumique de l'air ambiant standard (kg/m3)


# ==============================================================================
# 1. CÉLÉRITÉ DE L'ONDE DE CHOC D'ALLIEVI
# ==============================================================================
def calculate_allievi_wave_speed(
    d_inner_m: float,
    thickness_m: float,
    e_young_pa: float,
    rho_kg_m3: float = RHO_WATER,
    k_water_pa: float = K_WATER_BULK
) -> float:
    """
    Calcule la célérité exacte 'a' de l'onde de choc dans la conduite (m/s).
    Formule d'Allievi pour conduite cylindrique à paroi mince/épaisse :
        a = 1 / sqrt( rho * ( 1 / K_eau + d / (E * e) ) )

    Exemple PRV DN2000 (d=2.0m, e=0.035m, E=20 GPa) -> ~548 m/s.
    """
    if d_inner_m <= 0 or thickness_m <= 0 or e_young_pa <= 0:
        raise ValueError("Les dimensions et modules doivent être strictement positifs.")

    denom_term1 = 1.0 / k_water_pa
    denom_term2 = d_inner_m / (e_young_pa * thickness_m)
    denom = rho_kg_m3 * (denom_term1 + denom_term2)

    return 1.0 / math.sqrt(denom)


# ==============================================================================
# 2. LOI D'ÉCHAPPEMENT DE SAINT-VENANT (DÉGAZAGE & PETITS ORIFICES)
# ==============================================================================
def calculate_saint_venant_air_exhaust(
    orifice_area_m2: float,
    p2_mce_abs: float,
    p1_mce_abs: float = P_ATM_MCE,
    discharge_coeff_cd: float = 0.65
) -> Dict[str, float]:
    """
    Calcule le débit massique et volumique d'échappement d'air à travers un orifice
    selon la loi thermodynamique de Saint-Venant pour un gaz parfait.

    P1: Pression aval (atmosphérique, 10.33 mCE)
    P2: Pression amont dans la poche d'air (mCE absolu = P_rel + 10.33)

    Ratio critique pour l'air (gamma = 1.4) :
        r_c = (2 / (gamma + 1)) ^ (gamma / (gamma - 1)) = (2/2.4)^3.5 = 0.52828
        P_critique = P1 / 0.52828 = 19.55 mCE absolu (~0.92 bar relatif)

    Régime subsonique (P2 < 19.55 mCE) :
        Qair = 499 * s * (P1/P2)^0.714 * sqrt(1 - (P1/P2)^0.286)  [m3/s en cond. détendues]

    Régime sonique (P2 >= 19.55 mCE, vitesse sonique au col) :
        Qair = 129 * s  [m3/s]
    """
    if p2_mce_abs <= p1_mce_abs:
        # Aucune différence motrice ou dépression
        return {
            "regime": "aucun_ecoulement",
            "pressure_ratio": 1.0,
            "q_air_m3s": 0.0,
            "q_air_m3h": 0.0
        }

    ratio = p1_mce_abs / p2_mce_abs
    r_crit = (2.0 / (GAMMA_AIR + 1.0)) ** (GAMMA_AIR / (GAMMA_AIR - 1.0)) # ~0.5283
    p_crit_abs = p1_mce_abs / r_crit # ~19.55 mCE

    if p2_mce_abs < p_crit_abs:
        # Régime subsonique
        q_m3s = (
            499.0 * discharge_coeff_cd * orifice_area_m2 *
            (ratio ** 0.714) * math.sqrt(max(0.0, 1.0 - (ratio ** 0.286)))
        )
        regime = "subsonique"
    else:
        # Régime sonique bloqué (choked flow)
        q_m3s = 129.0 * discharge_coeff_cd * orifice_area_m2
        regime = "sonique"

    return {
        "regime": regime,
        "pressure_ratio": round(ratio, 4),
        "p_critique_mce": round(p_crit_abs, 2),
        "q_air_m3s": round(q_m3s, 5),
        "q_air_m3h": round(q_m3s * 3600.0, 2)
    }


def calculate_degassing_orifice_check(
    q_water_nominal_m3s: float,
    d_inner_m: float,
    wave_speed_a_ms: float,
    delta_h_max_mce: float = 10.0
) -> Dict[str, float]:
    """
    Vérification de la fonction 1 (dégazage en service).
    Le volume d'air dégagé est estimé à 2% du débit nominal d'eau.
    L'orifice est calibré pour limiter la surpression de coup de bélier
    lors du claquage de la bille à delta_h_max_mce (usuellement 10 mCE).
    """
    q_air_degas_m3h = 0.02 * q_water_nominal_m3s * 3600.0
    q_air_degas_m3s = q_air_degas_m3h / 3600.0

    # Section de la conduite
    s_pipe = math.pi * (d_inner_m ** 2) / 4.0

    # Relation simplifiée d'Allievi pour dégazage :
    # ratio d1 / d <= sqrt( delta_H / (19.9 * a) )  ou analyse de fermeture
    ratio_max = math.sqrt(delta_h_max_mce / (19.9 * wave_speed_a_ms)) if wave_speed_a_ms > 0 else 0.0
    d1_max_mm = ratio_max * (d_inner_m * 1000.0)

    return {
        "q_water_nominal_m3s": q_water_nominal_m3s,
        "q_air_degas_m3h": round(q_air_degas_m3h, 2),
        "q_air_degas_m3s": round(q_air_degas_m3s, 5),
        "wave_speed_a_ms": round(wave_speed_a_ms, 1),
        "delta_h_max_mce": delta_h_max_mce,
        "ratio_d1_d": round(ratio_max, 5),
        "d1_max_orifice_mm": round(d1_max_mm, 2)
    }


# ==============================================================================
# 3. ÉVACUATION D'AIR AU REMPLISSAGE (FONCTION 2)
# ==============================================================================
def calculate_filling_air_flow(
    d_inner_m: float,
    v_filling_ms: float = 0.5
) -> Dict[str, float]:
    """
    Calcule le débit d'air refoulé lors du remplissage à vitesse contrôlée.
    Pour éviter les coups de bélier et l'émulsion, V_remplissage est préconisée à 0.5 m/s.
    À pression atmosphérique, le débit volumique d'air refoulé est égal au débit d'eau refoulé :
        Qair = V * S_pipe
    """
    s_pipe = math.pi * (d_inner_m ** 2) / 4.0
    q_air_m3s = v_filling_ms * s_pipe
    q_air_m3h = q_air_m3s * 3600.0

    return {
        "v_filling_ms": v_filling_ms,
        "s_pipe_m2": round(s_pipe, 4),
        "q_air_remplissage_m3s": round(q_air_m3s, 4),
        "q_air_remplissage_m3h": round(q_air_m3h, 1)
    }


# ==============================================================================
# 4. ENTRÉE D'AIR LORS D'UNE CASSE FRANCHE (STRICKLER-BERNOULLI - FONCTION 3)
# ==============================================================================
def calculate_strickler_rupture_flow(
    d_inner_m: float,
    length_m: float,
    z_air_valve_m: float,
    z_drain_m: float,
    delta_p_admiss_mce: float = 3.0,
    ks_strickler: float = 104.0,
    singular_loss_coeff_k: float = 2.0
) -> Dict[str, float]:
    """
    Calcule le débit gravitationnel maximal d'eau (et donc le débit d'air d'admission
    requis pour empêcher une dépression supérieure à delta_p_admiss_mce).

    Formule exacte établie selon le principe de Bernoulli entre le point haut et le point bas :
        H = max(0, z_ventouse - delta_p_admiss - z_vidange)

    Si z_ventouse - z_vidange < delta_p_admiss (ex: < 3.0 mCE) :
        La colonne géométrique est insuffisante pour générer par gravité seule
        la dépression maximale autorisée de 3 mCE -> H = 0, écoulement non critique.

    Ligne d'énergie et pertes de charge :
        Delta_H = j * L + k * v^2 / (2g)
        avec j = (4^(4/3) * v^2) / (Ks^2 * D^(4/3)) (formule de Manning-Strickler)
        v = sqrt( H / [ (4^(4/3) * L) / (Ks^2 * D^(4/3) * 2g) + k / (2g) ] )
        Q = v * (pi * D^2 / 4)

    Pour Ks = 104 (PRV) et k = 2 :
        terme_lineaire = 4^(4/3) / (104^2 * 2 * 9.81) = 0.0005872
        terme_singulier = 2 / (2 * 9.81) = 0.1019
        Qair = (pi * D^2 / 4) * sqrt( H / ( 0.000587 * L / D^(4/3) + 0.102 ) )
    """
    diff_geom = z_air_valve_m - z_drain_m
    h_moteur = max(0.0, diff_geom - delta_p_admiss_mce)

    if h_moteur <= 0.0 or length_m <= 0.0 or d_inner_m <= 0.0:
        return {
            "h_moteur_m": 0.0,
            "diff_geom_m": round(diff_geom, 2),
            "v_water_ms": 0.0,
            "q_air_m3s": 0.0,
            "q_air_m3h": 0.0,
            "is_gravity_sufficient": False,
            "comment": "Dénivelée géométrique <= 3.0 m : colonne insuffisante pour créer 3 mCE de dépression."
        }

    # Coefficients exacts de la formule de Manning-Strickler / Bernoulli
    # Pour Ks = 104 (PRV) : coeff_lin = 0.0005872
    # Pour k = 2.0 : coeff_sing = 2.0 / (2 * 9.81) = 0.1019 ~ 0.102
    coeff_lin_base = 0.0005872 * ((104.0 / ks_strickler) ** 2)
    coeff_sing = singular_loss_coeff_k / (2.0 * G)

    denom = (coeff_lin_base * length_m / (d_inner_m ** (4.0 / 3.0))) + coeff_sing
    v = math.sqrt(h_moteur / denom)
    s_pipe = math.pi * (d_inner_m ** 2) / 4.0
    q = v * s_pipe

    return {
        "h_moteur_m": round(h_moteur, 2),
        "diff_geom_m": round(diff_geom, 2),
        "v_water_ms": round(v, 2),
        "q_air_m3s": round(q, 2),
        "q_air_m3h": round(q * 3600.0, 1),
        "is_gravity_sufficient": True,
        "comment": "Calcul de casse franche conforme (Strickler-Bernoulli)"
    }


def calculate_air_valve_full_analysis(
    pm: float,
    z_valve: float,
    dn_pipe_m: float,
    pm_upstream: Optional[float],
    z_upstream: Optional[float],
    pm_downstream: Optional[float],
    z_downstream: Optional[float],
    ks_strickler: float = 104.0,
    v_filling_ms: float = 0.5,
    q_nominal_water_m3s: float = 5.3
) -> Dict[str, any]:
    """
    Analyse complète d'un point haut :
    - Écoulement d'air amont et aval en cas de casse franche
    - Qair_max
    - Remplissage (évacuation gros débit)
    - Dégazage (fonctionnement normal)
    """
    # Branche amont
    if pm_upstream is not None and z_upstream is not None:
        l_up = abs(pm - pm_upstream)
        res_up = calculate_strickler_rupture_flow(
            d_inner_m=dn_pipe_m,
            length_m=l_up,
            z_air_valve_m=z_valve,
            z_drain_m=z_upstream,
            ks_strickler=ks_strickler
        )
    else:
        l_up = 0.0
        res_up = {
            "h_moteur_m": 0.0, "diff_geom_m": 0.0, "v_water_ms": 0.0,
            "q_air_m3s": 0.0, "q_air_m3h": 0.0, "is_gravity_sufficient": False,
            "comment": "Pas de tronçon amont"
        }

    # Branche aval
    if pm_downstream is not None and z_downstream is not None:
        l_down = abs(pm_downstream - pm)
        res_down = calculate_strickler_rupture_flow(
            d_inner_m=dn_pipe_m,
            length_m=l_down,
            z_air_valve_m=z_valve,
            z_drain_m=z_downstream,
            ks_strickler=ks_strickler
        )
    else:
        l_down = 0.0
        res_down = {
            "h_moteur_m": 0.0, "diff_geom_m": 0.0, "v_water_ms": 0.0,
            "q_air_m3s": 0.0, "q_air_m3h": 0.0, "is_gravity_sufficient": False,
            "comment": "Pas de tronçon aval"
        }

    q_air_max = max(res_up["q_air_m3s"], res_down["q_air_m3s"])

    # Remplissage
    res_filling = calculate_filling_air_flow(d_inner_m=dn_pipe_m, v_filling_ms=v_filling_ms)

    # Dégazage
    q_degas_m3h = 0.02 * q_nominal_water_m3s * 3600.0

    return {
        "pm": pm,
        "z_valve": z_valve,
        "dn_pipe_m": dn_pipe_m,
        "l_upstream_m": round(l_up, 2),
        "l_downstream_m": round(l_down, 2),
        "res_upstream": res_up,
        "res_downstream": res_down,
        "q_air_upstream_m3s": res_up["q_air_m3s"],
        "q_air_downstream_m3s": res_down["q_air_m3s"],
        "q_air_max_m3s": round(q_air_max, 2),
        "res_filling": res_filling,
        "q_filling_m3h": res_filling["q_air_remplissage_m3h"],
        "q_degas_m3h": round(q_degas_m3h, 1)
    }


# ==============================================================================
# 5. VIDANGES DES POINTS BAS
# ==============================================================================
def calculate_drain_dimensioning(
    dn_pipe_m: float,
    l_upstream_m: float,
    h_upstream_m: float,
    l_downstream_m: float = 0.0,
    h_downstream_m: float = 0.0,
    target_time_hours: float = 2.0,
    discharge_coeff_k: float = 0.70,
    dn_retained_mm: Optional[int] = None
) -> Dict[str, any]:
    """
    Dimensionne l'ouvrage de vidange d'un point bas selon la formule exacte
    avec hauteur moyenne pondérée des deux branches amont et aval.

    Paramètres :
        dn_pipe_m : Diamètre intérieur de la conduite principale (m)
        l_upstream_m : Longueur de la branche amont (m)
        h_upstream_m : Dénivelée de la branche amont (m) = Cote_haut_amont - Cote_vidange
        l_downstream_m : Longueur de la branche aval (m)
        h_downstream_m : Dénivelée de la branche aval (m) = Cote_haut_aval - Cote_vidange
        target_time_hours : Temps cible de vidange en heures (ex: 2.0 h = 7200 s)
        discharge_coeff_k : Coefficient de débit de l'orifice/vanne de vidange (usuellement 0.70)
        dn_retained_mm : Diamètre normalisé retenu en projet pour vérification du temps réel

    Formules exactes :
        V_eau = (pi * D^2 / 4) * (Lam + Lav)
        h_moy = [ Lam * (Ham / 2) + Lav * (Hav / 2) ] / (Lam + Lav)
        d_theorique (mm) = sqrt( V_eau / [ K * (pi/4) * sqrt(2*g*h_moy) * t_sec ] ) * 1000
                         = (D / sqrt(t_sec)) * sqrt( L_tot / (K * sqrt(2*g*h_moy)) ) * 1000

        Pour t = 2h (7200 s), K = 0.70, g = 9.81 :
            coeff = 1000 / sqrt( 7200 * 0.70 * sqrt(2 * 9.81) ) = 6.693
            d_theorique (mm) = 6.69 * D * sqrt( L_tot / sqrt(h_moy) )

        Temps réel de vidange avec un diamètre donné d_reel :
            t_reel (heures) = t_cible * (d_theorique / d_reel)^2
    """
    l_tot = l_upstream_m + l_downstream_m
    if l_tot <= 0 or dn_pipe_m <= 0:
        raise ValueError("La longueur totale et le diamètre de la conduite doivent être positifs.")

    t_sec = target_time_hours * 3600.0

    # Volume d'eau total à vidanger
    section_pipe = math.pi * (dn_pipe_m ** 2) / 4.0
    v_water_m3 = section_pipe * l_tot

    # Hauteur moyenne pondérée
    # Attention aux branches nulles ou à dénivelée négative/nulle
    h_am = max(0.01, h_upstream_m)
    h_av = max(0.01, h_downstream_m) if l_downstream_m > 0 else 0.0

    if l_downstream_m > 0:
        h_moy = (l_upstream_m * (h_am / 2.0) + l_downstream_m * (h_av / 2.0)) / l_tot
    else:
        h_moy = h_am / 2.0

    # Calcul exact du diamètre théorique
    # d = sqrt( (4 * V_water) / (pi * K * sqrt(2*g*h_moy) * t_sec) ) * 1000
    coeff_exact = 1000.0 / math.sqrt(t_sec * discharge_coeff_k * math.sqrt(2.0 * G))
    d_exact_mm = coeff_exact * dn_pipe_m * math.sqrt(l_tot / math.sqrt(h_moy))

    # Formule simplifiée avec coeff 6.69 pour t=2h
    coeff_doc_2h = 6.69
    d_doc_formula_mm = coeff_doc_2h * dn_pipe_m * math.sqrt(l_tot / math.sqrt(h_moy))

    # Choix du DN normalisé standard recommandé
    from core.catalog import get_standard_dn_drain
    dn_recommended = get_standard_dn_drain(d_exact_mm)

    # Vérification avec le DN retenu ou le DN recommandé
    dn_check = dn_retained_mm if dn_retained_mm else dn_recommended
    t_real_hours = target_time_hours * ((d_exact_mm / float(dn_check)) ** 2)

    # Débit moyen déchargé
    q_moy_m3s = v_water_m3 / (t_real_hours * 3600.0)

    # Diagnostics et alertes
    is_compliant = t_real_hours <= target_time_hours + 0.05  # marge de 3 min
    if is_compliant:
        status_msg = f"Conforme : temps de vidange {round(t_real_hours, 2)} h <= {target_time_hours} h"
    else:
        depassement_min = int((t_real_hours - target_time_hours) * 60)
        status_msg = (
            f"Non conforme : sous-dimensionné ! Temps réel {round(t_real_hours, 2)} h "
            f"(dépassement de {depassement_min} min par rapport aux {target_time_hours} h prévues)"
        )

    return {
        "l_total_m": round(l_tot, 2),
        "v_water_m3": round(v_water_m3, 1),
        "h_moy_m": round(h_moy, 2),
        "sqrt_h_moy": round(math.sqrt(h_moy), 4),
        "coeff_exact": round(coeff_exact, 3),
        "d_exact_mm": round(d_exact_mm, 1),
        "d_doc_formula_mm": round(d_doc_formula_mm, 1),
        "dn_recommended_mm": dn_recommended,
        "dn_check_mm": dn_check,
        "t_real_hours": round(t_real_hours, 2),
        "t_real_formatted": format_hours_minutes(t_real_hours),
        "q_moy_m3s": round(q_moy_m3s, 3),
        "is_compliant": is_compliant,
        "status_message": status_msg
    }


def format_hours_minutes(hours_float: float) -> str:
    """Formate une durée décimale en heures et minutes (ex: 2h14)."""
    h = int(hours_float)
    m = int(round((hours_float - h) * 60.0))
    if m >= 60:
        h += 1
        m -= 60
    return f"{h}h{m:02d}"
