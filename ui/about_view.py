"""
Vue "À propos & Aide utilisateur" (CustomTkinter).
Fournit le guide d'utilisation, les bonnes pratiques de sauvegarde et les informations sur l'application.
"""

import customtkinter as ctk

from core.project_data import HydraulicProject
from core.catalogues_ceai_snh import CATALOG_CONFIG_LABELS, DEFAULT_AIR_CATALOG_CONFIG


APP_VERSION = "1.1"
APP_NAME = "MK-St_Venant"


class AboutView(ctk.CTkFrame):
    def __init__(self, parent, project: HydraulicProject):
        super().__init__(parent, fg_color="transparent")
        self.project = project
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # En-tête
        header = ctk.CTkFrame(container, fg_color=("white", "#1E272E"), corner_radius=10)
        header.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            header,
            text=f"ℹ️ {APP_NAME} — À propos & Aide utilisateur",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1F497D", "#70A1FF"),
        ).pack(anchor="w", padx=20, pady=(15, 4))

        ctk.CTkLabel(
            header,
            text=(
                "Outil d'ingénierie hydraulique pour le dimensionnement et la vérification des "
                "organes de sécurité (ventouses/points hauts et vidanges/points bas)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray70"),
            justify="left",
            wraplength=900,
        ).pack(anchor="w", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            header,
            text=f"Version : {APP_VERSION}    •    Formats projet : .mkst.json / .json",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray65"),
        ).pack(anchor="w", padx=20, pady=(0, 15))

        self._section(
            container,
            "1) Ne pas perdre les calculs (important)",
            (
                "• Les imports Excel et les modifications vivent en mémoire tant que le projet n'est pas enregistré.\n"
                "• Utilisez Fichier > Enregistrer / Enregistrer sous pour sauvegarder un fichier projet (.mkst.json).\n"
                "  Ce fichier conserve : paramètres généraux, base catalogue air, points hauts/bas, DN retenus, "
                "équipements retenus et les données importées.\n"
                "• À l'ouverture d'un projet, l'application recharge les données et recalcule automatiquement les résultats.\n"
                "• Un astérisque (*) dans le titre de la fenêtre indique des modifications non enregistrées.\n"
                "• Avant de créer/ouvrir un projet, de recharger le cas de référence ou de quitter, "
                "l'application propose d'enregistrer si nécessaire."
            ),
        )

        self._section(
            container,
            "2) Workflow recommandé",
            (
                "1. Nouveau projet ou Ouvrir un projet existant (.mkst.json).\n"
                "2. Renseigner les paramètres généraux (DN, matériau, épaisseur, Ks, vitesses, ΔP, temps de vidange, base catalogue).\n"
                "3. Importer les points depuis Excel (Imports/Exports) ou les saisir dans les vues Points Hauts / Points Bas.\n"
                "4. Vérifier les calculs, ajuster les DN/équipements retenus, appliquer les recommandations si besoin.\n"
                "5. Enregistrer le projet (Fichier > Enregistrer).\n"
                "6. Exporter les livrables : rapport Word, classeur Excel de calculs, graphiques HD."
            ),
        )

        self._section(
            container,
            "3) Bases catalogue et calculs",
            (
                "• Base catalogue organes d'air sélectionnable : CEAI/SNH (référence) et PAM/SNH (existant), "
                "configurable dans le Tableau de bord.\n"
                "• Les recommandations d'équipements et les contrôles associés dépendent de la base choisie ; "
                "le rapport et les exports indiquent la base utilisée.\n"
                "• Vidanges : dimensionnement selon la hauteur moyenne pondérée des branches, le temps objectif "
                "et le DN retenu (temps réel recalculé).\n"
                "• Ventouses/points hauts : évaluation des débits d'air requis (casse franche, remplissage, dégazage) "
                "et de la couverture des équipements retenus/recommandés.\n"
                "• Vérifiez toujours les hypothèses (cotes, PM, longueurs, topologie amont/aval, matériau, coefficients) "
                "avant exploitation des résultats."
            ),
        )

        self._section(
            container,
            "4) Raccourcis clavier (menu Fichier)",
            (
                "• Ctrl+N : Nouveau projet\n"
                "• Ctrl+O : Ouvrir un projet\n"
                "• Ctrl+S : Enregistrer\n"
                "• Ctrl+Shift+S : Enregistrer sous\n"
                "• Ctrl+I : Importer un fichier Excel\n"
                "• Ctrl+Q : Quitter"
            ),
        )

        self._section(
            container,
            "5) Dépannage",
            (
                "• Si un import ne donne pas le résultat attendu : vérifier les en-têtes/colonnes du fichier Excel "
                "et utiliser le gabarit vierge fourni dans la vue Imports/Exports.\n"
                "• Si des valeurs paraissent incohérentes : contrôler la topologie (PM/cotes amont-aval), les unités "
                "et les paramètres généraux, puis relancer le calcul (appliquer les paramètres).\n"
                "• Pensez à sauvegarder régulièrement le fichier .mkst.json, surtout après un import ou des ajustements manuels."
            ),
        )

        footer = ctk.CTkFrame(container, fg_color=("white", "#1E272E"), corner_radius=10)
        footer.pack(fill="x", pady=(4, 10))
        ctk.CTkLabel(
            footer,
            text=(
                "MK-St_Venant — Application d'aide au calcul hydraulique. "
                "Les résultats doivent être validés par un ingénieur qualifié selon le contexte du projet."
            ),
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray65"),
            justify="left",
            wraplength=900,
        ).pack(anchor="w", padx=20, pady=12)

    def _section(self, parent, title: str, body: str):
        box = ctk.CTkFrame(parent, fg_color=("white", "#1E272E"), corner_radius=10)
        box.pack(fill="x", pady=6)
        ctk.CTkLabel(
            box,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#008080", "#00D2D3"),
        ).pack(anchor="w", padx=20, pady=(12, 6))
        ctk.CTkLabel(
            box,
            text=body,
            font=ctk.CTkFont(size=12),
            justify="left",
            wraplength=900,
            text_color=("gray15", "gray85"),
        ).pack(anchor="w", padx=20, pady=(0, 14))

    def refresh(self):
        # Vue statique (aucune donnée dépendante à rafraîchir pour l'instant)
        pass
