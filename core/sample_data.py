"""
Jeu de données de référence issu de la Note de calcul et de l'Audit technique
du projet Adduction BR3_LOT 8.
Permet d'initialiser immédiatement l'application avec les données réelles vérifiées.
"""

from core.project_data import HydraulicProject, AirValvePoint, DrainPoint
from core.catalogues_ceai_snh import CATALOG_PAM_SNH


def load_br3_lot8_project() -> HydraulicProject:
    """Crée et retourne le projet BR3_LOT 8 avec ses 10 ventouses et 9 vidanges."""
    project = HydraulicProject(
        name="Adduction BR3_LOT 8 (Référence Audit)",
        description="Audit et recalculs complets des organes de sécurité hydraulique (ventouses et vidanges)",
        dn_main_conduite_m=2.0,
        pipe_material="PRV (Polyester Renforcé Verre)",
        pipe_thickness_m=0.035,
        ks_strickler=104.0,
        v_filling_ms=0.5,
        delta_p_admiss_mce=3.0,
        q_nominal_water_m3s=5.3,
        target_drain_time_hours=2.0,
        drain_discharge_k=0.70,
        air_catalog_config=CATALOG_PAM_SNH,
    )

    # 10 Points Hauts (Ventouses) de l'Annexe 1
    # ID, PM, Cote, DN, PM_am, Cote_am, PM_av, Cote_av, Init_Equip, Init_Qadmis
    valves_data = [
        (1, 50529.89, 112.98, 2.0, 49681.60, 99.05, 50741.60, 110.40, "2 Ventouses DN200 + 1 Clapet DN250", 21.33),
        (2, 51041.59, 111.50, 2.0, 50741.60, 110.40, 51801.59, 105.55, "1 Purgeur sonique PSA250 + 1 Clapet DN250", 13.00),
        (3, 51801.59, 105.55, 2.0, None, None, 52621.60, 100.64, "1 Ventouse DN200", 4.17),
        (4, 53561.59, 103.40, 2.0, 52621.60, 100.64, 54041.60, 98.40, "1 Purgeur sonique PSA250 + 1 Clapet DN250", 13.00),
        (5, 54264.59, 102.00, 2.0, 54041.60, 98.40, 54661.60, 99.30, "1 Ventouse DN200 + 1 Clapet DN200", 11.97),
        (6, 54783.45, 102.40, 2.0, 54661.60, 99.30, 55081.60, 94.90, "1 Ventouse DN200 + 1 Clapet DN250", 17.17),
        (7, 55241.59, 100.60, 2.0, 55081.60, 94.90, 55781.60, 94.30, "1 Ventouse DN200 + 1 Clapet DN250", 17.17),
        (8, 56201.59, 96.40, 2.0, 55781.60, 94.30, 56422.30, 91.00, "1 Ventouse DN200 + 1 Clapet DN250", 17.17),
        (9, 57121.59, 101.80, 1.6, 56845.30, 5.60, 58721.60, 93.80, "1 Ventouse DN200 + 3 Clapets DN250", 43.17),
        (10, 58961.59, 94.50, 2.0, 58721.60, 93.80, 59701.60, 90.80, "1 Ventouse DN200 + 1 Clapet DN200", 11.97),
    ]

    for item in valves_data:
        v = AirValvePoint(
            id=item[0],
            pm=item[1],
            z_terrain=item[2],
            dn_conduite_m=item[3],
            pm_amont=item[4],
            z_amont=item[5],
            pm_aval=item[6],
            z_aval=item[7],
            initial_equipment=item[8],
            initial_flow_admitted=item[9]
        )
        project.air_valves.append(v)

    # 9 Points Bas (Vidanges) de l'Annexe 2
    # ID, PM, Cote, DN, PM_am, Cote_am, PM_av, Cote_av, DN_init_doc
    drains_data = [
        (1, 50741.59, 110.41, 2.0, 50529.89, 112.98, 51041.59, 111.50, 400),
        (2, 52621.59, 100.64, 2.0, 51801.59, 105.55, 53561.59, 103.40, 400),
        (3, 54041.59, 98.41, 2.0, 53561.59, 103.40, 54264.59, 102.00, 400),
        (4, 54661.59, 99.29, 2.0, 54264.59, 102.00, 54783.45, 102.40, 400),
        (5, 55081.59, 94.94, 2.0, 54783.45, 102.40, 55241.59, 100.60, 400),
        (6, 55781.59, 94.33, 2.0, 55241.59, 100.60, 56201.59, 96.40, 400),
        (7, 56845.25, 5.62, 1.6, 56201.59, 96.40, 57121.59, 101.80, 150),
        (8, 58721.59, 93.82, 2.0, 57121.59, 101.80, 58961.59, 94.50, 400),
        (9, 59701.59, 90.84, 2.0, 58961.59, 94.50, None, None, 400),
    ]

    for item in drains_data:
        d = DrainPoint(
            id=item[0],
            pm=item[1],
            z_terrain=item[2],
            dn_conduite_m=item[3],
            pm_amont=item[4],
            z_amont=item[5],
            pm_aval=item[6],
            z_aval=item[7],
            dn_initial_doc_mm=item[8],
            dn_retained_mm=item[8]  # Initialisé avec le choix de la note initiale pour voir l'impact
        )
        project.drains.append(d)

    # Exécution des calculs hydrauliques
    project.calculate_all()
    return project
