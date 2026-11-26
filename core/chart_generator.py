"""
Générateur de graphiques et profils hydrauliques pour MK-St_Venant.
Utilise matplotlib avec un rendu professionnel (style moderne, légendes soignées, exports PNG/PDF).
"""

from typing import Optional, List, Tuple
import matplotlib
matplotlib.use('Agg') # Mode non-interactif sécurisé pour threading/GUI
import matplotlib.pyplot as plt
import numpy as np

from core.project_data import HydraulicProject


def plot_longitudinal_profile(project: HydraulicProject, filepath: Optional[str] = None) -> plt.Figure:
    """
    Trace le profil en long de l'adduction avec positionnement des ventouses et des vidanges.
    """
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FAFAFB')

    # Rassembler tous les points géométriques pour tracer le profil du terrain/conduite
    points = []
    for v in project.air_valves:
        points.append((v.pm, v.z_terrain, 'valve', v))
    for d in project.drains:
        points.append((d.pm, d.z_terrain, 'drain', d))

    # Trier par PM croissant
    points.sort(key=lambda x: x[0])

    if points:
        pms = [p[0] for p in points]
        cotes = [p[1] for p in points]

        # Ligne de conduite / terrain
        ax.plot(pms, cotes, color='#2F3542', linewidth=2.0, linestyle='-', label="Profil conduite / terrain", zorder=2)
        ax.fill_between(pms, cotes, min(cotes) - 10, color='#70A1FF', alpha=0.15, zorder=1)

        # Points Hauts (Ventouses)
        valves_pm = [v.pm for v in project.air_valves]
        valves_z = [v.z_terrain for v in project.air_valves]
        valves_colors = ['#2ED573' if v.is_compliant else '#FF4757' for v in project.air_valves]

        ax.scatter(valves_pm, valves_z, color=valves_colors, s=110, edgecolor='#1E272E', linewidth=1.5,
                   marker='^', label="Points Hauts (Ventouses)", zorder=4)

        for v in project.air_valves:
            ax.annotate(
                f"PM {v.pm:.0f}\n{v.z_terrain:.1f} m\nQ={v.q_air_max_m3s:.1f}",
                xy=(v.pm, v.z_terrain),
                xytext=(0, 16),
                textcoords="offset points",
                ha='center', fontsize=7.5, fontweight='bold', color='#1E272E',
                bbox=dict(boxstyle="round,pad=0.25", fc="#FFFFFF", ec="#CED6E0", alpha=0.9)
            )

        # Points Bas (Vidanges)
        drains_pm = [d.pm for d in project.drains]
        drains_z = [d.z_terrain for d in project.drains]
        drains_colors = ['#1E90FF' if d.is_compliant else '#FF6B81' for d in project.drains]

        ax.scatter(drains_pm, drains_z, color=drains_colors, s=110, edgecolor='#1E272E', linewidth=1.5,
                   marker='v', label="Points Bas (Vidanges)", zorder=4)

        for d in project.drains:
            ax.annotate(
                f"PM {d.pm:.0f}\n{d.z_terrain:.1f} m\nDN {d.dn_retained_mm}\n({d.t_real_str})",
                xy=(d.pm, d.z_terrain),
                xytext=(0, -32),
                textcoords="offset points",
                ha='center', fontsize=7.5, fontweight='bold', color='#2F3542',
                bbox=dict(boxstyle="round,pad=0.25", fc="#F1F2F6", ec="#CED6E0", alpha=0.9)
            )

    ax.set_title(f"PROFIL EN LONG HYDRAULIQUE — {project.name.upper()}", fontsize=13, fontweight='bold', color='#1E272E', pad=15)
    ax.set_xlabel("Point Métrique - PM (m)", fontsize=10, fontweight='bold', color='#2F3542')
    ax.set_ylabel("Cote Altimétrique Projet (m)", fontsize=10, fontweight='bold', color='#2F3542')
    ax.grid(True, linestyle='--', alpha=0.5, color='#CED6E0')
    ax.legend(loc='upper right', frameon=True, facecolor='#FFFFFF', edgecolor='#CED6E0', fontsize=9)

    plt.tight_layout()
    if filepath:
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
    return fig


