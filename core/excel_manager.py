"""
Gestionnaire d'import et d'export Excel (XLSX) pour l'application MK-St_Venant.
Utilise openpyxl avec un stylage professionnel (en-têtes foncés, bordures, formatage conditionnel).
"""

from typing import Optional, Dict, Any, Tuple
import re
import unicodedata
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from core.project_data import HydraulicProject, AirValvePoint, DrainPoint
from core.catalogues_ceai_snh import (
    CATALOG_CONFIG_LABELS,
    CLAPETS_CEAI,
    DEFAULT_AIR_CATALOG_CONFIG,
    PRESSION_REFERENCE,
    PURGEURS_SONIQUES_SNH,
    VENTOUSES_TRIFON_CEAI,
)


# Styles de cellules
FONT_TITLE = Font(name="Segoe UI", size=14, bold=True, color="1F497D")
FONT_SUBTITLE = Font(name="Segoe UI", size=11, bold=True, color="595959")
FONT_HEADER = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
FONT_DATA = Font(name="Segoe UI", size=10)
FONT_BOLD = Font(name="Segoe UI", size=10, bold=True)
FONT_ALERT = Font(name="Segoe UI", size=10, bold=True, color="C00000")
FONT_SUCCESS = Font(name="Segoe UI", size=10, bold=True, color="008000")

FILL_HEADER_BLUE = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
FILL_HEADER_TEAL = PatternFill(start_color="008080", end_color="008080", fill_type="solid")
FILL_HEADER_DARK = PatternFill(start_color="2F3542", end_color="2F3542", fill_type="solid")
FILL_ZEBRA = PatternFill(start_color="F2F5F8", end_color="F2F5F8", fill_type="solid")
FILL_SUCCESS = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
FILL_ALERT = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")

BORDER_THIN = Border(
    left=Side(style='thin', color="D9D9D9"),
    right=Side(style='thin', color="D9D9D9"),
    top=Side(style='thin', color="D9D9D9"),
    bottom=Side(style='thin', color="D9D9D9")
)

# Libellés Excel ↔ champs de core.project_data.ProjectIdentity
IDENTITY_LABEL_TO_FIELD: dict[str, str] = {
    "Maître d'Ouvrage (MO)": "maitre_ouvrage",
    "Maitre d'Ouvrage (MO)": "maitre_ouvrage",
    "MO": "maitre_ouvrage",
    "Maître d'Œuvre": "maitre_oeuvre",
    "Maitre d'Oeuvre": "maitre_oeuvre",
    "Bureau d'Études Techniques (BET)": "bureau_etudes",
    "BET": "bureau_etudes",
    "Lieu": "lieu",
    "Commune": "commune",
    "Province / Région": "province",
    "Province": "province",
    "Région": "province",
    "Pays": "pays",
    "N° de marché / lot": "numero_marche",
    "Numero de marche": "numero_marche",
    "Année": "annee",
    "Responsable du projet": "responsable_projet",
    "Date de l'étude": "date_etude",
    "Référence dossier": "reference_dossier",
    "Introduction du rapport": "introduction",
    "Préambule du rapport": "preamble",
}


