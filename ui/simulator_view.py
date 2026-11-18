"""
Vue du Simulateur & Laboratoire Hydraulique Unitaire (CustomTkinter).
Permet de tester et vérifier interactivement chaque formule fondamentale :
- Allievi (Célérité d'onde)
- Saint-Venant (Échappement d'air subsonique / sonique)
- Strickler-Bernoulli (Casse franche unitaire)
- Vidange pondérée unitaire
"""

import customtkinter as ctk
import math
from core.catalog import PIPE_MATERIALS, STANDARD_DRAIN_DIAMETERS_MM
from core.catalogues_ceai_snh import (
    CATALOG_CEAI_SNH,
    CATALOG_CONFIG_LABELS,
    CATALOG_PAM_SNH,
    DEFAULT_AIR_CATALOG_CONFIG,
    recommander_equipement_air,
)
from core.hydraulic_models import (
    calculate_allievi_wave_speed,
    calculate_saint_venant_air_exhaust,
    calculate_strickler_rupture_flow,
    calculate_drain_dimensioning,
    format_hours_minutes
)


class SimulatorView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="⚡ Laboratoire de Calculs & Simulateurs Unitaires",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1F497D", "#70A1FF")
        )
        title.pack(anchor="w", padx=20, pady=(12, 4))

        sub = ctk.CTkLabel(
            header,
            text="Simulateur temps réel pour vérification ponctuelle des formules exactes corrigées",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        sub.pack(anchor="w", padx=20, pady=(0, 12))

        # Onglets de simulation
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=5)

        tab_allievi = self.tabview.add("⚡ Célérité Allievi")
        tab_sv = self.tabview.add("🌬️ Saint-Venant (Air)")
        tab_rupture = self.tabview.add("🌪️ Casse Franche (Ventouse)")
        tab_drain = self.tabview.add("💧 Vidange Unitaire")

        self._build_allievi_tab(tab_allievi)
        self._build_saint_venant_tab(tab_sv)
        self._build_rupture_tab(tab_rupture)
        self._build_drain_tab(tab_drain)

    # 1. TAB ALLIEVI
    def _build_allievi_tab(self, tab):
        grid = ctk.CTkFrame(tab, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=15, pady=10)
        grid.grid_columnconfigure((0, 1), weight=1)

        left = ctk.CTkFrame(grid, fg_color=("white", "#2C3E50"), corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)

        ctk.CTkLabel(left, text="Paramètres de la Conduite", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)

        # Matériau
        ctk.CTkLabel(left, text="Matériau :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        combo_mat = ctk.CTkComboBox(left, values=list(PIPE_MATERIALS.keys()))
        combo_mat.set("PRV (Polyester Renforcé Verre)")
        combo_mat.pack(fill="x", padx=15, pady=3)

        # Diamètre intérieur mm
        ctk.CTkLabel(left, text="Diamètre intérieur (mm) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_d = ctk.CTkEntry(left)
        e_d.insert(0, "2000")
        e_d.pack(fill="x", padx=15, pady=3)

        # Épaisseur mm
        ctk.CTkLabel(left, text="Épaisseur de paroi (mm) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_e = ctk.CTkEntry(left)
        e_e.insert(0, "35")
        e_e.pack(fill="x", padx=15, pady=3)

        # Module Young personnalisé
        ctk.CTkLabel(left, text="Module d'Young E (GPa) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_mod = ctk.CTkEntry(left)
        e_mod.insert(0, "20.0")
        e_mod.pack(fill="x", padx=15, pady=3)

        def on_mat_change(choice):
            m = PIPE_MATERIALS.get(choice)
            if m:
                e_mod.delete(0, "end")
                e_mod.insert(0, str(m["E_Pa"] / 1e9))

        combo_mat.configure(command=on_mat_change)

        # Résultat Droite
        right = ctk.CTkFrame(grid, fg_color=("white", "#2C3E50"), corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)

        ctk.CTkLabel(right, text="Résultat de la Célérité", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)

        res_speed_lbl = ctk.CTkLabel(right, text="a = --- m/s", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00A8FF")
        res_speed_lbl.pack(padx=15, pady=20)

        details_allievi_lbl = ctk.CTkLabel(right, text="", justify="left", font=ctk.CTkFont(family="Consolas", size=11))
        details_allievi_lbl.pack(anchor="w", padx=15, pady=5)

        def calc_allievi():
            try:
                d_m = float(e_d.get().replace(',', '.')) / 1000.0
                e_m = float(e_e.get().replace(',', '.')) / 1000.0
                e_young_pa = float(e_mod.get().replace(',', '.')) * 1e9

                a = calculate_allievi_wave_speed(d_inner_m=d_m, thickness_m=e_m, e_young_pa=e_young_pa)
                res_speed_lbl.configure(text=f"a = {a:.1f} m/s")

                term_water = 1.0 / 2.07e9
                term_pipe = d_m / (e_young_pa * e_m)
                ratio_pipe = term_pipe / (term_water + term_pipe) * 100.0

                details = (
                    f"• Formule : a = 1 / √[ ρ × ( 1/Keau + d/(E·e) ) ]\n"
                    f"• Compressibilité eau (1/Keau) : {term_water:.3e} Pa⁻¹\n"
                    f"• Déformabilité conduite : {term_pipe:.3e} Pa⁻¹ ({ratio_pipe:.1f}%)\n"
                    f"• Pression max coup de bélier pour ΔV=1 m/s : {1000.0*a*1.0/9810.0:.1f} mCE"
                )
                details_allievi_lbl.configure(text=details)
            except Exception as ex:
                res_speed_lbl.configure(text="Erreur")
                details_allievi_lbl.configure(text=str(ex))

        btn_calc = ctk.CTkButton(left, text="Calculer Célérité", fg_color="#0984E3", height=34, command=calc_allievi)
        btn_calc.pack(fill="x", padx=15, pady=15)
        calc_allievi()

    # 2. TAB SAINT-VENANT
    def _build_saint_venant_tab(self, tab):
        grid = ctk.CTkFrame(tab, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=15, pady=10)
        grid.grid_columnconfigure((0, 1), weight=1)

        left = ctk.CTkFrame(grid, fg_color=("white", "#2C3E50"), corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        ctk.CTkLabel(left, text="Orifice & Pression de la Poche", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)

        ctk.CTkLabel(left, text="Diamètre de l'orifice (mm) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_diam = ctk.CTkEntry(left)
        e_diam.insert(0, "50") # 50 mm
        e_diam.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left, text="Pression relative dans la conduite (bar) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_p_rel = ctk.CTkEntry(left)
        e_p_rel.insert(0, "2.0") # 2 bar rel
        e_p_rel.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left, text="Coefficient de décharge Cd :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_cd = ctk.CTkEntry(left)
        e_cd.insert(0, "0.65")
        e_cd.pack(fill="x", padx=15, pady=3)

        right = ctk.CTkFrame(grid, fg_color=("white", "#2C3E50"), corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        ctk.CTkLabel(right, text="Débit d'Échappement Évacué", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)

        res_q_lbl = ctk.CTkLabel(right, text="Q = --- m³/h", font=ctk.CTkFont(size=26, weight="bold"), text_color="#00D2D3")
        res_q_lbl.pack(padx=15, pady=15)

        res_regime_lbl = ctk.CTkLabel(right, text="Régime : ---", font=ctk.CTkFont(size=13, weight="bold"))
        res_regime_lbl.pack(padx=15, pady=5)

        details_sv_lbl = ctk.CTkLabel(right, text="", justify="left", font=ctk.CTkFont(family="Consolas", size=11))
        details_sv_lbl.pack(anchor="w", padx=15, pady=10)

        def calc_sv():
            try:
                diam_m = float(e_diam.get().replace(',', '.')) / 1000.0
                s_m2 = math.pi * (diam_m ** 2) / 4.0
                p_rel_bar = float(e_p_rel.get().replace(',', '.'))
                # 1 bar = 10.197 mCE
                p2_abs_mce = (p_rel_bar * 10.197) + 10.33
                cd = float(e_cd.get().replace(',', '.'))

                res = calculate_saint_venant_air_exhaust(
                    orifice_area_m2=s_m2,
                    p2_mce_abs=p2_abs_mce,
                    discharge_coeff_cd=cd
                )

                res_q_lbl.configure(text=f"Q = {res['q_air_m3h']:.1f} m³/h\n({res['q_air_m3s']:.3f} m³/s)")
                is_sonic = res["regime"] == "sonique"
                reg_txt = "🔴 Régime SONIQUE (Vitesse sonique au col)" if is_sonic else "🔵 Régime SUBSONIQUE"
                reg_col = "#FF7675" if is_sonic else "#74B9FF"
                res_regime_lbl.configure(text=reg_txt, text_color=reg_col)

                det = (
                    f"• Section orifice s : {s_m2*1e4:.2f} cm²\n"
                    f"• Pression P2 absolue : {p2_abs_mce:.2f} mCE ({p2_abs_mce/10.197:.2f} bar abs)\n"
                    f"• Pression critique P_crit : {res['p_critique_mce']:.2f} mCE abs (~0.92 bar rel)\n"
                    f"• Ratio de pression P1/P2 : {res['pressure_ratio']:.4f}\n"
                    f"• Formule appliquée : {'Q = 129·Cd·s (bloqué)' if is_sonic else 'Q = 499·Cd·s·(P1/P2)^0.714·√(1 - (P1/P2)^0.286)'}"
                )
                details_sv_lbl.configure(text=det)
            except Exception as ex:
                res_q_lbl.configure(text="Erreur")
                details_sv_lbl.configure(text=str(ex))

        btn_calc_sv = ctk.CTkButton(left, text="Calculer Échappement Air", fg_color="#00A8FF", height=34, command=calc_sv)
        btn_calc_sv.pack(fill="x", padx=15, pady=15)
        calc_sv()

    # 3. TAB CASSE FRANCHE
    def _build_rupture_tab(self, tab):
        grid = ctk.CTkFrame(tab, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=15, pady=10)
        grid.grid_columnconfigure((0, 1), weight=1)

        left = ctk.CTkFrame(grid, fg_color=("white", "#2C3E50"), corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        ctk.CTkLabel(left, text="Géométrie du Tronçon en Rupture", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)

        ctk.CTkLabel(left, text="Longueur du tronçon L (m) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_l = ctk.CTkEntry(left)
        e_l.insert(0, "850")
        e_l.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left, text="Dénivelée brute ΔZ (m) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_dz = ctk.CTkEntry(left)
        e_dz.insert(0, "13.93")
        e_dz.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left, text="Diamètre de la conduite D (m) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_d_pipe = ctk.CTkEntry(left)
        e_d_pipe.insert(0, "2.0")
        e_d_pipe.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left, text="Coefficient de Strickler Ks :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_ks = ctk.CTkEntry(left)
        e_ks.insert(0, "104.0")
        e_ks.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left, text="Base catalogue organes d'air :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        catalog_label_to_key = {
            CATALOG_CONFIG_LABELS[CATALOG_PAM_SNH]: CATALOG_PAM_SNH,
            CATALOG_CONFIG_LABELS[CATALOG_CEAI_SNH]: CATALOG_CEAI_SNH,
        }
        combo_catalog = ctk.CTkComboBox(left, values=list(catalog_label_to_key.keys()))
        combo_catalog.set(CATALOG_CONFIG_LABELS.get(DEFAULT_AIR_CATALOG_CONFIG, CATALOG_CONFIG_LABELS[CATALOG_CEAI_SNH]))
        combo_catalog.pack(fill="x", padx=15, pady=3)

        right = ctk.CTkFrame(grid, fg_color=("white", "#2C3E50"), corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        ctk.CTkLabel(right, text="Débit d'Air & Équipement Adéquat", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)

        res_q_air_lbl = ctk.CTkLabel(right, text="Qair = --- m³/s", font=ctk.CTkFont(size=26, weight="bold"), text_color="#E74C3C")
        res_q_air_lbl.pack(padx=15, pady=15)

        res_equip_lbl = ctk.CTkLabel(right, text="Équipement : ---", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2ECC71")
        res_equip_lbl.pack(padx=15, pady=5)

        details_rupt_lbl = ctk.CTkLabel(right, text="", justify="left", font=ctk.CTkFont(family="Consolas", size=11))
        details_rupt_lbl.pack(anchor="w", padx=15, pady=10)

        def calc_rupture():
            try:
                l_m = float(e_l.get().replace(',', '.'))
                dz = float(e_dz.get().replace(',', '.'))
                d_m = float(e_d_pipe.get().replace(',', '.'))
                ks = float(e_ks.get().replace(',', '.'))
                catalog_key = catalog_label_to_key.get(combo_catalog.get(), DEFAULT_AIR_CATALOG_CONFIG)

                res = calculate_strickler_rupture_flow(
                    d_inner_m=d_m,
                    length_m=l_m,
                    z_air_valve_m=dz,
                    z_drain_m=0.0,
                    delta_p_admiss_mce=3.0,
                    ks_strickler=ks
                )

                q_air = res["q_air_m3s"]
                res_q_air_lbl.configure(text=f"Qair = {q_air:.2f} m³/s\n({res['q_air_m3h']:,.0f} m³/h)")

                rec = recommander_equipement_air(
                    debit_m3s=q_air, dn_conduite_m=d_m, v_filling_ms=0.5, catalog_config=catalog_key
                )
                q_admis = rec.get("q_admis_m3s", rec.get("total_admission_flow_m3s", 0.0))
                res_equip_lbl.configure(
                    text=(
                        f"Recommandation ({rec.get('config_label', catalog_key)}) :\n"
                        f"{rec['equipment_str']}\n(Débit admis = {q_admis} m³/s)"
                    )
                )

                filling_ok = rec.get("is_compliant_filling")
                if catalog_key == CATALOG_CEAI_SNH:
                    filling_txt = "non vérifié (données évacuation non fournies)"
                else:
                    filling_txt = "OUI" if filling_ok else "NON"

                det = (
                    f"• Base catalogue : {rec.get('config_label', catalog_key)}\n"
                    f"• Dénivelée motrice H : {res['h_moteur_m']:.2f} m (ΔZ - 3.0 m)\n"
                    f"• Vitesse de l'eau v : {res['v_water_ms']:.2f} m/s\n"
                    f"• Taux de couverture : {rec.get('coverage_pct', 0)}%\n"
                    f"• Remplissage sécurisé à 0.5 m/s : {filling_txt}"
                )
                details_rupt_lbl.configure(text=det)
            except Exception as ex:
                res_q_air_lbl.configure(text="Erreur")
                details_rupt_lbl.configure(text=str(ex))

        btn_calc_rupt = ctk.CTkButton(left, text="Calculer Casse Franche", fg_color="#E67E22", height=34, command=calc_rupture)
        btn_calc_rupt.pack(fill="x", padx=15, pady=15)
        combo_catalog.configure(command=lambda _v: calc_rupture())
        calc_rupture()

    # 4. TAB VIDANGE UNITAIRE
    def _build_drain_tab(self, tab):
        grid = ctk.CTkFrame(tab, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=15, pady=10)
        grid.grid_columnconfigure((0, 1), weight=1)

        left = ctk.CTkFrame(grid, fg_color=("white", "#2C3E50"), corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        ctk.CTkLabel(left, text="Paramètres de Vidange", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)

        ctk.CTkLabel(left, text="Longueur totale à vidanger L (m) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_l_tot = ctk.CTkEntry(left)
        e_l_tot.insert(0, "1500")
        e_l_tot.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left, text="Hauteur moyenne hmoy (m) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_hmoy = ctk.CTkEntry(left)
        e_hmoy.insert(0, "2.5")
        e_hmoy.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left, text="Diamètre conduite principale D (m) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_d_cond = ctk.CTkEntry(left)
        e_d_cond.insert(0, "2.0")
        e_d_cond.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(left, text="Temps objectif de vidange (heures) :", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(5, 0))
        e_t_target = ctk.CTkEntry(left)
        e_t_target.insert(0, "2.0")
        e_t_target.pack(fill="x", padx=15, pady=3)

        right = ctk.CTkFrame(grid, fg_color=("white", "#2C3E50"), corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        ctk.CTkLabel(right, text="Diamètres & Durées Réelles", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=10)

        res_d_exact_lbl = ctk.CTkLabel(right, text="d exact = --- mm", font=ctk.CTkFont(size=26, weight="bold"), text_color="#1ABC9C")
        res_d_exact_lbl.pack(padx=15, pady=15)

        table_times_lbl = ctk.CTkLabel(right, text="", justify="left", font=ctk.CTkFont(family="Consolas", size=11))
        table_times_lbl.pack(anchor="w", padx=15, pady=10)

        def calc_drain():
            try:
                l_m = float(e_l_tot.get().replace(',', '.'))
                h_m = float(e_hmoy.get().replace(',', '.'))
                d_m = float(e_d_cond.get().replace(',', '.'))
                t_h = float(e_t_target.get().replace(',', '.'))

                res = calculate_drain_dimensioning(
                    dn_pipe_m=d_m,
                    l_upstream_m=l_m,
                    h_upstream_m=h_m * 2.0, # Pour avoir hmoy = h_m
                    target_time_hours=t_h
                )

                d_exact = res["d_exact_mm"]
                dn_rec = res["dn_recommended_mm"]
                res_d_exact_lbl.configure(text=f"d exact = {d_exact:.1f} mm\n(DN recommandé = {dn_rec} mm)")

                # Simulation durées selon DN standard
                test_dns = [200, 250, 300, 350, 400, 450, 500, 600]
                lines = ["Temps réel de vidange selon le DN normalisé :"]
                for test_dn in test_dns:
                    t_real = t_h * ((d_exact / float(test_dn)) ** 2)
                    t_str = format_hours_minutes(t_real)
                    ok_str = "✅ CONFORME" if t_real <= t_h + 0.05 else "❌ TROP LONG"
                    lines.append(f"• DN {test_dn:3d} mm : {t_str:5s} ({t_real:4.2f} h) — {ok_str}")

                table_times_lbl.configure(text="\n".join(lines))
            except Exception as ex:
                res_d_exact_lbl.configure(text="Erreur")
                table_times_lbl.configure(text=str(ex))

        btn_calc_dr = ctk.CTkButton(left, text="Calculer Diamètre Vidange", fg_color="#16A085", height=34, command=calc_drain)
        btn_calc_dr.pack(fill="x", padx=15, pady=15)
        calc_drain()
