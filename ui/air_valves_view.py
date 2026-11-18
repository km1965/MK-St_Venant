"""
Vue des Points Hauts / Ventouses (CustomTkinter).
Tableau interactif complet, vérification des 3 fonctions, édition et ajout de points hauts.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from core.project_data import HydraulicProject, AirValvePoint


class AirValvesView(ctk.CTkFrame):
    def __init__(self, parent, project: HydraulicProject, on_project_updated: Callable):
        super().__init__(parent, fg_color="transparent")
        self.project = project
        self.on_project_updated = on_project_updated

        self._build_ui()

    def _build_ui(self):
        # Header & Actions Bar
        header = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        top_row = ctk.CTkFrame(header, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=12)

        title = ctk.CTkLabel(
            top_row,
            text="🌬️ Dimensionnement et Vérification des Points Hauts (Ventouses)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1F497D", "#70A1FF")
        )
        title.pack(side="left")

        # Boutons d'action
        btn_apply_rec = ctk.CTkButton(
            top_row,
            text="✨ Retenir 100% Recommandations",
            fg_color="#00B894",
            hover_color="#00A884",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self._apply_all_recommendations
        )
        btn_apply_rec.pack(side="right", padx=(5, 0))

        btn_add = ctk.CTkButton(
            top_row,
            text="➕ Ajouter Point Haut",
            fg_color="#0984E3",
            hover_color="#0873C4",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self._open_add_dialog
        )
        btn_add.pack(side="right", padx=(5, 0))

        # Instructions / Légende
        info_lbl = ctk.CTkLabel(
            header,
            text="Vérification des 3 fonctions : (1) Dégazage en service | (2) Évacuation d'air au remplissage (V=0.5 m/s) | (3) Casse franche sous dépression admissible (3 mCE)",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray70")
        )
        info_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        # Tableau Treeview
        table_container = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        table_container.pack(fill="both", expand=True, padx=15, pady=5)

        columns = (
            "id", "pm", "z", "dn",
            "q_am", "q_av", "q_max",
            "init_equip", "init_q",
            "rec_equip", "rec_q",
            "status", "comment"
        )

        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")

        # Configuration des colonnes
        headers = {
            "id": ("N°", 40, "center"),
            "pm": ("PM (m)", 85, "e"),
            "z": ("Cote (m)", 70, "e"),
            "dn": ("DN (m)", 60, "center"),
            "q_am": ("Q amont (m³/s)", 95, "e"),
            "q_av": ("Q aval (m³/s)", 95, "e"),
            "q_max": ("Q max req (m³/s)", 105, "e"),
            "init_equip": ("Équipement Note Initiale", 170, "w"),
            "init_q": ("Q init (m³/s)", 85, "e"),
            "rec_equip": ("Équipement Corrigé Recommandé", 220, "w"),
            "rec_q": ("Q admis (m³/s)", 95, "e"),
            "status": ("Conformité", 95, "center"),
            "comment": ("Diagnostic / Observations", 220, "w")
        }

        for col_id, (text, width, align) in headers.items():
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, anchor=align)

        # Style Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10), background="#FFFFFF", fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#1F497D", foreground="#FFFFFF")
        style.map("Treeview", background=[('selected', '#70A1FF')], foreground=[('selected', '#FFFFFF')])

        # Scrollbars
        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        vsb.grid(row=0, column=1, sticky="ns", pady=10)
        hsb.grid(row=1, column=0, sticky="ew", padx=10)
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Tags de couleur pour lignes
        self.tree.tag_configure("compliant", foreground="#008000")
        self.tree.tag_configure("non_compliant", foreground="#C00000", font=("Segoe UI", 10, "bold"))

        # Barre d'actions sous tableau
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=15, pady=(5, 15))

        btn_edit = ctk.CTkButton(
            action_bar,
            text="✏️ Modifier la sélection",
            width=160,
            fg_color="#34495E",
            hover_color="#2C3E50",
            command=self._open_edit_dialog
        )
        btn_edit.pack(side="left", padx=(0, 10))

        btn_del = ctk.CTkButton(
            action_bar,
            text="🗑️ Supprimer",
            width=120,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._delete_selected
        )
        btn_del.pack(side="left")

        self.refresh()

    def refresh(self):
        """Recharge les données du tableau."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for v in self.project.air_valves:
            tag = "compliant" if v.is_compliant else "non_compliant"
            status_text = "CONFORME" if v.is_compliant else "NON CONFORME"

            self.tree.insert("", "end", iid=str(v.id), values=(
                v.id,
                f"{v.pm:,.2f}",
                f"{v.z_terrain:.2f}",
                f"{v.dn_conduite_m:.2f}",
                f"{v.q_air_amont_m3s:.2f}",
                f"{v.q_air_aval_m3s:.2f}",
                f"{v.q_air_max_m3s:.2f}",
                v.initial_equipment,
                f"{v.initial_flow_admitted:.2f}" if v.initial_flow_admitted > 0 else "-",
                v.recommended_equipment,
                f"{v.q_admis_m3s:.2f}",
                status_text,
                v.comment
            ), tags=(tag,))

    def _apply_all_recommendations(self):
        for v in self.project.air_valves:
            v.retained_equipment = v.recommended_equipment
        self.project.calculate_all()
        self.refresh()
        self.on_project_updated()
        messagebox.showinfo("Recommandations Appliquées", "Tous les points hauts ont été équipés avec les recommandations corrigées optimales.")

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un point haut à supprimer.")
            return
        vid = int(selected[0])
        self.project.air_valves = [v for v in self.project.air_valves if v.id != vid]
        self.project.calculate_all()
        self.refresh()
        self.on_project_updated()

    def _open_add_dialog(self):
        self._show_valve_dialog(title="Ajouter un Point Haut (Ventouse)")

    def _open_edit_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un point haut à modifier.")
            return
        vid = int(selected[0])
        valve = next((v for v in self.project.air_valves if v.id == vid), None)
        if valve:
            self._show_valve_dialog(title=f"Modifier le Point Haut PM {valve.pm}", valve=valve)

    def _show_valve_dialog(self, title: str, valve: Optional[AirValvePoint] = None):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("520x620")
        dialog.grab_set()

        lbl_t = ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        lbl_t.pack(padx=20, pady=(15, 10))

        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=5)

        e_pm = self._dialog_row(content, "PM Point Haut (m) :", str(valve.pm) if valve else "50000.00")
        e_z = self._dialog_row(content, "Cote Altimétrique Projet (m) :", str(valve.z_terrain) if valve else "100.00")
        e_dn = self._dialog_row(content, "DN Conduite Principale (m) :", str(valve.dn_conduite_m) if valve else str(self.project.dn_main_conduite_m))

        e_pm_am = self._dialog_row(content, "PM Vidange Amont (m) :", str(valve.pm_amont) if valve and valve.pm_amont else "")
        e_z_am = self._dialog_row(content, "Cote Vidange Amont (m) :", str(valve.z_amont) if valve and valve.z_amont else "")

        e_pm_av = self._dialog_row(content, "PM Vidange Aval (m) :", str(valve.pm_aval) if valve and valve.pm_aval else "")
        e_z_av = self._dialog_row(content, "Cote Vidange Aval (m) :", str(valve.z_aval) if valve and valve.z_aval else "")

        e_init_eq = self._dialog_row(content, "Équipement Prévu Initialement :", valve.initial_equipment if valve else "")
        e_init_q = self._dialog_row(content, "Débit Admis Initial (m³/s) :", str(valve.initial_flow_admitted) if valve else "0.0")

        def save_action():
            try:
                pm = float(e_pm.get().replace(',', '.'))
                z = float(e_z.get().replace(',', '.'))
                dn = float(e_dn.get().replace(',', '.'))
                pm_am = float(e_pm_am.get().replace(',', '.')) if e_pm_am.get().strip() else None
                z_am = float(e_z_am.get().replace(',', '.')) if e_z_am.get().strip() else None
                pm_av = float(e_pm_av.get().replace(',', '.')) if e_pm_av.get().strip() else None
                z_av = float(e_z_av.get().replace(',', '.')) if e_z_av.get().strip() else None
                init_eq = e_init_eq.get().strip()
                init_q = float(e_init_q.get().replace(',', '.')) if e_init_q.get().strip() else 0.0

                if valve:
                    valve.pm = pm
                    valve.z_terrain = z
                    valve.dn_conduite_m = dn
                    valve.pm_amont = pm_am
                    valve.z_amont = z_am
                    valve.pm_aval = pm_av
                    valve.z_aval = z_av
                    valve.initial_equipment = init_eq
                    valve.initial_flow_admitted = init_q
                else:
                    new_id = max([v.id for v in self.project.air_valves], default=0) + 1
                    new_v = AirValvePoint(
                        id=new_id, pm=pm, z_terrain=z, dn_conduite_m=dn,
                        pm_amont=pm_am, z_amont=z_am, pm_aval=pm_av, z_aval=z_av,
                        initial_equipment=init_eq, initial_flow_admitted=init_q
                    )
                    self.project.air_valves.append(new_v)

                self.project.air_valves.sort(key=lambda x: x.pm)
                self.project.calculate_all()
                self.refresh()
                self.on_project_updated()
                dialog.destroy()
            except Exception as ex:
                messagebox.showerror("Erreur", f"Données invalides :\n{ex}")

        btn_save = ctk.CTkButton(dialog, text="Valider et Recalculer", fg_color="#00A8FF", height=38, command=save_action)
        btn_save.pack(fill="x", padx=20, pady=(10, 15))

    def _dialog_row(self, parent, label: str, val: str) -> ctk.CTkEntry:
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=4)
        ctk.CTkLabel(f, text=label, width=220, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left")
        e = ctk.CTkEntry(f, height=28)
        e.insert(0, val)
        e.pack(side="right", fill="x", expand=True)
        return e
