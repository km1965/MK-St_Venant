"""Vue « Données du Projet » (CustomTkinter).

Renseigne l'identité administrative du projet (MO, maîtrise d'œuvre, BET,
lieu, marché, etc.) ainsi que l'introduction et le préambule qui seront
reprises automatiquement dans les rapports Word et Excel.
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Callable

from core.project_data import HydraulicProject, ProjectIdentity


IDENTITY_FIELDS: tuple[tuple[str, str], ...] = (
    ("maitre_ouvrage", "Maître d'Ouvrage (MO) :"),
    ("maitre_oeuvre", "Maître d'Œuvre :"),
    ("bureau_etudes", "Bureau d'Études Techniques (BET) :"),
    ("lieu", "Lieu du projet :"),
    ("commune", "Commune :"),
    ("province", "Province / Région :"),
    ("pays", "Pays :"),
    ("numero_marche", "N° de marché / lot :"),
    ("annee", "Année :"),
    ("responsable_projet", "Responsable du projet :"),
    ("date_etude", "Date de l'étude :"),
    ("reference_dossier", "Référence dossier :"),
)


class ProjectInfoView(ctk.CTkFrame):
    def __init__(self, parent, project: HydraulicProject, on_project_updated: Callable):
        super().__init__(parent, fg_color="transparent")
        self.project = project
        self.on_project_updated = on_project_updated
        self.entries: dict[str, ctk.CTkEntry] = {}
        self.texts: dict[str, ctk.CTkTextbox] = {}
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="📋 Données du Projet — Identification & Préambule des Rapports",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1F497D", "#70A1FF"),
        ).pack(anchor="w", padx=20, pady=(12, 4))

        ctk.CTkLabel(
            header,
            text=(
                "Ces informations sont reprises automatiquement dans le rapport Word (.docx), "
                "le classeur Excel exporté et les livrables. Pensez à enregistrer le projet (Ctrl+S)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70"),
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=15, pady=5)
        container.grid_columnconfigure((0, 1), weight=1, uniform="info")

        left = ctk.CTkFrame(container, fg_color=("white", "#1E272E"), corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            left,
            text="🏛️ Identification du projet",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#008080", "#00D2D3"),
        ).pack(anchor="w", padx=18, pady=(14, 10))

        identity = self.project.identity
        self.entries["name"] = self._add_row(left, "Intitulé du projet :", self.project.name)
        self.entries["description"] = self._add_row(left, "Description / objet :", self.project.description)
        for key, label in IDENTITY_FIELDS:
            self.entries[key] = self._add_row(left, label, getattr(identity, key, ""))

        right = ctk.CTkFrame(container, fg_color=("white", "#1E272E"), corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            right,
            text="📝 Textes insérés dans les rapports",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#1F497D", "#70A1FF"),
        ).pack(anchor="w", padx=18, pady=(14, 10))

        ctk.CTkLabel(
            right,
            text="Préambule (contexte, commanditaire, objet du rapport) :",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=18, pady=(4, 4))
        self.texts["preamble"] = ctk.CTkTextbox(right, height=170, font=ctk.CTkFont(size=12))
        self.texts["preamble"].insert("1.0", identity.preamble)
        self.texts["preamble"].pack(fill="both", expand=True, padx=18, pady=(0, 12))

        ctk.CTkLabel(
            right,
            text="Introduction (hypothèses et présentation de l'étude) :",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=18, pady=(4, 4))
        self.texts["introduction"] = ctk.CTkTextbox(right, height=170, font=ctk.CTkFont(size=12))
        self.texts["introduction"].insert("1.0", identity.introduction)
        self.texts["introduction"].pack(fill="both", expand=True, padx=18, pady=(0, 12))

        ctk.CTkLabel(
            right,
            text=(
                "Si ces champs sont laissés vides, un texte standard est généré "
                "à partir de l'intitulé et de l'identité du projet."
            ),
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray70"),
            wraplength=500,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 10))

        btn_apply = ctk.CTkButton(
            self,
            text="💾 Appliquer les données du projet",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#00A8FF",
            hover_color="#0097E6",
            height=38,
            command=self._apply,
        )
        btn_apply.pack(fill="x", padx=15, pady=(10, 15))

    @staticmethod
    def _add_row(parent, label: str, value: str) -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=3)
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), width=255, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, height=28, font=ctk.CTkFont(size=12))
        entry.insert(0, str(value or ""))
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def _apply(self):
        try:
            self.project.name = self.entries["name"].get().strip() or self.project.name
            self.project.description = self.entries["description"].get().strip()
            identity: ProjectIdentity = self.project.identity
            for key, _label in IDENTITY_FIELDS:
                setattr(identity, key, self.entries[key].get().strip())
            identity.preamble = self.texts["preamble"].get("1.0", "end").strip()
            identity.introduction = self.texts["introduction"].get("1.0", "end").strip()
            self.project.calculate_all()
            self.on_project_updated()
            messagebox.showinfo("Données du projet", "Les informations du projet ont été mises à jour.")
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible d'appliquer les données du projet :\n{exc}")

    def refresh(self):
        identity = getattr(self.project, "identity", None)
        if identity is None:
            return

        def set_entry(key: str, value: str):
            entry = self.entries.get(key)
            if entry is not None:
                entry.delete(0, "end")
                entry.insert(0, str(value or ""))

        set_entry("name", self.project.name)
        set_entry("description", self.project.description)
        for key, _label in IDENTITY_FIELDS:
            set_entry(key, getattr(identity, key, ""))
        for key, widget in self.texts.items():
            widget.delete("1.0", "end")
            widget.insert("1.0", getattr(identity, key, "") or "")