def plot_air_valves_comparison(project: HydraulicProject, filepath: Optional[str] = None) -> plt.Figure:
    """
    Diagramme à barres comparant le débit d'air requis (casse franche) vs débit admis équipé.
    """
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FAFAFB')

    labels = [f"PM {v.pm:.0f}" for v in project.air_valves]
    q_req = [v.q_air_max_m3s for v in project.air_valves]
    q_adm = [v.q_admis_m3s for v in project.air_valves]

    x = np.arange(len(labels))
    width = 0.38

    rects1 = ax.bar(x - width/2, q_req, width, label='Débit d\'air requis Qmax (m³/s)', color='#FF7675', edgecolor='#D63031')
    rects2 = ax.bar(x + width/2, q_adm, width, label='Débit d\'air équipé admis (m³/s)', color='#55EFC4', edgecolor='#00B894')

    ax.set_ylabel("Débit d'air (m³/s)", fontsize=10, fontweight='bold')
    ax.set_title("VÉRIFICATION DES DÉBITS D'AIR EN CASSE FRANCHE (POINTS HAUTS)", fontsize=12, fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=8.5)
    ax.legend(frameon=True, facecolor='#FFFFFF', edgecolor='#CED6E0')
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    # Valeurs sur les barres
    for rect in rects1:
        h = rect.get_height()
        if h > 0:
            ax.annotate(f"{h:.1f}", xy=(rect.get_x() + rect.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points", ha='center', fontsize=7.5, fontweight='bold')
    for rect in rects2:
        h = rect.get_height()
        if h > 0:
            ax.annotate(f"{h:.1f}", xy=(rect.get_x() + rect.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points", ha='center', fontsize=7.5, fontweight='bold')

    plt.tight_layout()
    if filepath:
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
    return fig


def plot_drain_times_comparison(project: HydraulicProject, filepath: Optional[str] = None) -> plt.Figure:
    """
    Diagramme comparant les temps réels de vidange avec le temps cible de 2 heures.
    """
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FAFAFB')

    labels = [f"PM {d.pm:.0f}\n(DN {d.dn_retained_mm})" for d in project.drains]
    times = [d.t_real_hours for d in project.drains]
    colors = ['#00B894' if d.is_compliant else '#D63031' for d in project.drains]

    x = np.arange(len(labels))
    bars = ax.bar(x, times, width=0.5, color=colors, edgecolor='#2D3436', linewidth=1.0)

    # Ligne du temps cible saisi (2 h par défaut)
    ax.axhline(y=project.target_drain_time_hours, color='#E17055', linestyle='--', linewidth=2.0,
               label=f"Objectif de vidange = {project.target_drain_time_hours:.1f} heures")

    ax.set_ylabel("Temps de vidange réel (heures)", fontsize=10, fontweight='bold')
    ax.set_title("TEMPS RÉELS DE VIDANGE DES TRONÇONS (POINTS BAS)", fontsize=12, fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.legend(frameon=True, facecolor='#FFFFFF', edgecolor='#CED6E0')
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for bar, d in zip(bars, project.drains):
        h = bar.get_height()
        ax.annotate(f"{d.t_real_str}",
                    xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 4), textcoords="offset points", ha='center', fontsize=8, fontweight='bold')

    plt.tight_layout()
    if filepath:
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
    return fig


def plot_saint_venant_law(filepath: Optional[str] = None) -> plt.Figure:
    """
    Trace la courbe de débit d'échappement d'air selon la loi de Saint-Venant (subsonique vs sonique).
    """
    from core.hydraulic_models import calculate_saint_venant_air_exhaust

    p2_vals = np.linspace(10.33, 40.0, 150)
    q_vals = []
    regimes = []
    s_ref = 0.001 # 10 cm2 orifice

    for p in p2_vals:
        res = calculate_saint_venant_air_exhaust(orifice_area_m2=s_ref, p2_mce_abs=p)
        q_vals.append(res["q_air_m3h"])
        regimes.append(res["regime"])

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FAFAFB')

    ax.plot(p2_vals, q_vals, color='#0984E3', linewidth=2.5, label="Débit d'air évacué Q (m³/h)")
    ax.axvline(x=19.55, color='#D63031', linestyle=':', linewidth=2.0, label="Pression critique = 19.55 mCE abs (Régime sonique)")

    # Zones subsonique et sonique
    ax.axvspan(10.33, 19.55, color='#74B9FF', alpha=0.15, label="Régime subsonique")
    ax.axvspan(19.55, 40.0, color='#FF7675', alpha=0.15, label="Régime sonique (bloqué)")

    ax.set_xlabel("Pression absolue dans la poche d'air P2 (mCE)", fontsize=10, fontweight='bold')
    ax.set_ylabel("Débit d'air à travers orifice s=10 cm² (m³/h)", fontsize=10, fontweight='bold')
    ax.set_title("LOI D'ÉCHAPPEMENT DE SAINT-VENANT (AIR COMPRESSIBLE)", fontsize=11, fontweight='bold', pad=12)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(frameon=True, facecolor='#FFFFFF', edgecolor='#CED6E0', fontsize=8.5)

    plt.tight_layout()
    if filepath:
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
    return fig
