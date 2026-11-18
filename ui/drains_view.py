"""
Vue des Points Bas / Vidanges (CustomTkinter).
Tableau interactif complet, calculs exacts des hauteurs moyennes pondérées,
diamètres théoriques, DN recommandés et durées réelles de vidange.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from core.project_data import HydraulicProject, DrainPoint
from core.catalog import STANDARD_DRAIN_DIAMETERS_MM


class DrainsView(ctk.CTkFrame):
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
            text="💧 Dimensionnement et Vérification des Vidanges (Points Bas)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#008080", "#00D2D3")
        )
        title.pack(side="left")

        # Boutons d'action
        btn_apply_rec = ctk.CTkButton(
            top_row,
            text="✨ Appliquer DN Recommandés (100% <= 2h)",
            fg_color="#00B894",
            hover_color="#00A884",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self._apply_all_recommended_dn
        )
        btn_apply_rec.pack(side="right", padx=(5, 0))

        btn_auto = ctk.CTkButton(
            top_row,
            text="⚡ Déduire depuis Ventouses",
            fg_color="#6C5CE7",
            hover_color="#5848C2",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self._auto_generate_from_valves
        )
        btn_auto.pack(side="right", padx=(5, 0))

        btn_apply_400 = ctk.CTkButton(
            top_row,
            text="⚠️ Tester DN 400 Uniformisé",
            fg_color="#E67E22",
            hover_color="#D35400",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self._apply_uniform_400
        )
        btn_apply_400.pack(side="right", padx=(5, 0))

        btn_add = ctk.CTkButton(
            top_row,
            text="➕ Ajouter Point Bas",
            fg_color="#0984E3",
            hover_color="#0873C4",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            command=self._open_add_dialog
        )
        btn_add.pack(side="right", padx=(5, 0))

        # Instructions / Formules
        info_lbl = ctk.CTkLabel(
            header,
            text="Formule exacte : d (mm) = 6.69 × D × √(L_tot / √h_moy) pour vidange en 2h | Hauteur pondérée h_moy = [Lam·(Ham/2) + Lav·(Hav/2)] / L_tot",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray70")
        )
        info_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        # Tableau Treeview
        table_container = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        table_container.pack(fill="both", expand=True, padx=15, pady=5)

        columns = (
            "id", "pm", "z", "dn_pipe",
            "l_tot", "h_moy", "vol_eau",
            "d_exact", "dn_rec",
            "dn_ret", "t_reel", "status", "comment"
        )

        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")

        headers = {
            "id": ("N°", 40, "center"),
            "pm": ("PM (m)", 85, "e"),
            "z": ("Cote (m)", 70, "e"),
            "dn_pipe": ("DN Cond (m)", 75, "center"),
            "l_tot": ("L totale (m)", 90, "e"),
            "h_moy": ("hmoy (m)", 75, "e"),
            "vol_eau": ("Vol. Eau (m³)", 95, "e"),
            "d_exact": ("d exact 2h (mm)", 110, "e"),
            "dn_rec": ("DN Recommandé", 110, "center"),
            "dn_ret": ("DN Retenu Projet", 110, "center"),
            "t_reel": ("Temps Réel", 90, "center"),
            "status": ("Statut Vidange", 120, "center"),
            "comment": ("Commentaire d'Exploitation", 240, "w")
        }

        for col_id, (text, width, align) in headers.items():
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, anchor=align)

        # Style Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10), background="#FFFFFF", fieldbackground="#FFFFFF")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#008080", foreground="#FFFFFF")
        style.map("Treeview", background=[('selected', '#48DBFB')], foreground=[('selected', '#1E272E')])

        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        vsb.grid(row=0, column=1, sticky="ns", pady=10)
        hsb.grid(row=1, column=0, sticky="ew", padx=10)
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

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

        for d in self.project.drains:
            tag = "compliant" if d.is_compliant else "non_compliant"
            status_text = "CONFORME (<= 2h)" if d.is_compliant else f"ALERTE ({d.t_real_str} > 2h)"

            self.tree.insert("", "end", iid=str(d.id), values=(
                d.id,
                f"{d.pm:,.2f}",
                f"{d.z_terrain:.2f}",
                f"{d.dn_conduite_m:.2f}",
                f"{d.l_total_m:,.2f}",
                f"{d.h_moy_m:.2f}",
                f"{d.volume_water_m3:,.1f}",
                f"{d.d_exact_mm:.1f}",
                f"DN {d.dn_recommended_mm}",
                f"DN {d.dn_retained_mm}",
                d.t_real_str,
                status_text,
                d.comment
            ), tags=(tag,))

    def _apply_all_recommended_dn(self):
        for d in self.project.drains:
            d.dn_retained_mm = d.dn_recommended_mm
        self.project.calculate_all()
        self.refresh()
        self.on_project_updated()
        messagebox.showinfo("DN Recommandés Appliqués", "Tous les points bas ont été dimensionnés avec le DN optimal (vidange <= 2h).")

    def _apply_uniform_400(self):
        for d in self.project.drains:
            d.dn_retained_mm = 400
        self.project.calculate_all()
        self.refresh()
        self.on_project_updated()
        messagebox.showwarning("DN 400 Uniformisé", "Le DN 400 a été appliqué partout. Notez les alertes de sous-dimensionnement sur les tronçons longs !")

    def _auto_generate_from_valves(self):
        if not self.project.air_valves:
            messagebox.showwarning("Aucune ventouse", "Le projet ne contient aucun point haut de ventouse pour déduire les vidanges.")
            return

        confirm = messagebox.askyesno(
            "Génération Automatique des Vidanges",
            "Voulez-vous générer / synchroniser automatiquement tous les points bas de vidange "
            "à partir des points amont et aval définis sur les ventouses ?\n\n"
            "Cette opération évite la double saisie et assure une parfaite cohérence géométrique."
        )
        if not confirm:
            return

        count = self.project.auto_generate_drains_from_valves()
        self.refresh()
        self.on_project_updated()
        messagebox.showinfo(
            "Vidanges Générées",
            f"✅ {count} points bas de vidange ont été déduits et dimensionnés avec succès !"
        )

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un point bas à supprimer.")
            return
        did = int(selected[0])
        self.project.drains = [d for d in self.project.drains if d.id != did]
        self.project.calculate_all()
        self.refresh()
        self.on_project_updated()

    def _open_add_dialog(self):
        self._show_drain_dialog(title="Ajouter un Point Bas (Vidange)")

    def _open_edit_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un point bas à modifier.")
            return
        did = int(selected[0])
        drain = next((d for d in self.project.drains if d.id == did), None)
        if drain:
            self._show_drain_dialog(title=f"Modifier le Point Bas PM {drain.pm}", drain=drain)

    def _show_drain_dialog(self, title: str, drain: Optional[DrainPoint] = None):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("520x600")
        dialog.grab_set()

        lbl_t = ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        lbl_t.pack(padx=20, pady=(15, 10))

        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=5)

        e_pm = self._dialog_row(content, "PM Point Bas (m) :", str(drain.pm) if drain else "50700.00")
        e_z = self._dialog_row(content, "Cote Altimétrique Point Bas (m) :", str(drain.z_terrain) if drain else "95.00")
        e_dn = self._dialog_row(content, "DN Conduite Principale (m) :", str(drain.dn_conduite_m) if drain else str(self.project.dn_main_conduite_m))

        e_pm_am = self._dialog_row(content, "PM Ventouse Amont (m) :", str(drain.pm_amont) if drain and drain.pm_amont else "")
        e_z_am = self._dialog_row(content, "Cote Ventouse Amont (m) :", str(drain.z_amont) if drain and drain.z_amont else "")

        e_pm_av = self._dialog_row(content, "PM Ventouse Aval (m) :", str(drain.pm_aval) if drain and drain.pm_aval else "")
        e_z_av = self._dialog_row(content, "Cote Ventouse Aval (m) :", str(drain.z_aval) if drain and drain.z_aval else "")

        # Sélecteur de DN retenu
        f_dn = ctk.CTkFrame(content, fg_color="transparent")
        f_dn.pack(fill="x", pady=4)
        ctk.CTkLabel(f_dn, text="DN Retenu en Projet (mm) :", width=220, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left")
        combo_dn = ctk.CTkComboBox(f_dn, values=[str(x) for x in STANDARD_DRAIN_DIAMETERS_MM], height=28)
        combo_dn.set(str(drain.dn_retained_mm) if drain else "400")
        combo_dn.pack(side="right", fill="x", expand=True)

        def save_action():
            try:
                pm = float(e_pm.get().replace(',', '.'))
                z = float(e_z.get().replace(',', '.'))
                dn = float(e_dn.get().replace(',', '.'))
                pm_am = float(e_pm_am.get().replace(',', '.')) if e_pm_am.get().strip() else None
                z_am = float(e_z_am.get().replace(',', '.')) if e_z_am.get().strip() else None
                pm_av = float(e_pm_av.get().replace(',', '.')) if e_pm_av.get().strip() else None
                z_av = float(e_z_av.get().replace(',', '.')) if e_z_av.get().strip() else None
                dn_ret = int(combo_dn.get())

                if drain:
                    drain.pm = pm
                    drain.z_terrain = z
                    drain.dn_conduite_m = dn
                    drain.pm_amont = pm_am
                    drain.z_amont = z_am
                    drain.pm_aval = pm_av
                    drain.z_aval = z_av
                    drain.dn_retained_mm = dn_ret
                else:
                    new_id = max([d.id for d in self.project.drains], default=0) + 1
                    new_d = DrainPoint(
                        id=new_id, pm=pm, z_terrain=z, dn_conduite_m=dn,
                        pm_amont=pm_am, z_amont=z_am, pm_aval=pm_av, z_aval=z_av,
                        dn_retained_mm=dn_ret
                    )
                    self.project.drains.append(new_d)

                self.project.drains.sort(key=lambda x: x.pm)
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