def export_project_to_xlsx(project: HydraulicProject, filepath: str):
    """Exporte l'intégralité du projet hydraulique vers un classeur Excel soigné."""
    project.calculate_all()
    wb = openpyxl.Workbook()

    # 1. FEUILLE DE SYNTHÈSE
    ws_summary = wb.active
    ws_summary.title = "Synthèse & Paramètres"
    ws_summary.views.sheetView[0].showGridLines = True

    ws_summary["A1"] = "RAPPORT D'EXPERTISE HYDRAULIQUE — MK-ST_VENANT"
    ws_summary["A1"].font = FONT_TITLE
    ws_summary["A2"] = f"Projet : {project.name}"
    ws_summary["A2"].font = FONT_SUBTITLE
    ws_summary["A3"] = f"Description : {project.description}"
    ws_summary["A3"].font = FONT_DATA

    stats = project.get_summary_stats()

    # Paramètres généraux
    catalog_label = CATALOG_CONFIG_LABELS.get(
        getattr(project, "air_catalog_config", DEFAULT_AIR_CATALOG_CONFIG),
        str(getattr(project, "air_catalog_config", DEFAULT_AIR_CATALOG_CONFIG)),
    )
    params_data = [
        ("Paramètre Hydraulique", "Valeur", "Unité"),
        ("Base catalogue organes d'air", catalog_label, "-"),
        ("Diamètre principal de la conduite", project.dn_main_conduite_m, "m"),
        ("Matériau de la conduite", project.pipe_material, "-"),
        ("Épaisseur nominale", project.pipe_thickness_m * 1000.0, "mm"),
        ("Coefficient de Strickler (PRV / Matériau)", project.ks_strickler, "m^(1/3)/s"),
        ("Célérité exacte d'Allievi calculée", stats["wave_speed_allievi_ms"], "m/s"),
        ("Vitesse de remplissage préconisée", project.v_filling_ms, "m/s"),
        ("Dépression admissible (casse franche)", project.delta_p_admiss_mce, "mCE"),
        ("Débit nominal d'eau en service", project.q_nominal_water_m3s, "m3/s"),
        ("Temps objectif de vidange des points bas", project.target_drain_time_hours, "heures"),
        ("Coefficient de débit orifice vidange (K)", project.drain_discharge_k, "-")
    ]

    start_row = 6
    ws_summary.cell(row=start_row-1, column=1, value="PARAMÈTRES GÉNÉRAUX DU PROJET").font = FONT_BOLD

    for r_idx, row_values in enumerate(params_data):
        for c_idx, val in enumerate(row_values):
            cell = ws_summary.cell(row=start_row + r_idx, column=c_idx + 1, value=val)
            cell.border = BORDER_THIN
            if r_idx == 0:
                cell.font = FONT_HEADER
                cell.fill = FILL_HEADER_BLUE
            else:
                cell.font = FONT_DATA
                if r_idx % 2 == 1:
                    cell.fill = FILL_ZEBRA

    # Indicateurs clés
    kpi_start_col = 5
    ws_summary.cell(row=start_row-1, column=kpi_start_col, value="INDICATEURS CLÉS & CONFORMITÉ").font = FONT_BOLD
    kpis = [
        ("Indicateur", "Valeur"),
        ("Nombre de points hauts (ventouses)", stats["total_air_valves"]),
        ("Ventouses conformes", f"{stats['air_valves_compliant']} / {stats['total_air_valves']}"),
        ("Ventouses sous-équipées / à adapter", stats["air_valves_non_compliant"]),
        ("Nombre de points bas (vidanges)", stats["total_drains"]),
        ("Vidanges conformes au temps cible", f"{stats['drains_compliant']} / {stats['total_drains']}"),
        ("Vidanges sous-dimensionnées", stats["drains_non_compliant"]),
        ("Volume d'eau total à vidanger", f"{stats['total_water_volume_m3']:,.1f} m3"),
        ("Débit max d'air requis (casse franche)", f"{stats['max_air_intake_m3s']:.2f} m3/s")
    ]

    for r_idx, (k, v) in enumerate(kpis):
        cell_k = ws_summary.cell(row=start_row + r_idx, column=kpi_start_col, value=k)
        cell_v = ws_summary.cell(row=start_row + r_idx, column=kpi_start_col + 1, value=v)
        cell_k.border = BORDER_THIN
        cell_v.border = BORDER_THIN
        if r_idx == 0:
            cell_k.font = FONT_HEADER
            cell_v.font = FONT_HEADER
            cell_k.fill = FILL_HEADER_DARK
            cell_v.fill = FILL_HEADER_DARK
        else:
            cell_k.font = FONT_DATA
            cell_v.font = FONT_BOLD
            if "sous" in k.lower() and int(str(v).split()[0]) > 0:
                cell_v.fill = FILL_ALERT
                cell_v.font = FONT_ALERT

    # 1bis. FEUILLE DONNÉES DU PROJET (identité, intro et préambule des rapports)
    ws_identity = wb.create_sheet(title="Données Projet")
    ws_identity["A1"] = "IDENTIFICATION DU PROJET — REPRISE AUTOMATIQUE DANS LES RAPPORTS"
    ws_identity["A1"].font = FONT_TITLE

    identity = getattr(project, "identity", None)
    identity_labels = {
        "maitre_ouvrage": "Maître d'Ouvrage (MO)",
        "maitre_oeuvre": "Maître d'Œuvre",
        "bureau_etudes": "Bureau d'Études Techniques (BET)",
        "lieu": "Lieu",
        "commune": "Commune",
        "province": "Province / Région",
        "pays": "Pays",
        "numero_marche": "N° de marché / lot",
        "annee": "Année",
        "responsable_projet": "Responsable du projet",
        "date_etude": "Date de l'étude",
        "reference_dossier": "Référence dossier",
        "introduction": "Introduction du rapport",
        "preamble": "Préambule du rapport",
    }
    identity_rows = [("Intitulé du projet", project.name), ("Description / objet", project.description)]
    if identity is not None:
        identity_rows.extend(
            (identity_labels.get(key, key), value)
            for key, value in vars(identity).items()
        )
    identity_rows.append(("Base catalogue organes d'air", catalog_label))

    for c_idx, header in enumerate(("Information", "Valeur"), 1):
        cell = ws_identity.cell(row=3, column=c_idx, value=header)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER_BLUE
        cell.border = BORDER_THIN
    for r_idx, (key, value) in enumerate(identity_rows, 4):
        cell_k = ws_identity.cell(row=r_idx, column=1, value=key)
        cell_v = ws_identity.cell(row=r_idx, column=2, value=value)
        cell_k.font = FONT_BOLD
        cell_v.font = FONT_DATA
        cell_k.border = BORDER_THIN
        cell_v.border = BORDER_THIN
        cell_v.alignment = Alignment(wrap_text=True, vertical="top")
        if r_idx % 2 == 0:
            cell_k.fill = FILL_ZEBRA
            cell_v.fill = FILL_ZEBRA
    ws_identity.column_dimensions["A"].width = 34
    ws_identity.column_dimensions["B"].width = 90

    # 2. FEUILLE POINTS HAUTS (VENTOUSES)
    ws_valves = wb.create_sheet(title="Points Hauts - Ventouses")
    ws_valves.views.sheetView[0].showGridLines = True

    ws_valves["A1"] = "TABLEAU DE DIMENSIONNEMENT ET VÉRIFICATION DES VENTOUSES (POINTS HAUTS)"
    ws_valves["A1"].font = FONT_TITLE

    headers_valves = [
        "N°", "PM Point Haut", "Cote Terrain (m)", "DN Conduite (m)",
        "PM Amont", "Cote Amont (m)", "L Amont (m)", "H Amont (m)", "Qair Amont (m3/s)",
        "PM Aval", "Cote Aval (m)", "L Aval (m)", "H Aval (m)", "Qair Aval (m3/s)",
        "Qair Max Requis (m3/s)", "Q Remplissage (m3/h)", "Q Dégazage (m3/h)",
        "Équipement Initial", "Q Admis Initial (m3/s)",
        "Équipement Recommandé", "Q Admis Recommandé (m3/s)", "Conformité", "Diagnostic & Commentaires"
    ]

    for c_idx, h in enumerate(headers_valves, 1):
        cell = ws_valves.cell(row=3, column=c_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER_BLUE
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER_THIN
    ws_valves.row_dimensions[3].height = 35

    for r_idx, v in enumerate(project.air_valves, 4):
        vals = [
            v.id, v.pm, v.z_terrain, v.dn_conduite_m,
            v.pm_amont if v.pm_amont is not None else "-", v.z_amont if v.z_amont is not None else "-", v.l_amont_m, v.h_amont_m, v.q_air_amont_m3s,
            v.pm_aval if v.pm_aval is not None else "-", v.z_aval if v.z_aval is not None else "-", v.l_aval_m, v.h_aval_m, v.q_air_aval_m3s,
            v.q_air_max_m3s, v.q_filling_m3h, v.q_degas_m3h,
            v.initial_equipment, v.initial_flow_admitted,
            v.recommended_equipment, v.q_admis_m3s,
            "CONFORME" if v.is_compliant else "NON CONFORME",
            v.comment
        ]
        for c_idx, val in enumerate(vals, 1):
            cell = ws_valves.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_DATA
            cell.border = BORDER_THIN
            if r_idx % 2 == 1:
                cell.fill = FILL_ZEBRA
            if c_idx in [2, 3, 4, 7, 8, 9, 12, 13, 14, 15, 16, 17, 19, 21]:
                cell.alignment = Alignment(horizontal="right")
            elif c_idx in [1, 22]:
                cell.alignment = Alignment(horizontal="center")

            # Coloriage conformité
            if c_idx == 22:
                if v.is_compliant:
                    cell.fill = FILL_SUCCESS
                    cell.font = FONT_SUCCESS
                else:
                    cell.fill = FILL_ALERT
                    cell.font = FONT_ALERT

    # 3. FEUILLE POINTS BAS (VIDANGES)
    ws_drains = wb.create_sheet(title="Points Bas - Vidanges")
    ws_drains.views.sheetView[0].showGridLines = True

    target_label = f"{float(getattr(project, 'target_drain_time_hours', 2.0) or 2.0):g}h"
    ws_drains["A1"] = f"TABLEAU DE DIMENSIONNEMENT ET VÉRIFICATION DES VIDANGES (POINTS BAS) — OBJECTIF {target_label}"
    ws_drains["A1"].font = FONT_TITLE

    headers_drains = [
        "N°", "PM Point Bas", "Cote Point Bas (m)", "DN Conduite (m)",
        "PM Amont", "Cote Amont (m)", "L Amont (m)", "H Amont (m)",
        "PM Aval", "Cote Aval (m)", "L Aval (m)", "H Aval (m)",
        "L Totale (m)", "Hauteur Moy hmoy (m)", "Volume Eau (m3)",
        f"d Théorique Exact t={target_label} (mm)", "DN Recommandé (mm)",
        "DN Retenu Projet (mm)", "Temps Réel Vidange", f"Statut Temps Cible ({target_label})", "Observations d'Exploitation"
    ]

    for c_idx, h in enumerate(headers_drains, 1):
        cell = ws_drains.cell(row=3, column=c_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER_TEAL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER_THIN
    ws_drains.row_dimensions[3].height = 35

    for r_idx, d in enumerate(project.drains, 4):
        vals = [
            d.id, d.pm, d.z_terrain, d.dn_conduite_m,
            d.pm_amont if d.pm_amont is not None else "-", d.z_amont if d.z_amont is not None else "-", d.l_amont_m, d.h_amont_m,
            d.pm_aval if d.pm_aval is not None else "-", d.z_aval if d.z_aval is not None else "-", d.l_aval_m, d.h_aval_m,
            d.l_total_m, d.h_moy_m, d.volume_water_m3,
            d.d_exact_mm, d.dn_recommended_mm,
            d.dn_retained_mm, d.t_real_str,
            f"CONFORME (<= {target_label})" if d.is_compliant else f"NON CONFORME (> {target_label})",
            d.comment
        ]
        for c_idx, val in enumerate(vals, 1):
            cell = ws_drains.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_DATA
            cell.border = BORDER_THIN
            if r_idx % 2 == 1:
                cell.fill = FILL_ZEBRA
            if c_idx in [2, 3, 4, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18]:
                cell.alignment = Alignment(horizontal="right")
            elif c_idx in [1, 19, 20]:
                cell.alignment = Alignment(horizontal="center")

            # Coloriage conformité
            if c_idx == 20:
                if d.is_compliant:
                    cell.fill = FILL_SUCCESS
                    cell.font = FONT_SUCCESS
                else:
                    cell.fill = FILL_ALERT
                    cell.font = FONT_ALERT

    # 4. FEUILLE CATALOGUE DE MATÉRIEL
    ws_cat = wb.create_sheet(title="Catalogue Équipements")
    ws_cat.views.sheetView[0].showGridLines = True
    ws_cat["A1"] = f"CATALOGUE DES ÉQUIPEMENTS D'AIR — CEAI/SNH, PAM/SNH ET MCP ({PRESSION_REFERENCE})"
    ws_cat["A1"].font = FONT_TITLE

    from core.catalog import PAM_TRIPLE_FUNCTION_VALVES, SNH_AIR_INLET_VALVES
    cat_headers = ["Type d'Organe", "Modèle / Famille", "DN", "Admission (m3/s)", "Admission (m3/h)", "Évacuation / Remarque", "Origine / Description"]
    for c_idx, h in enumerate(cat_headers, 1):
        cell = ws_cat.cell(row=3, column=c_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER_DARK
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER_THIN

    row_c = 4

    def _add_cat_row(values):
        nonlocal row_c
        for c_idx, val in enumerate(values, 1):
            cell = ws_cat.cell(row=row_c, column=c_idx, value=val)
            cell.border = BORDER_THIN
            cell.font = FONT_DATA
        row_c += 1

    # Référence CEAI/SNH
    for org in VENTOUSES_TRIFON_CEAI:
        _add_cat_row([org.famille, "Trifon CEAI", org.dn, round(org.capacite_m3s, 4), org.capacite_m3h, org.retenu, org.origine])
    for org in CLAPETS_CEAI:
        _add_cat_row([org.famille, "Clapet CEAI", org.dn, round(org.capacite_m3s, 4), org.capacite_m3h, org.retenu, org.origine])
    for org in PURGEURS_SONIQUES_SNH:
        _add_cat_row([org.famille, "Purgeur sonique SNH", org.dn, round(org.capacite_m3s, 6), org.capacite_m3h, f"Purge continue ({org.retenu})", org.origine])

    # Existant PAM/SNH
    for dn, spec in PAM_TRIPLE_FUNCTION_VALVES.items():
        _add_cat_row(["Ventouse Triple Fonction (existant)", spec.model, f"DN{spec.dn_mm}", spec.admission_flow_3m_m3s, spec.admission_flow_3m_m3h, f"Évacuation 1 mCE: {spec.exhaust_flow_1m_m3h} m3/h", spec.description])
    for dn, spec in SNH_AIR_INLET_VALVES.items():
        _add_cat_row(["Clapet d'Entrée d'Air (existant)", spec.model, f"DN{spec.dn_mm}", spec.admission_flow_3m_m3s, spec.admission_flow_3m_m3h, "-", spec.description])

    # Catalogue MCP (tableau Excel)
    from core.catalog_mcp import SOURCE_XLSX, VENTOUSES_MCP
    for v in VENTOUSES_MCP:
        _add_cat_row([
            "Ventouse MCP double orifice 3 fonctions", v.dn_label, v.dn_label,
            round(v.admission_3mce_m3s, 4), v.admission_opt_m3h,
            f"Évacuation 0,1 bar : {v.evacuation_1mce_m3h:,.0f} m3/h ; admission critique -0,5 bar : {v.admission_crit_m3h:,.0f} m3/h",
            f"{SOURCE_XLSX} — {v.courbe} ; {v.notes}",
        ])

    # Ajustement largeur automatique des colonnes pour toutes les feuilles
    for ws in [ws_summary, ws_identity, ws_valves, ws_drains, ws_cat]:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if '\n' in val_str:
                    lines = val_str.split('\n')
                    max_len = max(max_len, max(len(line) for line in lines))
                else:
                    max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 11), 45)

    wb.save(filepath)
    return filepath


def create_blank_import_template(filepath: str):
    """Génère un modèle vierge XLSX documenté que l'utilisateur peut remplir et importer."""
    wb = openpyxl.Workbook()

    # Feuille Ventouses
    ws_valves = wb.active
    ws_valves.title = "Points_Hauts_Ventouses"
    headers_valves = ["PM", "Cote_Terrain_m", "DN_Conduite_m", "PM_Amont", "Cote_Amont_m", "PM_Aval", "Cote_Aval_m", "Equipement_Initial", "Qadmis_Initial_m3s"]
    for c, h in enumerate(headers_valves, 1):
        cell = ws_valves.cell(row=1, column=c, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER_BLUE
        cell.border = BORDER_THIN

    # Exemple de ligne
    example_valve = [50529.89, 112.98, 2.0, 49681.60, 99.05, 50741.60, 110.40, "2 Ventouses DN200 + 1 Clapet DN250", 21.33]
    for c, val in enumerate(example_valve, 1):
        cell = ws_valves.cell(row=2, column=c, value=val)
        cell.font = FONT_DATA
        cell.border = BORDER_THIN

    # Feuille Vidanges
    ws_drains = wb.create_sheet(title="Points_Bas_Vidanges")
    headers_drains = ["PM", "Cote_Point_Bas_m", "DN_Conduite_m", "PM_Amont", "Cote_Amont_m", "PM_Aval", "Cote_Aval_m", "DN_Retenu_mm"]
    for c, h in enumerate(headers_drains, 1):
        cell = ws_drains.cell(row=1, column=c, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER_TEAL
        cell.border = BORDER_THIN

    example_drain = [50741.59, 110.41, 2.0, 50529.89, 112.98, 51041.59, 111.50, 400]
    for c, val in enumerate(example_drain, 1):
        cell = ws_drains.cell(row=2, column=c, value=val)
        cell.font = FONT_DATA
        cell.border = BORDER_THIN

    # Feuille Données Projet (identité + textes des rapports)
    ws_info = wb.create_sheet(title="Données_Projet")
    for c, header in enumerate(("Champ", "Valeur"), 1):
        cell = ws_info.cell(row=1, column=c, value=header)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER_BLUE
        cell.border = BORDER_THIN
    info_rows = [
        ("Intitulé du projet", ""),
        ("Description / objet", ""),
        ("Maître d'Ouvrage (MO)", ""),
        ("Maître d'Œuvre", ""),
        ("Bureau d'Études Techniques (BET)", ""),
        ("Lieu", ""),
        ("Commune", ""),
        ("Province / Région", ""),
        ("Pays", ""),
        ("N° de marché / lot", ""),
        ("Année", ""),
        ("Responsable du projet", ""),
        ("Date de l'étude", ""),
        ("Référence dossier", ""),
        ("Introduction du rapport", ""),
        ("Préambule du rapport", ""),
    ]
    for r, (key, value) in enumerate(info_rows, 2):
        cell_k = ws_info.cell(row=r, column=1, value=key)
        cell_v = ws_info.cell(row=r, column=2, value=value)
        cell_k.font = FONT_BOLD
        cell_v.font = FONT_DATA
        cell_k.border = BORDER_THIN
        cell_v.border = BORDER_THIN

    for ws in [ws_valves, ws_drains, ws_info]:
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = 22
    ws_info.column_dimensions["A"].width = 34
    ws_info.column_dimensions["B"].width = 80

    wb.save(filepath)
    return filepath


def import_project_from_xlsx(filepath: str) -> HydraulicProject:
    """
    Importe les points hauts et bas depuis un fichier Excel avec détection intelligente des colonnes.
    """
    wb = openpyxl.load_workbook(filepath, data_only=True)
    project = HydraulicProject(
        name="Projet Importé Excel",
        description=f"Importé depuis {filepath.split('/')[-1].split(chr(92))[-1]}"
    )

    # 0. Feuille « Données Projet » : identité, introduction et préambule
    sheet_identity = None
    for sheet_name in wb.sheetnames:
        normalized_name = _normalize_header(unicodedata.normalize("NFKD", sheet_name).encode("ascii", "ignore").decode())
        if "donnees projet" in normalized_name or "identite projet" in normalized_name:
            sheet_identity = wb[sheet_name]
            break
    if sheet_identity is not None:
        labels: Dict[str, Any] = {}
        for r in range(1, min(sheet_identity.max_row, 60) + 1):
            key = sheet_identity.cell(row=r, column=1).value
            value = sheet_identity.cell(row=r, column=2).value
            if key is None:
                continue
            normalized_key = _normalize_header(unicodedata.normalize("NFKD", str(key)).encode("ascii", "ignore").decode())
            labels[normalized_key] = value

        identity_map = {
            _normalize_header(unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()): field
            for label, field in IDENTITY_LABEL_TO_FIELD.items()
        }
        identity_map["intitule du projet"] = "name"
        identity_map["intitule projet"] = "name"
        identity_map["description objet"] = "description"
        identity_map["description / objet"] = "description"
        for normalized_key, value in labels.items():
            target = identity_map.get(normalized_key)
            if target is None:
                continue
            text = "" if value is None else str(value).strip()
            if target in ("name", "description"):
                if text:
                    setattr(project, target, text)
            else:
                setattr(project.identity, target, text)

    # 0bis. Feuille « Synthèse & Paramètres » : restaurer les paramètres
    # généraux, notamment le temps objectif qui ne doit jamais retomber à 2 h.
    sheet_params = None
    for sheet_name in wb.sheetnames:
        normalized_name = _normalize_header(
            unicodedata.normalize("NFKD", sheet_name).encode("ascii", "ignore").decode()
        )
        if "synthese" in normalized_name or "parametre" in normalized_name:
            sheet_params = wb[sheet_name]
            break

    if sheet_params is not None:
        param_matchers = [
            ("temps objectif de vidange", "target_drain_time_hours"),
            ("coefficient de debit orifice vidange", "drain_discharge_k"),
            ("diametre principal", "dn_main_conduite_m"),
            ("vitesse de remplissage", "v_filling_ms"),
            ("depression admissible", "delta_p_admiss_mce"),
            ("debit nominal", "q_nominal_water_m3s"),
            ("coefficient de strickler", "ks_strickler"),
            ("epaisseur nominale", "pipe_thickness_m"),
        ]
        for r in range(1, min(sheet_params.max_row, 80) + 1):
            key = sheet_params.cell(row=r, column=1).value
            value = sheet_params.cell(row=r, column=2).value
            if key is None or value is None:
                continue
            nk = _normalize_header(
                unicodedata.normalize("NFKD", str(key)).encode("ascii", "ignore").decode()
            )
            text = str(value).strip()

            if "materiau de la conduite" in nk:
                project.pipe_material = text
                continue
            if "base catalogue" in nk:
                for cfg_key, cfg_label in CATALOG_CONFIG_LABELS.items():
                    if text == cfg_label or text == cfg_key:
                        project.air_catalog_config = cfg_key
                        break
                continue

            for fragment, field_name in param_matchers:
                if fragment in nk:
                    numeric = parse_float_safe(value)
                    if numeric is None:
                        break
                    if field_name == "pipe_thickness_m":
                        numeric /= 1000.0
                    setattr(project, field_name, numeric)
                    break

    # 1. Recherche feuille ventouses
    sheet_valves = None
    for name in wb.sheetnames:
        lower = name.lower()
        if "ventouse" in lower or "haut" in lower or "air" in lower:
            sheet_valves = wb[name]
            break
    if sheet_valves is None and len(wb.sheetnames) > 0:
        sheet_valves = wb.sheetnames[0]

    if sheet_valves:
        ws = wb[sheet_valves] if isinstance(sheet_valves, str) else sheet_valves
        # Trouver la ligne d'en-tête
        header_row = 1
        headers_map = {}
        for r in range(1, min(10, ws.max_row + 1)):
            row_vals = [str(ws.cell(r, c).value or '').strip().lower() for c in range(1, ws.max_column + 1)]
            if any("pm" in v for v in row_vals):
                header_row = r
                for c_idx, v in enumerate(row_vals, 1):
                    headers_map[v] = c_idx
                break

        # Lecture des lignes de données
        id_counter = 1
        for r in range(header_row + 1, ws.max_row + 1):
            row_dict = {}
            for h_name, c_idx in headers_map.items():
                row_dict[h_name] = ws.cell(r, c_idx).value

            pm_val = parse_float_safe(_get_by_keys(row_dict, ["pm", "point metrique", "pm ventouse", "pm point haut", "pk"]))
            if pm_val is None or pm_val < 0:
                continue

            z_val = parse_float_safe(_get_by_keys(row_dict, ["cote terrain", "cote", "z terrain", "altitude", "alt", "z"]))
            dn_val = parse_float_safe(_get_by_keys(row_dict, ["dn conduite", "dn", "diametre"])) or 2.0
            if dn_val > 10.0: # si en mm
                dn_val = dn_val / 1000.0

            pm_am = parse_float_safe(_get_by_keys(row_dict, ["pm amont", "pm am", "vidange amont", "pm vidange amont"]))
            z_am = parse_float_safe(_get_by_keys(row_dict, ["cote amont", "z amont", "cote am", "cote vidange amont"]))
            pm_av = parse_float_safe(_get_by_keys(row_dict, ["pm aval", "pm av", "vidange aval", "pm vidange aval"]))
            z_av = parse_float_safe(_get_by_keys(row_dict, ["cote aval", "z aval", "cote av", "cote vidange aval"]))
            init_equip = str(_get_by_keys(row_dict, ["equipement initial", "equipement", "initial_equipment"]) or "")
            init_flow = parse_float_safe(_get_by_keys(row_dict, ["qadmis initial", "q initial", "qadmis"])) or 0.0

            valve = AirValvePoint(
                id=id_counter,
                pm=pm_val,
                z_terrain=z_val or 0.0,
                dn_conduite_m=dn_val,
                pm_amont=pm_am,
                z_amont=z_am,
                pm_aval=pm_av,
                z_aval=z_av,
                initial_equipment=init_equip,
                initial_flow_admitted=init_flow
            )
            project.air_valves.append(valve)
            id_counter += 1

    # 2. Recherche feuille vidanges
    sheet_drains = None
    for name in wb.sheetnames:
        lower = name.lower()
        if "vidange" in lower or "bas" in lower or "drain" in lower:
            sheet_drains = wb[name]
            break

    if sheet_drains:
        ws = wb[sheet_drains] if isinstance(sheet_drains, str) else sheet_drains
        header_row = 1
        headers_map = {}
        for r in range(1, min(10, ws.max_row + 1)):
            row_vals = [str(ws.cell(r, c).value or '').strip().lower() for c in range(1, ws.max_column + 1)]
            if any("pm" in v for v in row_vals):
                header_row = r
                for c_idx, v in enumerate(row_vals, 1):
                    headers_map[v] = c_idx
                break

        id_counter = 1
        for r in range(header_row + 1, ws.max_row + 1):
            row_dict = {}
            for h_name, c_idx in headers_map.items():
                row_dict[h_name] = ws.cell(r, c_idx).value

            pm_val = parse_float_safe(_get_by_keys(row_dict, ["pm", "point metrique", "pm vidange", "pm point bas", "pk"]))
            if pm_val is None or pm_val < 0:
                continue

            z_val = parse_float_safe(_get_by_keys(row_dict, ["cote point bas", "cote vidange", "cote terrain", "cote", "altitude", "z"]))
            dn_val = parse_float_safe(_get_by_keys(row_dict, ["dn conduite", "dn", "diametre"])) or 2.0
            if dn_val > 10.0:
                dn_val = dn_val / 1000.0

            pm_am = parse_float_safe(_get_by_keys(row_dict, ["pm amont", "pm ventouse amont", "pm am", "ventouse amont"]))
            z_am = parse_float_safe(_get_by_keys(row_dict, ["cote amont", "cote ventouse amont", "z amont", "cote am"]))
            pm_av = parse_float_safe(_get_by_keys(row_dict, ["pm aval", "pm ventouse aval", "pm av", "ventouse aval"]))
            z_av = parse_float_safe(_get_by_keys(row_dict, ["cote aval", "cote ventouse aval", "z aval", "cote av"]))
            dn_ret = parse_float_safe(_get_by_keys(row_dict, ["dn retenu", "dn retenu mm", "dn retenu projet", "dn projet", "dn ret"]))
            dn_ret_int = int(dn_ret) if dn_ret else 400

            drain = DrainPoint(
                id=id_counter,
                pm=pm_val,
                z_terrain=z_val or 0.0,
                dn_conduite_m=dn_val,
                pm_amont=pm_am,
                z_amont=z_am,
                pm_aval=pm_av,
                z_aval=z_av,
                dn_retained_mm=dn_ret_int
            )
            project.drains.append(drain)
            id_counter += 1

    # Déduction et réconciliation automatique des vidanges
    if len(project.drains) == 0 and len(project.air_valves) > 0:
        # Si la feuille Vidanges est absente ou vide, générer automatiquement les points bas
        # à partir des points amont et aval définis sur les ventouses !
        project.auto_generate_drains_from_valves()
    elif len(project.drains) > 0 and len(project.air_valves) > 0:
        # Réconcilier la topologie pour corriger d'éventuels PM mal saisis ou inversés avec les cotes
        project.reconcile_topology()

    project.calculate_all()
    return project


def _normalize_header(text: str) -> str:
    """Normalise un texte d'en-tête pour recherche tolérante."""
    return str(text or '').lower().replace('_', ' ').replace('-', ' ').replace('(', ' ').replace(')', ' ').strip()


def _get_by_keys(d: Dict[str, Any], keys: list) -> Any:
    """Recherche tolérante de valeur dans un dictionnaire d'en-têtes."""
    normalized_dict = {_normalize_header(k): v for k, v in d.items()}
    for k in keys:
        norm_k = _normalize_header(k)
        for actual_k, val in normalized_dict.items():
            if norm_k == actual_k or norm_k in actual_k:
                return val
    return None


def parse_float_safe(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        s = str(val).replace(',', '.').strip()
        s = re.sub(r'\s+', '', s)
        # Supprimer/fusionner les points consécutifs accidentels (ex: '95..66' -> '95.66')
        s = re.sub(r'\.+', '.', s)
        return float(s)
    except Exception:
        return None
