"""
Vue du Catalogue des Matériels Hydrauliques (CustomTkinter).
Présente les catalogues PAM/SNH (existant) et CEAI/SNH (référence),
ainsi que les matériaux de conduite.
"""

import customtkinter as ctk
from tkinter import ttk
from core.catalog import (
    PAM_TRIPLE_FUNCTION_VALVES,
    SNH_AIR_INLET_VALVES,
    PIPE_MATERIALS,
)
from core.catalogues_ceai_snh import (
    CATALOG_CONFIG_LABELS,
    CATALOG_CEAI_SNH,
    CLAPETS_CEAI,
    PRESSION_REFERENCE,
    PURGEURS_SONIQUES_SNH,
    VENTOUSES_TRIFON_CEAI,
)
from core.catalog_mcp import (
    NOTES_MCP,
    SOURCE_XLSX,
    VENTOUSES_MCP,
    PRESSION_ADMISSION_REFERENCE,
    PRESSION_EVACUATION_REFERENCE,
)


class CatalogView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=("white", "#1E272E"), corner_radius=10)
        header.pack(fill="x", padx=15, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="📚 Catalogue des Équipements Hydrauliques Standards",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1F497D", "#70A1FF")
        )
        title.pack(anchor="w", padx=20, pady=(12, 4))

        sub = ctk.CTkLabel(
            header,
            text=(
                f"Base de référence : {CATALOG_CONFIG_LABELS[CATALOG_CEAI_SNH]} — "
                f"capacités d'admission à la dépression {PRESSION_REFERENCE}. "
                "Choix permutable avec PAM/SNH (existant) et MCP (catalogue Excel)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70"),
            wraplength=1000,
            justify="left",
        )
        sub.pack(anchor="w", padx=20, pady=(0, 12))

        # Onglets
        tabview = ctk.CTkTabview(self, corner_radius=10)
        tabview.pack(fill="both", expand=True, padx=15, pady=5)

        tab_trifon = tabview.add("🌬️ Ventouses Trifon CEAI")
        tab_mcp = tabview.add("🌬️ Ventouses MCP (Excel)")
        tab_clapet_ceai = tabview.add("🚪 Clapets CEAI")
        tab_purge_snh = tabview.add("🫧 Purgeurs soniques SNH")
        tab_pam = tabview.add("🌬️ Ventouses PAM (existant)")
        tab_snh = tabview.add("🚪 Clapets SNH (existant)")
        tab_mat = tabview.add("🔩 Matériaux & Canalisations")

        self._build_trifon_ceai_tab(tab_trifon)
        self._build_mcp_tab(tab_mcp)
        self._build_clapets_ceai_tab(tab_clapet_ceai)
        self._build_purgeurs_snh_tab(tab_purge_snh)
        self._build_pam_tab(tab_pam)
        self._build_snh_tab(tab_snh)
        self._build_mat_tab(tab_mat)

    def _build_trifon_ceai_tab(self, tab):
        box = ctk.CTkFrame(tab, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        info = ctk.CTkLabel(
            box,
            text=(
                f"Ventouses Trifon CEAI (base de calcul de référence). "
                f"Capacité d'admission unitaire à {PRESSION_REFERENCE}."
            ),
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        )
        info.pack(anchor="w", pady=(0, 10))

        cols = ("famille", "dn", "q_m3h", "q_m3s", "retenu", "origine")
        tree = ttk.Treeview(box, columns=cols, show="headings", height=10)
        headers = {
            "famille": ("Famille", 180, "w"),
            "dn": ("DN", 80, "center"),
            "q_m3h": ("Admission (m³/h)", 140, "e"),
            "q_m3s": ("Admission (m³/s)", 140, "e"),
            "retenu": ("Statut / Retenu", 120, "center"),
            "origine": ("Origine", 180, "w"),
        }
        for c, (t, w, a) in headers.items():
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor=a)

        for org in VENTOUSES_TRIFON_CEAI:
            tree.insert("", "end", values=(
                org.famille,
                org.dn,
                f"{org.capacite_m3h:,.0f}",
                f"{org.capacite_m3s:.3f}",
                org.retenu,
                org.origine,
            ))
        tree.pack(fill="both", expand=True)

    def _build_mcp_tab(self, tab):
        box = ctk.CTkFrame(tab, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        info = ctk.CTkLabel(
            box,
            text=(
                f"Ventouses automatiques doubles orifices 3 fonctions (type MCP) — source : {SOURCE_XLSX}. "
                f"Admission retenue à {PRESSION_ADMISSION_REFERENCE}, évacuation au remplissage à "
                f"{PRESSION_EVACUATION_REFERENCE} ; débits critiques à -0,5 bar / +0,9 bar donnés à titre d'information."
            ),
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            wraplength=1000,
            justify="left",
        )
        info.pack(anchor="w", pady=(0, 10))

        cols = ("dn", "serie", "dims", "poids", "adm", "adm_crit", "evac", "evac_crit", "courbe", "notes")
        tree = ttk.Treeview(box, columns=cols, show="headings", height=11)
        headers = {
            "dn": ("DN Ventouse", 120, "w"),
            "serie": ("Série DN conduite", 110, "center"),
            "dims": ("L × H × M (mm)", 140, "center"),
            "poids": ("Poids (kg)", 80, "e"),
            "adm": ("Admission 0,3 bar (m³/h)", 145, "e"),
            "adm_crit": ("Admission critique -0,5 bar (m³/h)", 160, "e"),
            "evac": ("Évacuation 0,1 bar (m³/h)", 145, "e"),
            "evac_crit": ("Évacuation critique 0,9 bar (m³/h)", 160, "e"),
            "courbe": ("Courbe", 120, "center"),
            "notes": ("Observations", 320, "w"),
        }
        for c, (t, w, a) in headers.items():
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor=a)

        for org in VENTOUSES_MCP:
            tree.insert("", "end", values=(
                org.dn_label,
                org.serie_conduite,
                org.dimensions_mm,
                f"{org.poids_kg:g}",
                f"{org.admission_opt_m3h:,.0f}",
                f"{org.admission_crit_m3h:,.0f}",
                f"{org.evacuation_1mce_m3h:,.0f}",
                f"{org.evacuation_crit_m3h:,.0f}",
                org.courbe,
                org.notes,
            ))
        tree.pack(fill="both", expand=True)

        notes_lbl = ctk.CTkLabel(
            box,
            text="Règles d'ingénierie du catalogue MCP :\n• " + "\n• ".join(NOTES_MCP),
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray70"),
            justify="left",
            wraplength=1100,
            anchor="w",
        )
        notes_lbl.pack(anchor="w", pady=(10, 0))

    def _build_clapets_ceai_tab(self, tab):
        box = ctk.CTkFrame(tab, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        info = ctk.CTkLabel(
            box,
            text=(
                f"Clapets d'admission d'air CEAI (base de calcul de référence). "
                f"Capacité d'admission unitaire à {PRESSION_REFERENCE}."
            ),
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        )
        info.pack(anchor="w", pady=(0, 10))

        cols = ("famille", "dn", "q_m3h", "q_m3s", "retenu", "origine")
        tree = ttk.Treeview(box, columns=cols, show="headings", height=10)
        headers = {
            "famille": ("Famille", 140, "w"),
            "dn": ("DN", 80, "center"),
            "q_m3h": ("Admission (m³/h)", 140, "e"),
            "q_m3s": ("Admission (m³/s)", 140, "e"),
            "retenu": ("Statut / Retenu", 120, "center"),
            "origine": ("Origine", 180, "w"),
        }
        for c, (t, w, a) in headers.items():
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor=a)

        for org in CLAPETS_CEAI:
            tree.insert("", "end", values=(
                org.famille,
                org.dn,
                f"{org.capacite_m3h:,.0f}",
                f"{org.capacite_m3s:.3f}",
                org.retenu,
                org.origine,
            ))
        tree.pack(fill="both", expand=True)

    def _build_purgeurs_snh_tab(self, tab):
        box = ctk.CTkFrame(tab, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        info = ctk.CTkLabel(
            box,
            text=(
                "Purgeurs soniques SNH (référence de purge continue / dégazage). "
                "Ne constituent pas un organe d'admission grand débit en casse franche."
            ),
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            wraplength=900,
            justify="left",
        )
        info.pack(anchor="w", pady=(0, 10))

        cols = ("famille", "dn", "q_m3h", "q_m3s", "retenu", "origine")
        tree = ttk.Treeview(box, columns=cols, show="headings", height=10)
        headers = {
            "famille": ("Famille", 180, "w"),
            "dn": ("DN", 80, "center"),
            "q_m3h": ("Capacité (m³/h)", 140, "e"),
            "q_m3s": ("Capacité (m³/s)", 140, "e"),
            "retenu": ("Statut / Retenu", 120, "center"),
            "origine": ("Origine", 180, "w"),
        }
        for c, (t, w, a) in headers.items():
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor=a)

        for org in PURGEURS_SONIQUES_SNH:
            tree.insert("", "end", values=(
                org.famille,
                org.dn,
                f"{org.capacite_m3h:,.0f}",
                f"{org.capacite_m3s:.5f}",
                org.retenu,
                org.origine,
            ))
        tree.pack(fill="both", expand=True)

    def _build_pam_tab(self, tab):
        box = ctk.CTkFrame(tab, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        info = ctk.CTkLabel(
            box,
            text="Catalogue existant PAM (configuration audit PAM/SNH) : ventouses triple fonction (dégazage, évacuation au remplissage, admission en casse franche).",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70")
        )
        info.pack(anchor="w", pady=(0, 10))

        cols = ("dn", "model", "q_in_m3s", "q_in_m3h", "q_out_m3h", "desc")
        tree = ttk.Treeview(box, columns=cols, show="headings", height=8)

        headers = {
            "dn": ("DN (mm)", 80, "center"),
            "model": ("Désignation / Modèle", 140, "w"),
            "q_in_m3s": ("Admission sous 3 mCE (m³/s)", 180, "e"),
            "q_in_m3h": ("Admission sous 3 mCE (m³/h)", 180, "e"),
            "q_out_m3h": ("Évacuation sous 1 mCE (m³/h)", 180, "e"),
            "desc": ("Observations / Utilisation", 260, "w")
        }

        for c, (t, w, a) in headers.items():
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor=a)

        for dn, spec in PAM_TRIPLE_FUNCTION_VALVES.items():
            tree.insert("", "end", values=(
                spec.dn_mm,
                spec.model,
                f"{spec.admission_flow_3m_m3s:.3f}",
                f"{spec.admission_flow_3m_m3h:,.0f}",
                f"{spec.exhaust_flow_1m_m3h:,.0f}",
                spec.description
            ))

        tree.pack(fill="both", expand=True)

    def _build_snh_tab(self, tab):
        box = ctk.CTkFrame(tab, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        info = ctk.CTkLabel(
            box,
            text="Catalogue existant : clapets d'entrée d'air grand débit (type SNH) utilisés dans la configuration PAM/SNH (audit).",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70")
        )
        info.pack(anchor="w", pady=(0, 10))

        cols = ("dn", "model", "q_in_m3s", "q_in_m3h", "desc")
        tree = ttk.Treeview(box, columns=cols, show="headings", height=8)

        headers = {
            "dn": ("DN (mm)", 80, "center"),
            "model": ("Désignation / Modèle", 160, "w"),
            "q_in_m3s": ("Admission sous 3 mCE (m³/s)", 190, "e"),
            "q_in_m3h": ("Admission sous 3 mCE (m³/h)", 190, "e"),
            "desc": ("Observations", 300, "w")
        }

        for c, (t, w, a) in headers.items():
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor=a)

        for dn, spec in SNH_AIR_INLET_VALVES.items():
            tree.insert("", "end", values=(
                spec.dn_mm,
                spec.model,
                f"{spec.admission_flow_3m_m3s:.2f}",
                f"{spec.admission_flow_3m_m3h:,.0f}",
                spec.description
            ))

        tree.pack(fill="both", expand=True)

    def _build_mat_tab(self, tab):
        box = ctk.CTkFrame(tab, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("mat", "mod_e", "ks", "roughness", "desc")
        tree = ttk.Treeview(box, columns=cols, show="headings", height=8)

        headers = {
            "mat": ("Matériau", 220, "w"),
            "mod_e": ("Module d'Young E (GPa)", 170, "e"),
            "ks": ("Coeff. Strickler Ks", 150, "center"),
            "roughness": ("Rugosité k (mm)", 140, "e"),
            "desc": ("Domaine d'emploi courant", 260, "w")
        }

        for c, (t, w, a) in headers.items():
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor=a)

        descs = {
            "PRV (Polyester Renforcé Verre)": "Grandes adductions d'eau brute / potable",
            "PVC (Polychlorure de Vinyle)": "Adductions et distribution sous pression, diamètres moyens",
            "Fonte ductile": "Réseaux sous forte pression et voirie",
            "Acier": "Très hautes pressions et traversées spéciales",
            "PEHD (Polyéthylène Haute Densité)": "Distribution et flexibilité géologique",
            "Béton armé": "Adductions gravitaires gros diamètre"
        }

        for name, vals in PIPE_MATERIALS.items():
            tree.insert("", "end", values=(
                name,
                f"{vals['E_Pa']/1e9:.1f}",
                f"{vals['Ks']:.0f}",
                f"{vals['default_roughness_m']*1000.0:.3f}",
                descs.get(name, "-")
            ))

        tree.pack(fill="both", expand=True)
