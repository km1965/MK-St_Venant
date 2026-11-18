"""
Générateur de rapport technique et d'expertise au format Word (.docx).
Génère un document d'ingénierie complet et professionnel avec justifications,
tableaux récapitulatifs, diagnostics détaillés et graphiques insérés.
Toujours robuste : génère le rapport même en présence d'anomalies de calcul avec trace d'audit.
"""

import os
from typing import Optional, Dict, Any
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from core.project_data import HydraulicProject
from core.catalogues_ceai_snh import CATALOG_CONFIG_LABELS, DEFAULT_AIR_CATALOG_CONFIG


# Couleurs corporate
COLOR_NAVY = RGBColor(0x1F, 0x49, 0x7D)
COLOR_TEAL = RGBColor(0x00, 0x80, 0x80)
COLOR_DARK = RGBColor(0x2F, 0x35, 0x42)
COLOR_RED = RGBColor(0xC0, 0x00, 0x00)
COLOR_GREEN = RGBColor(0x00, 0x80, 0x00)


def set_cell_background(cell, hex_color: str):
    """Applique une couleur d'arrière-plan hexadécimale à une cellule de tableau Word."""
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Définit les marges internes d'une cellule."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def generate_word_report(
    project: HydraulicProject,
    output_docx_path: str,
    include_charts: bool = True,
    chart_dir: Optional[str] = None
) -> str:
    """
    Génère un rapport Word officiel (.docx) complet et justifié.
    Garantit la génération de rapports même en cas d'erreur ou données incomplètes.
    """
    project.calculate_all()
    stats = project.get_summary_stats()

    doc = docx.Document()

    # Configuration des marges
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # 1. TITRE PRINCIPAL ET EN-TÊTE
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("RAPPORT D'EXPERTISE TECHNIQUE ET HYDRAULIQUE")
    run_title.font.name = "Segoe UI"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = COLOR_NAVY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run(f"DIMENSIONNEMENT ET AUDIT DES ORGANES DE SÉCURITÉ : VENTOUSES ET VIDANGES\n{project.name.upper()}")
    run_sub.font.name = "Segoe UI"
    run_sub.font.size = Pt(13)
    run_sub.font.bold = True
    run_sub.font.color.rgb = COLOR_TEAL

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_meta = p_meta.add_run(f"Document conforme aux lois d'écoulement compressible (Saint-Venant), d'Allievi et de Strickler-Bernoulli\nApplication MK-St_Venant v1.0")
    run_meta.font.name = "Segoe UI"
    run_meta.font.size = Pt(9.5)
    run_meta.font.italic = True
    run_meta.font.color.rgb = RGBColor(120, 120, 120)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # 2. SYNTHÈSE DES PARAMÈTRES ET DU PROJET
    h1 = doc.add_heading("1. Synthèse du Projet et Hypothèses Générales", level=1)
    h1.style.font.color.rgb = COLOR_NAVY

    p_intro = doc.add_paragraph(
        f"La présente étude hydraulique a pour objet le contrôle, la vérification et le dimensionnement optimal "
        f"des ouvrages de vidange des points bas et des ventouses d'aération/purge des points hauts pour l'adduction "
        f"« {project.name} ».\n"
        f"Le tracé est équipé d'une conduite principale en {project.pipe_material} de diamètre nominal DN {int(project.dn_main_conduite_m*1000)} mm "
        f"(épaisseur {project.pipe_thickness_m*1000:.1f} mm), transitant un débit d'eau nominal de {project.q_nominal_water_m3s} m³/s."
    )
    p_intro.style.font.name = "Segoe UI"
    p_intro.style.font.size = Pt(10)

    # Tableau des hypothèses
    catalog_label = CATALOG_CONFIG_LABELS.get(
        getattr(project, "air_catalog_config", DEFAULT_AIR_CATALOG_CONFIG),
        str(getattr(project, "air_catalog_config", DEFAULT_AIR_CATALOG_CONFIG)),
    )

    params_rows = [
        ("Paramètre Hydraulique", "Valeur Retenue", "Justification & Référence Normative"),
        ("Base catalogue organes d'air", catalog_label, "Catalogue sélectionné pour le dimensionnement (référence CEAI/SNH ou PAM/SNH existant)"),
        ("Diamètre Conduite Principale", f"DN {int(project.dn_main_conduite_m*1000)} mm", "Profil en long de l'adduction"),
        ("Matériau & Coefficient Strickler", f"{project.pipe_material} (Ks = {project.ks_strickler})", "Pertes de charge linéaires régulières"),
        ("Célérité d'Allievi calculée", f"a = {stats['wave_speed_allievi_ms']} m/s", "Formule exacte avec compressibilité de l'eau (2.07 GPa)"),
        ("Vitesse de remplissage limite", f"V = {project.v_filling_ms} m/s", "Règle de l'art pour éviter coups de bélier d'air"),
        ("Dépression admissible maximale", f"ΔP = {project.delta_p_admiss_mce} mCE", "Seuil de non-écrasement des tuyaux PRV"),
        ("Temps objectif de vidange des points bas", f"t = {project.target_drain_time_hours} heures", "Délai contractuel de maintenance d'exploitation")
    ]

    tbl_params = doc.add_table(rows=len(params_rows), cols=3)
    tbl_params.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_params.autofit = False

    for r_idx, row_data in enumerate(params_rows):
        row = tbl_params.rows[r_idx]
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.text = str(val)
            set_cell_margins(cell, 80, 80, 100, 100)
            p = cell.paragraphs[0]
            p.runs[0].font.name = "Segoe UI"
            if r_idx == 0:
                set_cell_background(cell, "1F497D")
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
                p.runs[0].font.size = Pt(9.5)
            else:
                set_cell_background(cell, "F2F5F8" if r_idx % 2 == 1 else "FFFFFF")
                p.runs[0].font.size = Pt(9)
                if c_idx == 0:
                    p.runs[0].font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 3. PRINCIPES ET FORMULES HYDRAULIQUES APPLIQUÉES
    h2 = doc.add_heading("2. Principes et Formules Hydrauliques Appliquées", level=1)
    h2.style.font.color.rgb = COLOR_NAVY

    doc.add_paragraph(
        "Les calculs sont réalisés selon les formulations hydrauliques et thermodynamiques "
        "suivantes, appliquées aux paramètres du projet en cours :"
    ).style.font.name = "Segoe UI"

    dn_mm = int(project.dn_main_conduite_m * 1000)
    import math
    q_fill_m3h = (
        project.v_filling_ms * (math.pi * (project.dn_main_conduite_m ** 2) / 4.0) * 3600.0
        if project.dn_main_conduite_m > 0
        else 0.0
    )

    audit_points = [
        ("Vidange des points bas :",
         f"Temps objectif t = {project.target_drain_time_hours:g} h. Le diamètre théorique est obtenu par "
         "continuité et écoulement par orifice : d = √(4·V / (π·K·√(2·g·hmoy)·t))·1000. "
         "La hauteur motrice est la hauteur moyenne pondérée des deux branches "
         "hmoy = [Lam·(Ham/2) + Lav·(Hav/2)] / (Lam + Lav). Le temps réel est recalculé selon le DN retenu."),

        ("Célérité des ondes d'Allievi :",
         f"Célérité calculée : a = {stats['wave_speed_allievi_ms']} m/s "
         f"(DN {dn_mm} mm, {project.pipe_material}, e = {project.pipe_thickness_m*1000:.1f} mm). "
         "Formule : a = 1 / √[ ρ · (1/Keau + D/(E·e)) ] avec Keau = 2,07 GPa."),

        ("Échappement d'air (Saint-Venant) :",
         "Écoulement compressible subsonique / sonique à travers orifice, transition à "
         "P_critique = 19,55 mCE abs. "
         "Subsonique : Q = 499·Cd·s·(P1/P2)^0,714·√(1 - (P1/P2)^0,286) ; "
         "Sonique : Q = 129·Cd·s."),

        ("Admission d'air en casse franche (Strickler-Bernoulli) :",
         f"Dépression admissible ΔP = {project.delta_p_admiss_mce:g} mCE. "
         "Hauteur motrice H = max(0 ; Z_ventouse - ΔP - Z_vidange). "
         "Le débit gravitationnel (débit d'air requis) est calculé avec pertes de charge de Strickler "
         "et pertes singulières sur chaque branche amont/aval ; le Qair requis est le maximum des deux branches."),

        ("Remplissage de la conduite :",
         f"À V = {project.v_filling_ms:g} m/s sur DN {dn_mm} mm, le débit d'air refoulé est d'environ "
         f"{q_fill_m3h:,.0f} m³/h. ".replace(",", " ") +
         "Les équipements sont dimensionnés selon la base catalogue sélectionnée "
         f"({catalog_label}) pour couvrir les besoins d'admission en casse franche (et les critères associés).")
    ]

    for title_run, text_run in audit_points:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.2)
        r1 = p.add_run(f"• {title_run} ")
        r1.font.name = "Segoe UI"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = COLOR_DARK

        r2 = p.add_run(text_run)
        r2.font.name = "Segoe UI"
        r2.font.size = Pt(9)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 4. TABLEAU DES VENTOUSES (POINTS HAUTS)
    h3 = doc.add_heading("3. Dimensionnement et Vérification des Points Hauts (Ventouses)", level=1)
    h3.style.font.color.rgb = COLOR_NAVY

    doc.add_paragraph(
        f"L'analyse porte sur les {stats['total_air_valves']} points hauts de l'adduction. "
        f"Chaque équipement est dimensionné pour satisfaire simultanément aux 3 fonctions : "
        f"(1) Purge des micro-bulles sous pression de service, (2) Évacuation d'air grand débit au remplissage, "
        f"et (3) Admission d'air d'urgence lors d'une casse franche."
    ).style.font.name = "Segoe UI"

    tbl_valves = doc.add_table(rows=len(project.air_valves) + 1, cols=7)
    tbl_valves.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_valves.autofit = False

    valves_headers = [
        "PM (m)", "DN (m)", "Qair Amont (m³/s)", "Qair Aval (m³/s)",
        "Qair Max Requis (m³/s)", "Équipement Recommandé", "Q Admis (m³/s)"
    ]

    for c_idx, h in enumerate(valves_headers):
        cell = tbl_valves.rows[0].cells[c_idx]
        cell.text = h
        set_cell_background(cell, "1F497D")
        set_cell_margins(cell, 80, 80, 80, 80)
        p = cell.paragraphs[0]
        p.runs[0].font.name = "Segoe UI"
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p.runs[0].font.size = Pt(8.5)

    for r_idx, v in enumerate(project.air_valves, 1):
        row = tbl_valves.rows[r_idx]
        vals = [
            f"{v.pm:,.2f}", f"{v.dn_conduite_m:.1f}",
            f"{v.q_air_amont_m3s:.2f}", f"{v.q_air_aval_m3s:.2f}",
            f"{v.q_air_max_m3s:.2f}", v.recommended_equipment, f"{v.q_admis_m3s:.2f}"
        ]
        for c_idx, val in enumerate(vals):
            cell = row.cells[c_idx]
            cell.text = str(val)
            set_cell_margins(cell, 60, 60, 80, 80)
            set_cell_background(cell, "F2F5F8" if r_idx % 2 == 1 else "FFFFFF")
            p = cell.paragraphs[0]
            p.runs[0].font.name = "Segoe UI"
            p.runs[0].font.size = Pt(8.5)
            if c_idx in [0, 1, 2, 3, 4, 6]:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if c_idx == 4:
                p.runs[0].font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 5. TABLEAU DES VIDANGES (POINTS BAS)
    h4 = doc.add_heading("4. Dimensionnement et Vérification des Points Bas (Vidanges)", level=1)
    h4.style.font.color.rgb = COLOR_NAVY

    doc.add_paragraph(
        f"L'analyse porte sur les {stats['total_drains']} points bas de l'adduction. "
        f"Le tableau ci-dessous indique les diamètres théoriques pour vidanger en "
        f"{project.target_drain_time_hours:g} heure(s), les DN normalisés recommandés, "
        f"le DN retenu et le temps réel de vidange correspondant :"
    ).style.font.name = "Segoe UI"

    tbl_drains = doc.add_table(rows=len(project.drains) + 1, cols=7)
    tbl_drains.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_drains.autofit = False

    drains_headers = [
        "PM (m)", "DN Conduite (m)", "L Totale (m)", "hmoy (m)",
        "d exact 2h (mm)", "DN Recommandé (mm)", "Temps avec DN 400"
    ]

    for c_idx, h in enumerate(drains_headers):
        cell = tbl_drains.rows[0].cells[c_idx]
        cell.text = h
        set_cell_background(cell, "008080")
        set_cell_margins(cell, 80, 80, 80, 80)
        p = cell.paragraphs[0]
        p.runs[0].font.name = "Segoe UI"
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p.runs[0].font.size = Pt(8.5)

    for r_idx, d in enumerate(project.drains, 1):
        row = tbl_drains.rows[r_idx]
        vals = [
            f"{d.pm:,.2f}", f"{d.dn_conduite_m:.1f}", f"{d.l_total_m:,.2f}",
            f"{d.h_moy_m:.2f}", f"{d.d_exact_mm:.1f}", f"DN {d.dn_recommended_mm}",
            f"{d.t_real_str} ({'Conforme' if d.is_compliant else 'Alerte > 2h'})"
        ]
        for c_idx, val in enumerate(vals):
            cell = row.cells[c_idx]
            cell.text = str(val)
            set_cell_margins(cell, 60, 60, 80, 80)
            set_cell_background(cell, "F2F5F8" if r_idx % 2 == 1 else "FFFFFF")
            p = cell.paragraphs[0]
            p.runs[0].font.name = "Segoe UI"
            p.runs[0].font.size = Pt(8.5)
            if c_idx in [0, 1, 2, 3, 4]:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if c_idx == 6:
                if not d.is_compliant:
                    set_cell_background(cell, "FCE4D6")
                    p.runs[0].font.color.rgb = COLOR_RED
                    p.runs[0].font.bold = True
                else:
                    p.runs[0].font.color.rgb = COLOR_GREEN

    doc.add_paragraph().paragraph_format.space_after = Pt(15)

    # 6. INSERTION DES GRAPHIQUES SI DISPONIBLES
    if include_charts:
        h5 = doc.add_heading("5. Profils et Analyses Graphiques", level=1)
        h5.style.font.color.rgb = COLOR_NAVY

        # Génération temporaire des graphiques si nécessaire
        import tempfile
        from core.chart_generator import (
            plot_longitudinal_profile,
            plot_air_valves_comparison,
            plot_drain_times_comparison
        )

        target_dir = chart_dir if chart_dir and os.path.exists(chart_dir) else tempfile.gettempdir()

        p_prof = os.path.join(target_dir, "profil_long.png")
        p_valves = os.path.join(target_dir, "debits_air.png")
        p_drains = os.path.join(target_dir, "temps_vidange.png")

        try:
            plot_longitudinal_profile(project, p_prof)
            doc.add_paragraph("Figure 1 : Profil en long hydraulique et localisation des organes").style.font.name = "Segoe UI"
            doc.add_picture(p_prof, width=Inches(6.8))
        except Exception as e:
            doc.add_paragraph(f"[Graphique profil non inséré : {e}]")

        try:
            plot_air_valves_comparison(project, p_valves)
            doc.add_paragraph("Figure 2 : Comparaison Débits d'air requis vs Débits équipés admis").style.font.name = "Segoe UI"
            doc.add_picture(p_valves, width=Inches(6.5))
        except Exception as e:
            doc.add_paragraph(f"[Graphique ventouses non inséré : {e}]")

        try:
            plot_drain_times_comparison(project, p_drains)
            doc.add_paragraph("Figure 3 : Temps réels de vidange des points bas vs objectif 2 heures").style.font.name = "Segoe UI"
            doc.add_picture(p_drains, width=Inches(6.5))
        except Exception as e:
            doc.add_paragraph(f"[Graphique vidanges non inséré : {e}]")

    # 7. CONCLUSIONS ET RECOMMANDATIONS D'EXPLOITATION
    h6 = doc.add_heading("6. Recommandations et Prescriptions Techniques", level=1)
    h6.style.font.color.rgb = COLOR_NAVY

    recomms: list[str] = []

    # Vidanges non conformes -> recommandations dynamiques
    drains_nc = [d for d in project.drains if not d.is_compliant]
    if drains_nc:
        details = ", ".join(
            f"PM {d.pm:,.2f} (DN retenu {d.dn_retained_mm} mm → DN recommandé {d.dn_recommended_mm} mm, t réel {d.t_real_str})"
            for d in drains_nc
        )
        recomms.append(
            f"Vidanges à adapter pour respecter l'objectif de {project.target_drain_time_hours:g} h : {details}."
        )
    else:
        recomms.append(
            f"Vidanges : l'ensemble des points bas vérifiés respecte l'objectif de vidange de {project.target_drain_time_hours:g} h "
            "avec les DN retenus."
        )

    # Ventouses non conformes -> recommandations dynamiques
    valves_nc = [v for v in project.air_valves if not v.is_compliant]
    if valves_nc:
        details_v = ", ".join(
            f"PM {v.pm:,.2f} (Qmax {v.q_air_max_m3s:.2f} m³/s, équipé/recommandé : {v.recommended_equipment}, admis {v.q_admis_m3s:.2f} m³/s)"
            for v in valves_nc
        )
        recomms.append(
            f"Points hauts à compléter ou à ajuster : {details_v}. Vérifier la couverture admission (casse franche) "
            "et, selon la base catalogue, la capacité d'évacuation au remplissage."
        )
    else:
        recomms.append(
            "Points hauts : les équipements recommandés couvrent les débits d'air requis selon la base catalogue sélectionnée "
            "(admission en casse franche et critères associés)."
        )

    # Recommandations générales
    recomms.extend([
        "Appliquer la base catalogue d'organes d'air sélectionnée dans le projet et conserver la traçabilité "
        f"des capacités ({catalog_label}) dans les notes de calcul et bordereaux.",
        "Prévoir, selon les équipements retenus, les dispositifs de limitation des chocs de refermeture (anti-bélier / amortissement) "
        "et vérifier les conditions d'exploitation (vitesse de remplissage, isolement, accès maintenance).",
        "Valider les cotes, longueurs de tronçons et raccordements topologiques (amont/aval) avant exécution, "
        "car ils conditionnent directement les débits d'air et les temps de vidange."
    ])

    for rec in recomms:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.2)
        r = p.add_run(f"✔ {rec}")
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.5)

    doc.save(output_docx_path)
    return output_docx_path
