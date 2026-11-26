"""
Vue Tableau de bord & Paramètres généraux du projet (CustomTkinter).
Affiche les KPIs clés, les paramètres de conduite et les alertes globales.
"""

import customtkinter as ctk
from typing import Callable
from core.project_data import HydraulicProject
from core.catalog import PIPE_MATERIALS
from core.catalogues_ceai_snh import (
    CATALOG_CEAI_SNH,
    CATALOG_CONFIG_LABELS,
)
from core.hydraulic_models import drain_formula_coefficient


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, project: HydraulicProject, on_project_updated: Callable):
        super().__init__(parent, fg_color="transparent")
        self.project = project
        self.on_project_updated = on_project_updated

        self._build_ui()

    def _build_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        self.title_lbl = ctk.CTkLabel(
            header_frame,
            text=f"📊 Tableau de Bord Hydraulique — {self.project.name}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_lbl.pack(anchor="w", padx=20, pady=(15, 5))

        self.desc_lbl = ctk.CTkLabel(
            header_frame,
            text=self.project.description,
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        self.desc_lbl.pack(anchor="w", padx=20, pady=(0, 15))

        # KPI Cards Frame
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=15, pady=5)
        self.kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        self._render_kpi_cards()

        # Split frame: Paramètres (gauche) & Audit / Diagnostics (droite)
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=15, pady=10)
        main_content.grid_columnconfigure((0, 1), weight=1, uniform="content")
        main_content.grid_rowconfigure(0, weight=1)

        # 1. PARAMÈTRES DU PROJET (Cadre Gauche)
        params_box = ctk.CTkFrame(main_content, fg_color=("white", "#1E272E"), corner_radius=10)
        params_box.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        p_title = ctk.CTkLabel(
            params_box,
            text="⚙️ Paramètres Hydrauliques Généraux",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#1F497D", "#70A1FF")
        )
        p_title.pack(anchor="w", padx=20, pady=(15, 10))

        scroll_params = ctk.CTkScrollableFrame(params_box, fg_color="transparent")
        scroll_params.pack(fill="both", expand=True, padx=15, pady=5)

        # Champs de formulaire
        self.entry_dn = self._add_form_row(scroll_params, "Diamètre principal conduite (m) :", str(self.project.dn_main_conduite_m))
        self.combo_mat = self._add_combo_row(scroll_params, "Matériau de la conduite :", list(PIPE_MATERIALS.keys()), self.project.pipe_material)
        self._catalog_label_to_key = {
            label: key for key, label in CATALOG_CONFIG_LABELS.items()
        }
        catalog_labels = list(self._catalog_label_to_key.keys())
        current_catalog_label = CATALOG_CONFIG_LABELS.get(
            self.project.air_catalog_config, CATALOG_CONFIG_LABELS[CATALOG_CEAI_SNH]
        )
        self.combo_air_catalog = self._add_combo_row(
            scroll_params,
            "Base catalogue organes d'air :",
            catalog_labels,
            current_catalog_label,
        )
        self.entry_thick = self._add_form_row(scroll_params, "Épaisseur de paroi (mm) :", str(self.project.pipe_thickness_m * 1000.0))
        self.entry_ks = self._add_form_row(scroll_params, "Coefficient de Strickler Ks :", str(self.project.ks_strickler))
        self.entry_v_fill = self._add_form_row(scroll_params, "Vitesse de remplissage (m/s) :", str(self.project.v_filling_ms))
        self.entry_dp = self._add_form_row(scroll_params, "Dépression admissible ΔP (mCE) :", str(self.project.delta_p_admiss_mce))
        self.entry_q_nom = self._add_form_row(scroll_params, "Débit nominal en service (m³/s) :", str(self.project.q_nominal_water_m3s))
        self.entry_t_drain = self._add_form_row(scroll_params, "Temps cible vidange (heures) :", str(self.project.target_drain_time_hours))
        self.entry_k_drain = self._add_form_row(scroll_params, "Coeff. débit vanne vidange K :", str(self.project.drain_discharge_k))

        btn_apply = ctk.CTkButton(
            params_box,
            text="💾 Enregistrer et Recalculer le Projet",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#00A8FF",
            hover_color="#0097E6",
            height=38,
            command=self._apply_parameters
        )
        btn_apply.pack(fill="x", padx=20, pady=(10, 15))

        # 2. AUDIT TECHNIQUE & CONFORMITÉ (Cadre Droite)
        audit_box = ctk.CTkFrame(main_content, fg_color=("white", "#1E272E"), corner_radius=10)
        audit_box.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)

        a_title = ctk.CTkLabel(
            audit_box,
            text="📑 Synthèse d'Audit & Règles de Calcul",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#008080", "#00D2D3")
        )
        a_title.pack(anchor="w", padx=20, pady=(15, 10))

        scroll_audit = ctk.CTkScrollableFrame(audit_box, fg_color="transparent")
        scroll_audit.pack(fill="both", expand=True, padx=15, pady=5)

        self.audit_lbl = ctk.CTkLabel(
            scroll_audit,
            text=self._audit_text(),
            font=ctk.CTkFont(family="Consolas", size=11),
            justify="left",
            text_color=("gray20", "gray85")
        )
        self.audit_lbl.pack(anchor="w", padx=10, pady=5)

    def _audit_text(self) -> str:
        """Synthèse des formules, avec coefficient de vidange lié au temps cible."""
        target_h = float(getattr(self.project, "target_drain_time_hours", 2.0) or 2.0)
        coeff = drain_formula_coefficient(target_h, self.project.drain_discharge_k)
        return (
            "✅ FORMULES EXACTES CORRIGÉES :\n\n"
            "• Vidanges (Points Bas) :\n"
            f"  d (mm) = {coeff:.3f} × D × √(L_tot / √h_moy) pour t = {target_h:g}h\n"
            "  où h_moy = [Lam × (Ham/2) + Lav × (Hav/2)] / (Lam + Lav)\n"
            "  (Coefficient recalculé : 6.693 pour 2 h, 9.465 pour 1 h ;\n"
            "   le DN retenu est imposé égal au DN recommandé en mode auto.)\n\n"
            "• Célérité d'Allievi (Conduite PRV) :\n"
            "  a = 1 / √[ ρ × ( 1/K_eau + D/(E × e) ) ]\n"
            "  avec Keau = 2.07 GPa, E = 20 GPa (PRV) -> a ≈ 548 m/s.\n\n"
            "• Écoulement d'Air Compressible (Saint-Venant) :\n"
            "  Transition critique exacte à P2 = 19.55 mCE abs.\n"
            "  Subsonique : Q = 499 × s × (P1/P2)^0.714 × √(1 - (P1/P2)^0.286)\n"
            "  Sonique : Q = 129 × s (vitesse sonique au col de l'orifice).\n\n"
            "• Entrée d'Air en Casse Franche (Strickler-Bernoulli) :\n"
            "  Qair = (π D² / 4) × √[ H / ( 0.000587 × L / D^(4/3) + 0.102 ) ]\n"
            "  avec H = max(0 ; Cote_ventouse - 3.0 m - Cote_vidange).\n\n"
            "• Remplissage de la conduite à V = 0.5 m/s :\n"
            "  Débit d'air refoulé = 5 655 m³/h pour DN 2000 mm.\n"
            "  Nécessite au moins 2 ventouses DN 200 (5 300 m³/h chacune sous 1 mCE).\n"
        )

    def _render_kpi_cards(self):
        for widget in self.kpi_frame.winfo_children():
            widget.destroy()

        stats = self.project.get_summary_stats()

        # Carte 1: Ventouses
        v_ratio = f"{stats['air_valves_compliant']} / {stats['total_air_valves']}"
        v_sub = "100% Conforme" if stats['air_valves_non_compliant'] == 0 else f"{stats['air_valves_non_compliant']} sous-équipée(s)"
        v_color = "#2ED573" if stats['air_valves_non_compliant'] == 0 else "#FFA502"
        self._create_card(self.kpi_frame, 0, "🌬️ Points Hauts (Ventouses)", v_ratio, v_sub, v_color)

        # Carte 2: Vidanges
        d_ratio = f"{stats['drains_compliant']} / {stats['total_drains']}"
        target_label = f"{float(self.project.target_drain_time_hours or 2.0):g}h"
        d_sub = (
            f"Temps <= {target_label} respecté" if stats['drains_non_compliant'] == 0
            else f"{stats['drains_non_compliant']} tronçon(s) > {target_label} !"
        )
        d_color = "#2ED573" if stats['drains_non_compliant'] == 0 else "#FF4757"
        self._create_card(self.kpi_frame, 1, "💧 Points Bas (Vidanges)", d_ratio, d_sub, d_color)

        # Carte 3: Célérité Allievi
        c_val = f"{stats['wave_speed_allievi_ms']} m/s"
        c_sub = f"PRV DN {int(self.project.dn_main_conduite_m*1000)} e={self.project.pipe_thickness_m*1000:.0f}mm"
        self._create_card(self.kpi_frame, 2, "⚡ Célérité d'Allievi", c_val, c_sub, "#1E90FF")

        # Carte 4: Débit Max Air
        q_val = f"{stats['max_air_intake_m3s']} m³/s"
        q_sub = f"Vol. Eau: {stats['total_water_volume_m3']:,.0f} m³"
        self._create_card(self.kpi_frame, 3, "🌪️ Débit Max Air Requis", q_val, q_sub, "#9B59B6")

    def _create_card(self, parent, col, title, value, subtitle, accent_color):
        card = ctk.CTkFrame(parent, fg_color=("white", "#1E272E"), corner_radius=10, border_width=1, border_color=("gray85", "gray30"))
        card.grid(row=0, column=col, sticky="nsew", padx=6, pady=5)

        t_lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=("gray40", "gray70"))
        t_lbl.pack(anchor="w", padx=15, pady=(12, 2))

        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=22, weight="bold"), text_color=accent_color)
        val_lbl.pack(anchor="w", padx=15, pady=0)

        sub_lbl = ctk.CTkLabel(card, text=subtitle, font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"))
        sub_lbl.pack(anchor="w", padx=15, pady=(2, 12))

    def _add_form_row(self, parent, label_text: str, default_val: str) -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        lbl = ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=12), width=230, anchor="w")
        lbl.pack(side="left")
        entry = ctk.CTkEntry(row, height=28, font=ctk.CTkFont(size=12))
        entry.insert(0, default_val)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def _add_combo_row(self, parent, label_text: str, values: list, default_val: str) -> ctk.CTkComboBox:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        lbl = ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=12), width=230, anchor="w")
        lbl.pack(side="left")
        combo = ctk.CTkComboBox(row, values=values, height=28, font=ctk.CTkFont(size=12))
        combo.set(default_val)
        combo.pack(side="right", fill="x", expand=True)
        return combo

    def _apply_parameters(self):
        try:
            self.project.dn_main_conduite_m = float(self.entry_dn.get().replace(',', '.'))
            self.project.pipe_material = self.combo_mat.get()
            selected_catalog_label = self.combo_air_catalog.get()
            self.project.air_catalog_config = self._catalog_label_to_key.get(
                selected_catalog_label, CATALOG_CEAI_SNH
            )
            self.project.pipe_thickness_m = float(self.entry_thick.get().replace(',', '.')) / 1000.0
            self.project.ks_strickler = float(self.entry_ks.get().replace(',', '.'))
            self.project.v_filling_ms = float(self.entry_v_fill.get().replace(',', '.'))
            self.project.delta_p_admiss_mce = float(self.entry_dp.get().replace(',', '.'))
            self.project.q_nominal_water_m3s = float(self.entry_q_nom.get().replace(',', '.'))
            self.project.target_drain_time_hours = float(self.entry_t_drain.get().replace(',', '.'))
            self.project.drain_discharge_k = float(self.entry_k_drain.get().replace(',', '.'))

            self.project.calculate_all()
            self._render_kpi_cards()
            self.on_project_updated()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur de saisie", f"Veuillez vérifier les valeurs numériques saisies :\n{e}")

    def refresh(self):
        self._render_kpi_cards()
        if hasattr(self, "audit_lbl"):
            self.audit_lbl.configure(text=self._audit_text())
        if hasattr(self, "title_lbl"):
            self.title_lbl.configure(text=f"📊 Tableau de Bord Hydraulique — {self.project.name}")
        if hasattr(self, "desc_lbl"):
            self.desc_lbl.configure(text=self.project.description)

        # Synchroniser les champs de paramètres avec l'état courant du projet
        def _set_entry(entry, value):
            try:
                entry.delete(0, "end")
                entry.insert(0, str(value))
            except Exception:
                pass

        if hasattr(self, "entry_dn"):
            _set_entry(self.entry_dn, self.project.dn_main_conduite_m)
            if hasattr(self, "combo_mat"):
                self.combo_mat.set(self.project.pipe_material)
            _set_entry(self.entry_thick, self.project.pipe_thickness_m * 1000.0)
            _set_entry(self.entry_ks, self.project.ks_strickler)
            _set_entry(self.entry_v_fill, self.project.v_filling_ms)
            _set_entry(self.entry_dp, self.project.delta_p_admiss_mce)
            _set_entry(self.entry_q_nom, self.project.q_nominal_water_m3s)
            _set_entry(self.entry_t_drain, self.project.target_drain_time_hours)
            _set_entry(self.entry_k_drain, self.project.drain_discharge_k)

        if hasattr(self, "combo_air_catalog"):
            current_catalog_label = CATALOG_CONFIG_LABELS.get(
                self.project.air_catalog_config, CATALOG_CONFIG_LABELS[CATALOG_CEAI_SNH]
            )
            self.combo_air_catalog.set(current_catalog_label)
