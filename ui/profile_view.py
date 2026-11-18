"""
Vue Profil en Long & Graphiques Hydrauliques interactifs (CustomTkinter).
Intègre Matplotlib avec FigureCanvasTkAgg pour visualiser en temps réel
le profil de l'adduction, les débits d'air et les durées de vidange.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import matplotlib
matplotlib.use('TkAgg') # Mode TkAgg pour intégration dans l'UI
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

from core.project_data import HydraulicProject
from core.chart_generator import (
    plot_longitudinal_profile,
    plot_air_valves_comparison,
    plot_drain_times_comparison,
    plot_saint_venant_law
)


class ProfileView(ctk.CTkFrame):
    def __init__(self, parent, project: HydraulicProject):
        super().__init__(parent, fg_color="transparent")
        self.project = project
        self.current_fig = None
        self.canvas = None
        self.toolbar = None

        self._build_ui()

    def _build_ui(self):
        # Header & Sélecteur de graphique
        header = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        top_row = ctk.CTkFrame(header, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=12)

        title = ctk.CTkLabel(
            top_row,
            text="📈 Visualisations Graphiques & Profil en Long",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1F497D", "#70A1FF")
        )
        title.pack(side="left")

        # Bouton export image
        btn_save = ctk.CTkButton(
            top_row,
            text="💾 Exporter le Graphique (PNG / PDF)",
            fg_color="#0984E3",
            hover_color="#0873C4",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self._export_chart
        )
        btn_save.pack(side="right")

        # Sélecteur d'onglets de graphique
        selector_frame = ctk.CTkFrame(header, fg_color="transparent")
        selector_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.chart_type_var = ctk.StringVar(value="profil")

        btn_p1 = ctk.CTkRadioButton(selector_frame, text="Profil en long de l'adduction", variable=self.chart_type_var, value="profil", command=self.refresh)
        btn_p1.pack(side="left", padx=(0, 15))

        btn_p2 = ctk.CTkRadioButton(selector_frame, text="Débits d'air (Requis vs Équipé)", variable=self.chart_type_var, value="air", command=self.refresh)
        btn_p2.pack(side="left", padx=(0, 15))

        btn_p3 = ctk.CTkRadioButton(selector_frame, text="Temps réels de vidange", variable=self.chart_type_var, value="drain", command=self.refresh)
        btn_p3.pack(side="left", padx=(0, 15))

        btn_p4 = ctk.CTkRadioButton(selector_frame, text="Loi d'échappement Saint-Venant", variable=self.chart_type_var, value="sv", command=self.refresh)
        btn_p4.pack(side="left")

        # Conteneur Canvas Matplotlib
        self.canvas_container = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        self.canvas_container.pack(fill="both", expand=True, padx=15, pady=5)

        self.refresh()

    def refresh(self):
        """Redessine le graphique sélectionné dans le canvas."""
        # Nettoyage précédent
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None
        if self.current_fig:
            plt.close(self.current_fig)
            self.current_fig = None

        chart_type = self.chart_type_var.get()

        if chart_type == "profil":
            self.current_fig = plot_longitudinal_profile(self.project)
        elif chart_type == "air":
            self.current_fig = plot_air_valves_comparison(self.project)
        elif chart_type == "drain":
            self.current_fig = plot_drain_times_comparison(self.project)
        elif chart_type == "sv":
            self.current_fig = plot_saint_venant_law()

        self.canvas = FigureCanvasTkAgg(self.current_fig, master=self.canvas_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.canvas_container)
        self.toolbar.update()
        self.toolbar.pack(fill="x", padx=10, pady=(0, 10))

    def _export_chart(self):
        if not self.current_fig:
            return
        fpath = filedialog.asksaveasfilename(
            title="Enregistrer le graphique",
            defaultextension=".png",
            filetypes=[("Image PNG", "*.png"), ("Document PDF", "*.pdf"), ("Tous les fichiers", "*.*")]
        )
        if fpath:
            try:
                self.current_fig.savefig(fpath, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export Réussi", f"Le graphique a été enregistré avec succès :\n{fpath}")
            except Exception as e:
                messagebox.showerror("Erreur d'export", f"Impossible d'enregistrer le graphique :\n{e}")
