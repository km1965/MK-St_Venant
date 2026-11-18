"""
Fenêtre Principale de l'application MK-St_Venant (CustomTkinter).
Gère la barre latérale de navigation, le menu, l'état global du projet,
la persistance (sauvegarde/ouverture) et les thèmes d'affichage.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.project_data import HydraulicProject
from core.sample_data import load_br3_lot8_project
from core.excel_manager import import_project_from_xlsx

from ui.dashboard_view import DashboardView
from ui.air_valves_view import AirValvesView
from ui.drains_view import DrainsView
from ui.simulator_view import SimulatorView
from ui.profile_view import ProfileView
from ui.catalog_view import CatalogView
from ui.report_view import ReportView
from ui.about_view import AboutView


PROJECT_FILETYPES = [
    ("Projet MK-St_Venant", "*.mkst.json"),
    ("Fichier JSON", "*.json"),
    ("Tous les fichiers", "*.*"),
]


class MainApplication(ctk.CTk):
    def __init__(self):
        super().__init__()

        # État projet / persistance
        self.current_project_path: str | None = None
        self.is_dirty: bool = False

        # Style CustomTkinter
        ctk.set_appearance_mode("Dark")  # "Dark" ou "Light"
        ctk.set_default_color_theme("blue")

        # Configuration de la fenêtre principale
        self.geometry("1300x820")
        self.minsize(1050, 680)

        # Initialisation avec les données vérifiées du Lot 8 (non enregistré)
        self.project: HydraulicProject = load_br3_lot8_project()

        # Layout principal (Barre latérale à gauche, Contenu dynamique à droite)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_menu()
        self._build_sidebar()
        self._build_views()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._bind_shortcuts()

        # Affichage par défaut : Tableau de bord
        self._select_view("dashboard")
        self._on_project_updated(is_dirty=False)

    def _build_menu(self):
        menubar = tk.Menu(self)

        # Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nouveau projet", command=self._new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Ouvrir un projet...", command=self._open_project, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Enregistrer", command=self._save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Enregistrer sous...", command=self._save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Importer depuis Excel...", command=self._import_excel_from_menu, accelerator="Ctrl+I")
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self._on_close, accelerator="Ctrl+Q")
        menubar.add_cascade(label="Fichier", menu=file_menu)

        # Affichage
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Tableau de bord", command=lambda: self._select_view("dashboard"))
        view_menu.add_command(label="Points hauts (ventouses)", command=lambda: self._select_view("air_valves"))
        view_menu.add_command(label="Points bas (vidanges)", command=lambda: self._select_view("drains"))
        view_menu.add_command(label="Profil & graphiques", command=lambda: self._select_view("profile"))
        view_menu.add_separator()
        theme_menu = tk.Menu(view_menu, tearoff=0)
        theme_menu.add_command(label="Sombre", command=lambda: self._change_appearance_mode("Dark"))
        theme_menu.add_command(label="Clair", command=lambda: self._change_appearance_mode("Light"))
        theme_menu.add_command(label="Système", command=lambda: self._change_appearance_mode("System"))
        view_menu.add_cascade(label="Thème", menu=theme_menu)
        menubar.add_cascade(label="Affichage", menu=view_menu)

        # Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Guide utilisateur", command=lambda: self._select_view("about"))
        help_menu.add_command(label="À propos de MK-St_Venant", command=self._show_about_dialog)
        menubar.add_cascade(label="Aide", menu=help_menu)

        self.config(menu=menubar)

    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self._new_project())
        self.bind_all("<Control-o>", lambda e: self._open_project())
        self.bind_all("<Control-s>", lambda e: self._save_project())
        self.bind_all("<Control-S>", lambda e: self._save_project_as())
        self.bind_all("<Control-Shift-s>", lambda e: self._save_project_as())
        self.bind_all("<Control-Shift-S>", lambda e: self._save_project_as())
        self.bind_all("<Control-i>", lambda e: self._import_excel_from_menu())
        self.bind_all("<Control-q>", lambda e: self._on_close())

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        # Logo / Titre
        app_title = ctk.CTkLabel(
            self.sidebar_frame,
            text="💧 MK-St_Venant",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#00A8FF",
        )
        app_title.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        app_sub = ctk.CTkLabel(
            self.sidebar_frame,
            text="Adductions & Sécurité Hydraulique",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray50"),
        )
        app_sub.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Boutons de navigation
        self.nav_buttons = {}

        nav_items = [
            ("dashboard", "📊 Tableau de Bord", 2),
            ("air_valves", "🌬️ Points Hauts (Ventouses)", 3),
            ("drains", "💧 Points Bas (Vidanges)", 4),
            ("simulator", "⚡ Simulateur Unitaire", 5),
            ("profile", "📈 Profil & Graphiques", 6),
            ("catalog", "📚 Catalogue Équipements", 7),
            ("reports", "📥 Imports / 📤 Exports", 8),
            ("about", "ℹ️ À propos & Aide", 9),
        ]

        for key, text, r in nav_items:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=text,
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "#2C3E50"),
                command=lambda k=key: self._select_view(k),
            )
            btn.grid(row=r, column=0, padx=12, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Bas de sidebar
        bottom_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        bottom_frame.grid(row=10, column=0, padx=15, pady=(10, 20), sticky="ew")

        btn_save = ctk.CTkButton(
            bottom_frame,
            text="💾 Enregistrer le projet",
            height=32,
            fg_color="#00A8FF",
            hover_color="#0097E6",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._save_project,
        )
        btn_save.pack(fill="x", pady=(0, 8))

        btn_reload = ctk.CTkButton(
            bottom_frame,
            text="🔄 Recharger Cas BR3_LOT 8",
            height=32,
            fg_color="#34495E",
            hover_color="#2C3E50",
            font=ctk.CTkFont(size=11),
            command=self._reload_br3_lot8,
        )
        btn_reload.pack(fill="x", pady=(0, 15))

        # Sélecteur de mode d'apparence
        theme_lbl = ctk.CTkLabel(
            bottom_frame, text="Thème d'affichage :", font=ctk.CTkFont(size=11), text_color="gray60"
        )
        theme_lbl.pack(anchor="w", pady=(0, 2))

        self.theme_menu = ctk.CTkOptionMenu(
            bottom_frame,
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode,
            height=28,
        )
        self.theme_menu.pack(fill="x")
        self.theme_menu.set("Dark")

    def _build_views(self):
        """Instancie toutes les vues dans le conteneur principal."""
        self.container = ctk.CTkFrame(self, fg_color=("gray95", "#12181F"), corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.views = {
            "dashboard": DashboardView(self.container, self.project, self._on_project_updated),
            "air_valves": AirValvesView(self.container, self.project, self._on_project_updated),
            "drains": DrainsView(self.container, self.project, self._on_project_updated),
            "simulator": SimulatorView(self.container),
            "profile": ProfileView(self.container, self.project),
            "catalog": CatalogView(self.container),
            "reports": ReportView(self.container, self.project, self._on_project_updated),
            "about": AboutView(self.container, self.project),
        }

        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

    # ---------- Gestion d'état / titre ----------

    def _update_window_title(self):
        name = getattr(self.project, "name", "Projet")
        if self.current_project_path:
            path_display = self.current_project_path
        else:
            path_display = "Non enregistré"
        dirty_mark = " *" if self.is_dirty else ""
        self.title(f"MK-St_Venant — {name} [{path_display}]{dirty_mark}")

    def _mark_dirty(self, dirty: bool = True):
        self.is_dirty = bool(dirty)
        self._update_window_title()

    def _on_project_updated(self, is_dirty: bool = True):
        """Appelée dès qu'une modification intervient pour rafraîchir les vues dépendantes."""
        if is_dirty:
            self.is_dirty = True
        self._update_window_title()

        for key in ("dashboard", "air_valves", "drains", "profile", "reports", "about"):
            view = self.views.get(key)
            if view and hasattr(view, "refresh"):
                try:
                    view.refresh()
                except Exception:
                    pass

    def _replace_project(self, new_project: HydraulicProject):
        """Remplace les données du projet courant en conservant l'instance référencée par les vues."""
        self.project.name = new_project.name
        self.project.description = new_project.description
        self.project.dn_main_conduite_m = new_project.dn_main_conduite_m
        self.project.pipe_material = new_project.pipe_material
        self.project.pipe_thickness_m = new_project.pipe_thickness_m
        self.project.ks_strickler = new_project.ks_strickler
        self.project.v_filling_ms = new_project.v_filling_ms
        self.project.delta_p_admiss_mce = new_project.delta_p_admiss_mce
        self.project.q_nominal_water_m3s = new_project.q_nominal_water_m3s
        self.project.target_drain_time_hours = new_project.target_drain_time_hours
        self.project.drain_discharge_k = new_project.drain_discharge_k
        self.project.air_catalog_config = new_project.air_catalog_config
        self.project.air_valves = new_project.air_valves
        self.project.drains = new_project.drains
        self.project.calculate_all()

    # ---------- Navigation ----------

    def _select_view(self, view_key: str):
        """Active la vue demandée et met en surbrillance son bouton."""
        for k, btn in self.nav_buttons.items():
            if k == view_key:
                btn.configure(fg_color=("#1F497D", "#1E90FF"), text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

        target_view = self.views.get(view_key)
        if target_view:
            if hasattr(target_view, "refresh"):
                try:
                    target_view.refresh()
                except Exception:
                    pass
            target_view.tkraise()

    # ---------- Fichier / persistance ----------

    def _confirm_discard_or_save(self) -> bool:
        """Retourne True si l'action peut continuer (projet sauvegardé ou abandon des modifs accepté)."""
        if not self.is_dirty:
            return True
        choice = messagebox.askyesnocancel(
            "Modifications non enregistrées",
            "Le projet actuel contient des modifications non enregistrées.\n\n"
            "Voulez-vous les enregistrer avant de continuer ?",
            icon=messagebox.WARNING,
        )
        if choice is None:  # Annuler
            return False
        if choice is True:  # Oui -> enregistrer
            return self._save_project()
        return True  # Non -> continuer sans enregistrer

    def _new_project(self):
        if not self._confirm_discard_or_save():
            return
        new_proj = HydraulicProject(name="Nouveau projet", description="Projet vierge")
        new_proj.air_valves = []
        new_proj.drains = []
        self._replace_project(new_proj)
        self.current_project_path = None
        self._select_view("dashboard")
        self._on_project_updated(is_dirty=False)

    def _open_project(self):
        if not self._confirm_discard_or_save():
            return
        fpath = filedialog.askopenfilename(
            title="Ouvrir un projet MK-St_Venant",
            filetypes=PROJECT_FILETYPES,
        )
        if not fpath:
            return
        try:
            loaded = HydraulicProject.load_from_file(fpath)
            self._replace_project(loaded)
            self.current_project_path = fpath
            self._select_view("dashboard")
            self._on_project_updated(is_dirty=False)
            messagebox.showinfo("Projet ouvert", f"Projet chargé avec succès :\n{fpath}")
        except Exception as e:
            messagebox.showerror("Erreur d'ouverture", f"Impossible d'ouvrir le projet :\n{e}")

    def _save_project(self) -> bool:
        if not self.current_project_path:
            return self._save_project_as()
        try:
            self.project.save_to_file(self.current_project_path)
            self._mark_dirty(False)
            messagebox.showinfo("Projet enregistré", f"Projet enregistré :\n{self.current_project_path}")
            return True
        except Exception as e:
            messagebox.showerror("Erreur d'enregistrement", f"Impossible d'enregistrer le projet :\n{e}")
            return False

    def _save_project_as(self) -> bool:
        initial = (self.project.name or "projet").replace(" ", "_")
        fpath = filedialog.asksaveasfilename(
            title="Enregistrer le projet sous",
            initialfile=f"{initial}.mkst.json",
            defaultextension=".mkst.json",
            filetypes=PROJECT_FILETYPES,
        )
        if not fpath:
            return False
        try:
            self.project.save_to_file(fpath)
            self.current_project_path = fpath
            self._mark_dirty(False)
            messagebox.showinfo("Projet enregistré", f"Projet enregistré :\n{fpath}")
            return True
        except Exception as e:
            messagebox.showerror("Erreur d'enregistrement", f"Impossible d'enregistrer le projet :\n{e}")
            return False

    def _import_excel_from_menu(self):
        if not self._confirm_discard_or_save():
            return
        fpath = filedialog.askopenfilename(
            title="Importer un fichier Excel",
            filetypes=[("Fichiers Excel", "*.xlsx;*.xlsm"), ("Tous les fichiers", "*.*")],
        )
        if not fpath:
            return
        try:
            new_proj = import_project_from_xlsx(fpath)
            self._replace_project(new_proj)
            self.current_project_path = None
            self._select_view("reports")
            self._on_project_updated(is_dirty=True)
            messagebox.showinfo(
                "Import réussi",
                f"Le fichier a été importé avec succès !\n"
                f"• {len(self.project.air_valves)} points hauts (ventouses)\n"
                f"• {len(self.project.drains)} points bas (vidanges)\n\n"
                "Pensez à enregistrer le projet (Fichier > Enregistrer) pour conserver ces données et calculs.",
            )
        except Exception as e:
            messagebox.showerror("Erreur d'importation", f"Impossible d'importer le fichier Excel :\n{e}")

    # ---------- Actions diverses ----------

    def _reload_br3_lot8(self):
        if not self._confirm_discard_or_save():
            return
        confirm = messagebox.askyesno(
            "Réinitialisation",
            "Voulez-vous recharger le jeu de données de référence du projet Adduction BR3_LOT 8 ?",
        )
        if not confirm:
            return
        reloaded = load_br3_lot8_project()
        self._replace_project(reloaded)
        self.current_project_path = None
        self._select_view("dashboard")
        self._on_project_updated(is_dirty=False)
        messagebox.showinfo("Projet rechargé", "Le cas de référence BR3_LOT 8 a été rechargé avec succès.")

    def _change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)
        if hasattr(self, "theme_menu"):
            try:
                self.theme_menu.set(new_mode)
            except Exception:
                pass

    def _show_about_dialog(self):
        from ui.about_view import APP_NAME, APP_VERSION

        messagebox.showinfo(
            f"À propos de {APP_NAME}",
            f"{APP_NAME}\nVersion {APP_VERSION}\n\n"
            "Outil d'ingénierie hydraulique pour le dimensionnement et la vérification "
            "des ventouses (points hauts) et vidanges (points bas).\n\n"
            "Utilisez Fichier > Enregistrer pour conserver vos imports et calculs dans un fichier projet (.mkst.json).",
        )

    def _on_close(self):
        if not self._confirm_discard_or_save():
            return
        self.destroy()
