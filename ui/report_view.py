"""
Vue Gestion des Imports et Exports de Livrables (CustomTkinter).
Permet l'import de fichiers Excel, l'exportation du rapport Word (.docx),
du classeur Excel (.xlsx) et des graphiques haute définition.
"""

import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Callable

from core.project_data import HydraulicProject
from core.excel_manager import export_project_to_xlsx, import_project_from_xlsx, create_blank_import_template
from core.word_report_generator import generate_word_report
from core.chart_generator import (
    plot_longitudinal_profile,
    plot_air_valves_comparison,
    plot_drain_times_comparison,
    plot_saint_venant_law
)


class ReportView(ctk.CTkFrame):
    def __init__(self, parent, project: HydraulicProject, on_project_updated: Callable):
        super().__init__(parent, fg_color="transparent")
        self.project = project
        self.on_project_updated = on_project_updated

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="📥 Imports & 📤 Exports des Rapports et Livrables",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1F497D", "#70A1FF")
        )
        title.pack(anchor="w", padx=20, pady=(12, 4))

        sub = ctk.CTkLabel(
            header,
            text="Génération automatique des rapports officiels Word (.docx), classeurs Excel (.xlsx) et packages graphiques",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        sub.pack(anchor="w", padx=20, pady=(0, 12))

        # Main Grid (2 colonnes : Imports à gauche, Exports à droite)
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=15, pady=5)
        grid.grid_columnconfigure((0, 1), weight=1, uniform="io")
        grid.grid_rowconfigure(0, weight=1)

        # 1. SECTION IMPORTS (Gauche)
        left = ctk.CTkFrame(grid, fg_color=("white", "#1E272E"), corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        ctk.CTkLabel(
            left,
            text="📥 Importation de Fichiers Excel",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#008080", "#00D2D3")
        )
        p1 = left
        p1_title = ctk.CTkLabel(left, text="📥 Importation de Fichiers Excel", font=ctk.CTkFont(size=15, weight="bold"), text_color=("#008080", "#00D2D3"))
        p1_title.pack(anchor="w", padx=20, pady=(15, 10))

        desc_import = ctk.CTkLabel(
            left,
            text=(
                "Vous pouvez importer vos propres données de points hauts et bas depuis un classeur Excel.\n"
                "Le système détecte automatiquement les colonnes (PM, Cotes, DN, Amont, Aval)."
            ),
            font=ctk.CTkFont(size=11),
            justify="left",
            text_color=("gray40", "gray70")
        )
        desc_import.pack(anchor="w", padx=20, pady=(0, 15))

        btn_import_excel = ctk.CTkButton(
            left,
            text="📂 Sélectionner et Importer un Fichier XLSX",
            fg_color="#0984E3",
            hover_color="#0873C4",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            command=self._import_excel
        )
        btn_import_excel.pack(fill="x", padx=20, pady=8)

        btn_template = ctk.CTkButton(
            left,
            text="📑 Télécharger le Gabarit / Modèle Excel Vierge",
            fg_color="#718093",
            hover_color="#2F3640",
            font=ctk.CTkFont(size=12),
            height=36,
            command=self._generate_template
        )
        btn_template.pack(fill="x", padx=20, pady=8)

        # Résumé des données actuelles
        curr_box = ctk.CTkFrame(left, fg_color=("gray95", "#2C3E50"), corner_radius=8)
        curr_box.pack(fill="both", expand=True, padx=20, pady=(15, 20))

        ctk.CTkLabel(curr_box, text="Projet Actuellement Chargé :", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))
        self.lbl_loaded_info = ctk.CTkLabel(
            curr_box,
            text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            justify="left"
        )
        self.lbl_loaded_info.pack(anchor="w", padx=12, pady=(0, 10))

        # 2. SECTION EXPORTS (Droite)
        right = ctk.CTkFrame(grid, fg_color=("white", "#1E272E"), corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)

        ctk.CTkLabel(
            right,
            text="📤 Génération des Rapports & Livrables",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#1F497D", "#70A1FF")
        ).pack(anchor="w", padx=20, pady=(15, 10))

        desc_export = ctk.CTkLabel(
            right,
            text="Exportez les rapports complets, documentés et prêts pour la soumission au Maître d'Ouvrage :",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70")
        )
        desc_export.pack(anchor="w", padx=20, pady=(0, 15))

        # Export Word
        btn_word = ctk.CTkButton(
            right,
            text="📄 Exporter Rapport Technique Complet (.DOCX)",
            fg_color="#2B5797", # Word blue
            hover_color="#1E3E6E",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            command=self._export_word
        )
        btn_word.pack(fill="x", padx=20, pady=6)

        # Export Excel
        btn_excel = ctk.CTkButton(
            right,
            text="📊 Exporter Classeur de Calculs Détaillé (.XLSX)",
            fg_color="#217346", # Excel green
            hover_color="#185533",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            command=self._export_excel
        )
        btn_excel.pack(fill="x", padx=20, pady=6)

        # Export Pack Graphique
        btn_charts = ctk.CTkButton(
            right,
            text="🖼️ Exporter le Pack Graphique Haute Résolution (PNG)",
            fg_color="#D35400",
            hover_color="#BA4A00",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            command=self._export_charts_pack
        )
        btn_charts.pack(fill="x", padx=20, pady=6)

        # Options de rapport
        opt_frame = ctk.CTkFrame(right, fg_color=("gray95", "#2C3E50"), corner_radius=8)
        opt_frame.pack(fill="x", padx=20, pady=(15, 15))

        self.cb_include_charts = ctk.CTkCheckBox(opt_frame, text="Insérer automatiquement les figures graphiques dans le DOCX", font=ctk.CTkFont(size=11))
        self.cb_include_charts.select()
        self.cb_include_charts.pack(anchor="w", padx=15, pady=(10, 5))

        self.cb_open_after = ctk.CTkCheckBox(opt_frame, text="Ouvrir le fichier généré après l'exportation", font=ctk.CTkFont(size=11))
        self.cb_open_after.select()
        self.cb_open_after.pack(anchor="w", padx=15, pady=(5, 10))

        self.refresh()

    def refresh(self):
        from core.catalogues_ceai_snh import CATALOG_CONFIG_LABELS, DEFAULT_AIR_CATALOG_CONFIG

        stats = self.project.get_summary_stats()
        catalog_label = CATALOG_CONFIG_LABELS.get(
            getattr(self.project, "air_catalog_config", DEFAULT_AIR_CATALOG_CONFIG),
            str(getattr(self.project, "air_catalog_config", DEFAULT_AIR_CATALOG_CONFIG)),
        )
        info_text = (
            f"• Nom : {self.project.name}\n"
            f"• Base catalogue air : {catalog_label}\n"
            f"• Ventouses : {stats['total_air_valves']} points ({stats['air_valves_compliant']} conformes)\n"
            f"• Vidanges : {stats['total_drains']} points ({stats['drains_compliant']} conformes)\n"
            f"• Conduite : DN {int(self.project.dn_main_conduite_m*1000)} mm ({self.project.pipe_material})\n"
            f"• Célérité Allievi : {stats['wave_speed_allievi_ms']} m/s\n"
            f"• Volume eau : {stats['total_water_volume_m3']:,.1f} m³"
        )
        self.lbl_loaded_info.configure(text=info_text)

    def _import_excel(self):
        app = self.winfo_toplevel()
        if hasattr(app, "_confirm_discard_or_save") and not app._confirm_discard_or_save():
            return

        fpath = filedialog.askopenfilename(
            title="Sélectionner un fichier Excel",
            filetypes=[("Fichiers Excel", "*.xlsx;*.xlsm"), ("Tous les fichiers", "*.*")]
        )
        if not fpath:
            return
        try:
            new_proj = import_project_from_xlsx(fpath)
            # Mettre à jour le projet existant
            self.project.name = new_proj.name
            self.project.description = new_proj.description
            self.project.identity = new_proj.identity
            self.project.dn_main_conduite_m = new_proj.dn_main_conduite_m
            self.project.pipe_material = new_proj.pipe_material
            self.project.pipe_thickness_m = new_proj.pipe_thickness_m
            self.project.ks_strickler = new_proj.ks_strickler
            self.project.v_filling_ms = new_proj.v_filling_ms
            self.project.delta_p_admiss_mce = new_proj.delta_p_admiss_mce
            self.project.q_nominal_water_m3s = new_proj.q_nominal_water_m3s
            self.project.target_drain_time_hours = new_proj.target_drain_time_hours
            self.project.drain_discharge_k = new_proj.drain_discharge_k
            self.project.air_catalog_config = new_proj.air_catalog_config
            self.project.air_valves = new_proj.air_valves
            self.project.drains = new_proj.drains
            self.project.calculate_all()

            # Import remplace le projet courant (fichier projet source non associé)
            if hasattr(app, "current_project_path"):
                app.current_project_path = None

            self.refresh()
            self.on_project_updated()

            messagebox.showinfo(
                "Import Réussi",
                f"Le fichier a été importé avec succès !\n"
                f"• {len(self.project.air_valves)} points hauts (ventouses)\n"
                f"• {len(self.project.drains)} points bas (vidanges)\n\n"
                "Pensez à enregistrer le projet (Fichier > Enregistrer) pour conserver ces données et calculs."
            )
        except Exception as e:
            messagebox.showerror("Erreur d'importation", f"Impossible d'importer le fichier Excel :\n{e}")

    def _generate_template(self):
        fpath = filedialog.asksaveasfilename(
            title="Enregistrer le gabarit Excel",
            initialfile="Template_Import_Hydraulique.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Fichier Excel", "*.xlsx")]
        )
        if fpath:
            try:
                create_blank_import_template(fpath)
                messagebox.showinfo("Gabarit Créé", f"Le gabarit vierge a été généré avec succès :\n{fpath}")
                if self.cb_open_after.get():
                    os.startfile(fpath)
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def _export_word(self):
        fpath = filedialog.asksaveasfilename(
            title="Enregistrer le rapport Word",
            initialfile=f"Rapport_Expertise_{self.project.name.replace(' ', '_')}.docx",
            defaultextension=".docx",
            filetypes=[("Document Word", "*.docx")]
        )
        if not fpath:
            return
        try:
            generate_word_report(
                project=self.project,
                output_docx_path=fpath,
                include_charts=bool(self.cb_include_charts.get())
            )
            messagebox.showinfo("Export Réussi", f"Le rapport technique Word a été généré avec succès :\n{fpath}")
            if self.cb_open_after.get():
                os.startfile(fpath)
        except Exception as e:
            messagebox.showerror("Erreur lors de la génération du rapport", str(e))

    def _export_excel(self):
        fpath = filedialog.asksaveasfilename(
            title="Enregistrer le classeur Excel",
            initialfile=f"Calculs_Hydrauliques_{self.project.name.replace(' ', '_')}.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Classeur Excel", "*.xlsx")]
        )
        if not fpath:
            return
        try:
            export_project_to_xlsx(self.project, fpath)
            messagebox.showinfo("Export Réussi", f"Le classeur Excel a été généré avec succès :\n{fpath}")
            if self.cb_open_after.get():
                os.startfile(fpath)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def _export_charts_pack(self):
        folder = filedialog.askdirectory(title="Sélectionner le dossier de destination des graphiques")
        if not folder:
            return
        try:
            f1 = os.path.join(folder, "01_Profil_en_long_hydraulique.png")
            f2 = os.path.join(folder, "02_Debits_air_casse_franche.png")
            f3 = os.path.join(folder, "03_Temps_reels_vidange.png")
            f4 = os.path.join(folder, "04_Loi_Saint_Venant_air.png")

            plot_longitudinal_profile(self.project, f1)
            plot_air_valves_comparison(self.project, f2)
            plot_drain_times_comparison(self.project, f3)
            plot_saint_venant_law(f4)

            messagebox.showinfo(
                "Pack Graphique Exporté",
                f"Les 4 graphiques ont été générés en haute définition (300 DPI) dans :\n{folder}"
            )
            if self.cb_open_after.get():
                subprocess.Popen(f'explorer "{os.path.realpath(folder)}"')
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
